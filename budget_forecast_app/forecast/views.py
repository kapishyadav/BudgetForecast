# Create your views here.
from .dto import ForecastTriggerDTO, CustomScenarioDTO
from .services.services import ForecastOrchestrationService
from .dto import DatasetUploadDTO
from .services.ingestion_service import DataIngestionService
from .serializers import ForecastTriggerSerializer, CustomScenarioSerializer, CloudIntegrationSerializer
from .utils.responses import api_response

from django.shortcuts import render
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .models import ForecastRun, HistoricalSpend, CloudIntegration
from .ml.main import run_forecast
from .ml.utils.setup_logging import setup_logging

from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from .tasks import sync_integration_data
from celery.result import AsyncResult

import json
import os
import pandas as pd

logger = setup_logging()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    # AllowAny means anyone can access this URL (necessary for signing up!)
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

def hello_vite(request):
    return render(request, "hello_vite.html")


@csrf_exempt
def upload_file(request):
    """View for handling file uploads."""
    if request.method == "POST" and request.FILES.get("dataset"):
        file = request.FILES["dataset"]
        dataset_name = file.name.split('.')[0]

        try:
            # Map to DRO
            dto = DatasetUploadDTO(file = file, dataset_name= dataset_name)

            # Delegate to Service
            service = DataIngestionService()
            dataset_id = service.process_csv_upload(dto)

            # Update session state
            request.session['current_dataset_id'] = dataset_id
            request.session.modified = True

            return JsonResponse({
                "status": "success",
                "dataset_id": dataset_id,
                "message": "Upload successful, processing started."
            })

        except ValueError as e:
            # Catch bad CSV formats or empty files cleanly
            logger.warning(f"Upload validation failed: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

        except Exception as e:
            logger.error(f"Critical Upload failure: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request or missing file"}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_forecast(request):
    """Standard forecast trigger - strictly HTTP boundary."""
    serializer = ForecastTriggerSerializer(data=request.data)

    # raise_exception=True instantly hands control to our custom_exception_handler if invalid!
    serializer.is_valid(raise_exception=True)

    dto = ForecastTriggerDTO(**serializer.validated_data)
    service = ForecastOrchestrationService()
    result = service.trigger_standard_forecast(dto)

    return api_response(data=result, message="Processing started.", status_code=202)


@api_view(['POST'])
@permission_classes([AllowAny])
def run_custom_scenario(request):
    """Custom scenario trigger - strictly HTTP boundary."""

    serializer = CustomScenarioSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    dto = CustomScenarioDTO(**serializer.validated_data)
    service = ForecastOrchestrationService()
    result = service.trigger_custom_scenario(dto)

    return api_response(data=result, message="Scenario triggered successfully.", status_code=202)

def get_suggestions(request):
    """
    Fetches unique suggestions directly from PostgreSQL.
    No more slow CSV reading!
    Now supports Cascading Filters!
    """
    dataset_id = request.GET.get("dataset_id", "").strip()
    # Fallback to latest dataset if none provided
    if not dataset_id:
        latest_spend = HistoricalSpend.objects.order_by('-id').first()
        if latest_spend:
            dataset_id = latest_spend.dataset_id
        else:
            return JsonResponse({"suggestions": []})

    field = request.GET.get("field")
    query = request.GET.get("q", "").strip().lower()

    # Map the frontend field name to our PostgreSQL model field name
    field_map = {
        "account": "account_name",
        "service": "service_name",
        "bu_code": "bu_code",
        "segment": "segment"
    }

    model_field = field_map.get(field)
    if not model_field:
        return JsonResponse({"error": "Invalid field"}, status=400)

    # Gather active UI filters
    active_filters = {
        "account_name": request.GET.get("account_name"),
        "service_name": request.GET.get("service_name"),
        "bu_code": request.GET.get("bu_code"),
        "segment": request.GET.get("segment_name")
    }

    try:
        # DELEGATE TO DATA ACCESS LAYER
        suggestions = HistoricalSpend.objects.get_cascading_suggestions(
            dataset_id=dataset_id,
            model_field=model_field,
            query=query,
            active_filters=active_filters
        )
        return JsonResponse({"suggestions": suggestions})

    except Exception as e:
        logger.error(f"ERROR in get_suggestions: {e}")
        return JsonResponse({"suggestions": []})


def download_forecast_csv(request):
    """Return the forecast CSV stored in session as a downloadable file."""
    logger.info("DEBUG Downloading forecast csv!")

    csv_data = request.session.get("forecast_csv_json")

    # 1. ALWAYS check if data exists before trying to parse it
    if not csv_data:
        return HttpResponse("No forecast data available. Please generate a forecast first.", status=404)

    # 2. Parse the JSON and build the DataFrame
    parsed_data = json.loads(csv_data)
    forecast_df = pd.DataFrame(parsed_data)

    # 3. Convert DataFrame directly to a CSV string (in memory)
    csv_string = forecast_df.to_csv(index=False)

    # 4. Handle Filename Generation
    base_filename = request.session.get("csv_base_filename", "forecast")
    account_name = request.session.get("account_name", "")
    service_name = request.session.get("service_name", "")
    forecast_type = request.session.get("forecast_type", "monthly")

    base_filename = os.path.splitext(base_filename)[0]
    logger.info(f"DEBUG Base_Filename is : {base_filename}")

    def clean(name):
        return name.strip().replace(" ", "_").lower() if name else ""

    account_name = clean(account_name)
    service_name = clean(service_name)

    if account_name and service_name:
        filename = f"{base_filename}-forecasts-{account_name}-{service_name}.csv"
    elif account_name:
        filename = f"{base_filename}-forecasts-{account_name}.csv"
    else:
        filename = f"{base_filename}-forecasts-{forecast_type}-aggregate.csv"

    # 5. Return the file as a downloadable response
    response = HttpResponse(csv_string, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


def dashboard_view(request):
    # Suppose this is your forecasts-misc DataFrame
    forecasts_formatted = request['forecast']
    metrics = request['metrics']

    # Convert to JSON
    chart_data = forecasts_formatted.to_dict(orient='records')
    chart_json = json.dumps(chart_data, default=str)

    return render(request, "dashboard.html", {
        "chart_json": chart_json,
        "metrics": metrics,
    })


@csrf_exempt
def forecast_api(request):
    """
    API endpoint for programmatic access.
    POST a CSV file → returns JSON with forecast + metrics + figure JSON.
    """
    if request.method == "POST" and request.FILES.get("dataset"):
        file = request.FILES["dataset"]
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)
        forecast_type = request.POST.get("forecast_type", "monthly")  # default to monthly

        try:
            result = run_forecast(file_path, forecast_type)
            return JsonResponse({
                "status": "success",
                "metrics": result["metrics"],
                "figure_json": result["figure_json"],
                "forecast": result["forecast"],
            })
        except Exception as e:
            logger.error(f"Forecasting failed in API: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "No dataset uploaded"}, status=400)


def check_task_status(request, task_id):
    """JSON endpoint for React to poll Celery task status."""
    task = AsyncResult(task_id)

    if task.state == 'PENDING' or task.state == 'STARTED':
        # Still working! Return the loading spinner snippet again.
        return JsonResponse({"status": "PENDING", "message": "Forecasting in progress..."})

    elif task.state == 'SUCCESS':
        # Task is done! Grab the dictionary returned by tasks.py
        result = task.result

        # Check if our task caught an error gracefully
        if result.get("status") == "error":
            return JsonResponse({"status": "FAILURE", "message": result.get("message")})

        # Success! Save the big JSON strings in the session for the dashboard to use later
        request.session['forecast_csv_json'] = result["forecast_json"]
        request.session['historical_csv_json'] = result.get("historical_json", "[]")  # Save historical too
        request.session.modified = True

        logger.info(f"DEBUG: Task {task_id} SUCCESS. Returning JSON to React.")

        # Return a pure JSON success message so React knows to redirect
        return JsonResponse({
            "status": "SUCCESS",
            "message": "Forecast complete!"
        })

    elif task.state == 'FAILURE':
        # Something crashed hard inside the Celery worker
        return JsonResponse({
            "status": "FAILURE",
            "message": str(task.info)  # This passes the actual Python error back to React
        })


def get_dashboard_data(request):
    """Retrieves forecast JSON directly from Celery and filters it via Pandas."""
    task_id = request.GET.get('task_id')

    if not task_id:
        return JsonResponse({"error": "No task ID provided in URL."}, status=400)

    task = AsyncResult(task_id)

    if task.state != 'SUCCESS':
        return JsonResponse({"error": "Forecast not ready or invalid task ID."}, status=400)

    result = task.result
    raw_forecast = json.loads(result.get("forecast_json", "[]"))
    raw_historical = json.loads(result.get("historical_json", "[]"))
    metrics = result.get("metrics", {})

    # --- THE FIX: Robust Dataset ID Retrieval ---
    # First, try to get it from the Celery result dictionary
    dataset_id = result.get("dataset_id")

    # If the Celery task didn't return it, look it up in the PostgreSQL database!
    if not dataset_id:
        try:
            # Look up the run record using the task_id
            run_record = ForecastRun.objects.filter(task_id=task_id).first()
            if run_record:
                dataset_id = str(run_record.dataset.id)
                print(f"DEBUG: Found dataset_id {dataset_id} via database fallback.")
            else:
                print(f"DEBUG: No ForecastRun found for task_id {task_id}")
        except Exception as e:
            print(f"DEBUG: Database lookup failed for dataset_id: {e}")

    # 2. Extract valid filters from the incoming request
    allowed_filters = ['account_name', 'service_name', 'segment_name', 'bu_code']
    active_filters = {
        key: request.GET.get(key)
        for key in allowed_filters
        if request.GET.get(key)
    }

    # 3. If no filters are applied, return the global view
    if not active_filters:
        return JsonResponse({
            "forecast": raw_forecast,
            "historical": raw_historical,
            "metrics": metrics,
            "dataset_id": dataset_id  # This will now successfully pass to React!
        })

    # 4. Filter logic
    def filter_data(data_list, filters):
        if not data_list:
            return []
        df = pd.DataFrame(data_list)
        for column, value in filters.items():
            if column in df.columns:
                df = df[df[column] == value]
        if df.empty:
            return []
        df = df.replace({np.nan: None})
        return df.to_dict(orient='records')

    filtered_forecast = filter_data(raw_forecast, active_filters)
    filtered_historical = filter_data(raw_historical, active_filters)

    return JsonResponse({
        "forecast": filtered_forecast,
        "historical": filtered_historical,
        "metrics": metrics,
        "dataset_id": dataset_id
    })


# --- NEW CLOUD INTEGRATION VIEWSET ---

class CloudIntegrationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Cloud Integrations to be viewed, created, or edited.
    """
    queryset = CloudIntegration.objects.all().order_by('-id')
    serializer_class = CloudIntegrationSerializer

    def get_queryset(self):
        """
        Optional: If you want to filter integrations by a specific dataset
        passed in the URL query params (e.g., ?dataset_id=123)
        """
        queryset = super().get_queryset()
        dataset_id = self.request.query_params.get('dataset_id')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)

        provider = self.request.query_params.get('provider')
        if provider:
            # .upper() ensures 'aws' or 'AWS' both match your database choices
            queryset = queryset.filter(provider=provider.upper())

        return queryset

    @action(detail=True, methods=['post'], url_path='sync-now')
    def sync_now(self, request, pk=None):
        """
        Custom endpoint to manually trigger the Celery ingestion task.
        Accessed via: POST /api/cloud-integrations/{id}/sync-now/
        """
        integration = self.get_object()

        if not integration.is_active:
            return Response(
                {"error": "Cannot sync an inactive integration."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Dispatch the Celery task in the background
        task = sync_integration_data.delay(integration.id)

        logger.info(f"Manual sync triggered for integration {integration.id}. Task ID: {task.id}")

        return Response(
            {
                "message": f"Sync queued successfully for {integration.provider}.",
                "task_id": task.id
            },
            status=status.HTTP_202_ACCEPTED
        )