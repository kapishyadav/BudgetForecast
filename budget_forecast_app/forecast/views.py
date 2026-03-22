# Create your views here.
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .ml.main import run_forecast
from .ml.utils.setup_logging import setup_logging
from .ml.enums import ForecastType, Granularity
from .ml.prophet_model import get_mapped_columns

from .tasks import generate_forecast_task
from celery.result import AsyncResult

import plotly.io as pio
import json
import os
import io
import uuid
import pandas as pd
import traceback
from pathlib import Path

logger = setup_logging()

def hello_vite(request):
    return render(request, "hello_vite.html")

@csrf_exempt
def upload_file(request):
    """Renders the upload form and delegates forecasting to Celery."""
    if request.method == "POST" and request.FILES.get("dataset"):

        # Clear any old session data to avoid stale suggestions
        for key in ["csv_base_filename", "uploaded_file_path", "forecast_csv_json"]:
            if key in request.session:
                del request.session[key]

        file = request.FILES["dataset"]
        extension = os.path.splitext(file.name)[1]

        # Create a short, unique name
        short_filename = f"Forecasts-{uuid.uuid4().hex[:12]}{extension}"
        fs = FileSystemStorage()
        filename = fs.save(short_filename, file)
        file_path = fs.path(filename)

        logger.info(f"DEBUG select filename from POST: {filename}")
        logger.info(f"DEBUG select filename from POST: {file_path}")

        # --- CLEANUP FUNCTION ---
        delete_old_files(max_files=5)

        # Safely convert to enum strings for Celery (Celery can't handle complex objects)
        selected_type = request.POST.get("forecast_type", "overall_aggregate")
        granularity = request.POST.get("granularity", "monthly")

        try:
            forecast_type = ForecastType(selected_type)
            granularity_val = Granularity(granularity).value if hasattr(Granularity(granularity), "value") else str(
                Granularity(granularity))
        except ValueError:
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity_val = Granularity.MONTHLY.value

        forecast_type_str = forecast_type.value if hasattr(forecast_type, "value") else str(forecast_type)

        # Optional inputs
        account_name = request.POST.get("account_name", "").strip()
        service_name = request.POST.get("service_name", "").strip()
        bu_code_raw = request.POST.get("bu_code", "").strip()
        bu_code = int(bu_code_raw) if bu_code_raw != "" else None
        segment_name = request.POST.get("segment_name", "").strip()

        # Build kwargs for the task
        kwargs = {}
        if forecast_type == ForecastType.ACCOUNT and account_name:
            kwargs["account_name"] = account_name
        if forecast_type == ForecastType.SERVICE:
            if service_name: kwargs["service_name"] = service_name
            if account_name: kwargs["account_name"] = account_name
        if forecast_type == ForecastType.BUCODE and bu_code is not None:
            kwargs["bu_code"] = bu_code
        if forecast_type == ForecastType.SEGMENT:
            if segment_name: kwargs["segment_name"] = segment_name
            if service_name: kwargs["service_name"] = service_name
            if account_name: kwargs["account_name"] = account_name

        try:
            logger.info("Sending ML pipeline to Celery worker...")

            # Send the job to the background worker using .delay()
            task = generate_forecast_task.delay(
                file_path=file_path,
                forecast_type_str=forecast_type_str,
                granularity_str=granularity_val,
                **kwargs
            )

            # Store session data NOW so it is ready for the download step later
            # request.session['csv_base_filename'] = filename
            # request.session['uploaded_file_path'] = file_path
            # request.session['forecast_type'] = forecast_type_str
            # request.session['account_name'] = account_name
            # request.session['service_name'] = service_name
            # request.session['bu_code'] = bu_code
            # request.session['segment_name'] = segment_name
            # request.session.modified = True

            # ==========================================
            # 2. CRITICAL: SET THE SESSION VARIABLES
            # ==========================================
            request.session['csv_base_filename'] = filename
            request.session['uploaded_file_path'] = file_path

            # Force Django to save the session to the database/cache immediately
            request.session.modified = True

            logger.info(f"✅ Session successfully set! csv_base_filename: {request.session['csv_base_filename']}")

            # 3. Return JSON for React
            return JsonResponse({
                "status": "success",
                "task_id": task.id,
                "message": "Upload successful, processing started."
            })

            # Return the loading template, passing the task_id to HTMX
            # return render(request, "forecast/partials/loading.html", {"task_id": task.id})

        except Exception as e:
            logger.error(f"Forecasting failed to start: {e}")
            #return render(request, "forecast/upload.html", {"error": str(e)})
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    #return render(request, "forecast/upload.html")
    return JsonResponse({"status": "error", "message": "Invalid request or missing file"}, status=400)

def get_suggestions(request):
    logger.info(f"DEBUG in get_suggestions views")
    logger.info(f"DEBUG request in get_suggestions views- {request}")
    logger.info(f"DEBUG REQUEST SESSION in get_suggestions views- {request.session}")
    query = request.GET.get("q", "").strip().lower()
    field = request.GET.get("field")  # 'account', 'service', 'bucode'or 'segment'

    filename = request.session.get("csv_base_filename")
    logger.info(f"DEBUG Request Session csv_base_filename : {filename}")
    if not filename:
        print("❌ No file found in session — likely no upload in this session.")
        # Try to get the most recently uploaded file (as fallback)
        fs = FileSystemStorage()
        files = sorted(fs.listdir(fs.location)[1], key=lambda f: os.path.getctime(os.path.join(fs.location, f)),
                       reverse=True)
        if files:
            filename = files[0]
            filename = filename[:10]
            print(f"⚠️ Using fallback file: {filename}")
            request.session["csv_base_filename"] = filename
        else:
            return JsonResponse({"suggestions": []})

    fs = FileSystemStorage()
    file_path = fs.path(filename)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return JsonResponse({"suggestions": []})

    try:
        df = pd.read_csv(file_path)
        print(f"✅ Loaded file with columns: {list(df.columns)}")
        logger.info(f"Dataset loaded successfully for get_suggestions. Shape: {df.shape}")
        COLUMN_MAPPINGS = {
            "accountName": ["accountName", "vendor_name", "vendor_account_name"],
            "spend": ["spend", "cost", "public_on_demand", "public_on_demand_cost", "total_amortized_cost"],
            "serviceName": ["serviceName", "enhanced_service_name"],
            "month": ["month", "date", "year_month"],
            "date": ["Date"]
        }

        mapped_columns = get_mapped_columns(df.columns.tolist(), COLUMN_MAPPINGS)
        logger.info(f"DEBUG for get_suggestions mapped columns after get_mapped_columns method in prophet_model.py - {mapped_columns}")
        rename_dict = {actual_col: canonical_col for canonical_col, actual_col in mapped_columns.items()}
        logger.info(f"DEBUG for get_suggestions Renamed Dict Column Names: {rename_dict}")
        # Apply the mapping to the DataFrame
        df = df.rename(columns=rename_dict)
        logger.info(f"DEBUG for get_suggestions DF Column Names after renaming post remap: {df.columns}")

        if field == "account":
            col_name = "accountName"
        elif field == "service":
            col_name = "serviceName"
        elif field == "bu_code":
            col_name = "buCode"
        elif field == "segment":
            col_name = "segment"
        else:
            return JsonResponse({"error": "Invalid field"}, status=400)

        if col_name not in df.columns:
            print(f"❌ Column {col_name} not found in CSV.")
            return JsonResponse({"suggestions": []})

        unique_vals = df[col_name].dropna().unique().tolist()
        matches = [v for v in unique_vals if query in str(v).lower()]
        print(f"🔍 Query='{query}' found {len(matches)} matches: {matches[:5]}")
        print(f"🧪 First 5 accountName values: {df['accountName'].dropna().unique()[:5]}")

        return JsonResponse({"suggestions": matches[:10]})

    except Exception as e:
        print(f"ERROR in get_suggestions: {e}")
        return JsonResponse({"error": str(e)}, status=500)


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
    """Retrieves forecast JSON directly from Celery via task_id."""
    task_id = request.GET.get('task_id')

    if not task_id:
        return JsonResponse({"error": "No task ID provided in URL."}, status=400)

    task = AsyncResult(task_id)

    if task.state != 'SUCCESS':
        return JsonResponse({"error": "Forecast not ready or invalid task ID."}, status=400)

    # Grab the result dictionary directly from Redis/Celery
    result = task.result

    return JsonResponse({
        # We parse the stringified JSON from Celery back into Python lists
        "forecast": json.loads(result.get("forecast_json", "[]")),
        "historical": json.loads(result.get("historical_json", "[]")),
        "metrics": result.get("metrics", {})
    })

