# Create your views here.
from typing import Dict

from django.views.decorators.http import require_POST
from .dto import ForecastTriggerDTO, CustomScenarioDTO
from .services.services import ForecastOrchestrationService
from .config import DEFAULT_FORECAST_TYPE, DEFAULT_GRANULARITY

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .models import ForecastDataset, ForecastRun, HistoricalSpend
from .ml.main import run_forecast
from .ml.utils.setup_logging import setup_logging
from .ml.enums import ForecastType, Granularity

from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import RegisterSerializer

from .tasks import generate_forecast_task
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

COLUMN_MAPPINGS = {
    "accountName": ["accountName", "vendor_name", "vendor_account_name", "account"],
    "spend": ["spend", "cost", "public_on_demand", "public_on_demand_cost", "total_amortized_cost"],
    "serviceName": ["serviceName", "enhanced_service_name", "service"],
    "date": ["date", "month", "year_month", "Date", "Month"], # Consolidated date mappings
    "buCode": ["buCode", "business_unit", "bu_code"],
    "segment": ["segment", "segment_name"]
}

def hello_vite(request):
    return render(request, "hello_vite.html")


@csrf_exempt
def upload_file(request):
    """Parses CSV, dynamically maps columns, and saves to PostgreSQL."""
    if request.method == "POST" and request.FILES.get("dataset"):

        file = request.FILES["dataset"]
        dataset_name = file.name.split('.')[0]

        try:
            # 1. Read CSV directly into memory
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()  # Clean column headers

            # ==========================================
            # APPLY DYNAMIC COLUMN MAPPING
            # ==========================================
            available_cols = df.columns.tolist()
            mapped_columns = get_mapped_columns(available_cols, COLUMN_MAPPINGS)

            logger.info(f"Available columns: {available_cols}")
            logger.info(f"Mapped columns: {mapped_columns}")

            # Create the rename dictionary: {actual_csv_col: canonical_model_col}
            # Note: We reverse dict comprehension so df.rename works correctly
            rename_dict = {actual_col: canonical_col for canonical_col, actual_col in mapped_columns.items()}

            # Rename the dataframe columns
            df = df.rename(columns=rename_dict)
            logger.info(f"DF Column Names post-mapping: {df.columns.tolist()}")

            # ==========================================
            # VERIFY CRITICAL COLUMNS
            # ==========================================
            # After mapping, we absolutely must have 'date' and 'spend'
            if 'date' not in df.columns:
                return JsonResponse({"error": "CSV must contain a recognized date column (e.g., date, month, Date)."},
                                    status=400)
            if 'spend' not in df.columns:
                return JsonResponse({"error": "CSV must contain a recognized spend/cost column."}, status=400)

            # ==========================================
            # DATABASE INSERTION
            # ==========================================
            dataset = ForecastDataset.objects.create(name=dataset_name)
            # Save to session so the get_suggestions view can use it immediately
            request.session['current_dataset_id'] = str(dataset.id)
            request.session.modified = True

            spend_records = []

            # Check for optional columns (using the canonical names now!)
            has_account = 'accountName' in df.columns
            has_service = 'serviceName' in df.columns
            has_bucode = 'buCode' in df.columns
            has_segment = 'segment' in df.columns

            for index, row in df.iterrows():
                record = HistoricalSpend(
                    dataset=dataset,
                    # We can safely assume 'date' and 'spend' exist now
                    date=pd.to_datetime(row['date']).date(),
                    spend=row['spend'],

                    # Safely handle optional columns
                    account_name=row['accountName'] if has_account and pd.notna(row['accountName']) else None,
                    service_name=row['serviceName'] if has_service and pd.notna(row['serviceName']) else None,
                    bu_code=int(row['buCode']) if has_bucode and pd.notna(row['buCode']) else None,
                    segment=row['segment'] if has_segment and pd.notna(row['segment']) else None,
                )
                spend_records.append(record)

            with transaction.atomic():
                HistoricalSpend.objects.bulk_create(spend_records, batch_size=5000)

            logger.info(f"Successfully saved {len(spend_records)} rows to Postgres.")

            return JsonResponse({
                "status": "success",
                # "task_id": task.id,
                "dataset_id": str(dataset.id),
                "message": "Upload successful, processing started."
            })

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request or missing file"}, status=400)

@csrf_exempt
@require_POST
def trigger_forecast(request):
    """Standard forecast trigger - strictly HTTP boundary."""
    try:
        # 1. Map HTTP Request directly to Domain DTO
        # The __post_init__ in the DTO will throw a ValueError if data is bad
        dto = ForecastTriggerDTO(
            dataset_id=request.POST.get("dataset_id"),
            forecast_type=request.POST.get("forecast_type", "overall_aggregate"),
            granularity=request.POST.get("granularity", "monthly"),
            account_name=request.POST.get("account_name") or None,
            service_name=request.POST.get("service_name") or None,
            bu_code=request.POST.get("bu_code") or None,
            segment_name=request.POST.get("segment_name") or None
        )

        # 2. Delegate to Business Logic
        service = ForecastOrchestrationService()
        result = service.trigger_standard_forecast(dto)

        # 3. Return Standardized HTTP Response
        return JsonResponse(result, status=202)

    except ValueError as e:
        logger.warning(f"Validation error in trigger_forecast: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in trigger_forecast: {e}")
        return JsonResponse({"status": "error", "message": "Internal Server Error"}, status=500)


@csrf_exempt
@require_POST
def run_custom_scenario(request):
    """Custom scenario trigger - strictly HTTP boundary."""
    try:
        body = json.loads(request.body)

        # 1. Map to DTO (Fail-fast validation and type-casting happens here)
        dto = CustomScenarioDTO(
            dataset_id=body.get("dataset_id"),
            changepoint_prior_scale=float(body.get("changepoint_prior_scale", 0.05)),
            seasonality_mode=str(body.get("seasonality_mode", "additive")),
            include_holidays=bool(body.get("include_holidays", False))
        )

        # 2. Delegate to Service
        service = ForecastOrchestrationService()
        result = service.trigger_custom_scenario(dto)

        return JsonResponse(result, status=202)

    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return JsonResponse({"status": "error", "message": f"Invalid input: {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Error in custom scenario: {e}")
        return JsonResponse({"status": "error", "message": "Internal Server Error"}, status=500)


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
    # Suppose this is your forecasts DataFrame
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


def delete_old_files(max_files=5):
    folder = settings.MEDIA_ROOT

    # Ensure the directory exists to avoid errors
    if not os.path.exists(folder):
        return

    # Get ONLY files (ignore directories) with their full paths
    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    ]

    # Sort files by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)

    # Delete files older than the limit
    if len(files) > max_files:
        for file_path in files[max_files:]:
            try:
                os.remove(file_path)
                logger.info(f"Deleted old file to maintain limit: {file_path}")
            except OSError as e:
                logger.error(f"Error deleting file {file_path}: {e}")


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

def get_mapped_columns(available_columns: list, mappings: Dict[str, list]) -> Dict[str, str]:
    """Maps available column names to standardized canonical names."""
    columns_dict = {}
    for canonical_name, possible_names in mappings.items():
        # Case-insensitive match is usually safer, but keeping your original logic here
        match = next((name for name in possible_names if name in available_columns), None)
        if match:
            columns_dict[canonical_name] = match
    return columns_dict

