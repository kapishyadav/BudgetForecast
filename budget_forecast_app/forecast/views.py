# Create your views here.
from datetime import datetime
from typing import Dict

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

            # --- PREPARE CELERY KWARGS ---
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

            account_name = request.POST.get("account_name", "").strip()
            service_name = request.POST.get("service_name", "").strip()
            bu_code_raw = request.POST.get("bu_code", "").strip()
            bu_code = int(bu_code_raw) if bu_code_raw != "" else None
            segment_name = request.POST.get("segment_name", "").strip()

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

            # Trigger Celery Task
            logger.info("Sending ML pipeline to Celery worker...")
            task = generate_forecast_task.delay(
                dataset_id=str(dataset.id),
                forecast_type_str=forecast_type_str,
                granularity_str=granularity_val,
                **kwargs
            )

            ForecastRun.objects.create(dataset=dataset, task_id=task.id)

            return JsonResponse({
                "status": "success",
                "task_id": task.id,
                "dataset_id": str(dataset.id),
                "message": "Upload successful, processing started."
            })

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request or missing file"}, status=400)


@csrf_exempt
def run_custom_scenario(request):
    """Standard Django API endpoint for custom hyperparameter runs."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        # Manually parse the JSON body
        body = json.loads(request.body)
        dataset_id = body.get("dataset_id")

        if not dataset_id:
            return JsonResponse({"error": "dataset_id is required"}, status=400)

        # Manually cast types and provide fallbacks
        try:
            cp_scale = float(body.get("changepoint_prior_scale", 0.05))
            seasonality = str(body.get("seasonality_mode", "additive"))
            holidays = bool(body.get("include_holidays", False))
        except ValueError:
            return JsonResponse({"error": "Invalid data types for hyperparameters"}, status=400)

        # Retrieve the dataset
        dataset = get_object_or_404(ForecastDataset, id=dataset_id)

        # Trigger Celery Worker
        task = generate_forecast_task.delay(
            dataset_id=str(dataset.id),
            changepoint_prior_scale=cp_scale,
            seasonality_mode=seasonality,
            include_holidays=holidays
        )

        # Log the run in Postgres
        ForecastRun.objects.create(
            dataset=dataset,
            task_id=task.id,
            changepoint_prior_scale=cp_scale,
            seasonality_mode=seasonality,
            include_holidays=holidays
        )

        return JsonResponse({
            "status": "success",
            "task_id": task.id,
            "message": "Scenario triggered successfully."
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

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

def get_mapped_columns(available_columns: list, mappings: Dict[str, list]) -> Dict[str, str]:
    """Maps available column names to standardized canonical names."""
    columns_dict = {}
    for canonical_name, possible_names in mappings.items():
        # Case-insensitive match is usually safer, but keeping your original logic here
        match = next((name for name in possible_names if name in available_columns), None)
        if match:
            columns_dict[canonical_name] = match
    return columns_dict

