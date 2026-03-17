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

import plotly.io as pio
import json
import os
import io
import pandas as pd
import traceback
from pathlib import Path

logger = setup_logging()

def hello_vite(request):
    return render(request, "hello_vite.html")


def upload_file(request):
    """Renders the upload form and handles forecast display."""
    if request.method == "POST" and request.FILES.get("dataset"):

        # Clear any old session data to avoid stale suggestions
        for key in ["csv_base_filename", "uploaded_file_path"]:
            if key in request.session:
                del request.session[key]

        file = request.FILES["dataset"]
        # forecast_type = request.POST.get("forecast_type", "monthly")  # default to monthly
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)
        logger.info(f"DEBUG select filename from POST: {filename}")
        logger.info(f"DEBUG select filename from POST: {file_path}")

        # --- CLEANUP FUNCTION ---
        delete_old_files(max_files=5)

        # Make sure it's stored in session right away
        request.session["csv_base_filename"] = filename
        request.session["uploaded_file_path"] = file_path
        request.session.modified = True

        # Safely convert to enum
        selected_type = request.POST.get("forecast_type", "overall_aggregate")
        granularity = request.POST.get("granularity", "monthly")

        logger.info(f"DEBUG selected_type from POST: {selected_type}")
        logger.info(f"DEBUG granularity from POST: {granularity}")
        try:
            forecast_type = ForecastType(selected_type)
            granularity = Granularity(granularity)

        except ValueError:
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity = Granularity.MONTHLY

        # Optional account name input
        account_name = request.POST.get("account_name", "").strip()

        # Optional service name input
        service_name = request.POST.get("service_name", "").strip()

        # Optional bu code input
        bu_code_raw = request.POST.get("bu_code", "").strip()

        if bu_code_raw == "":
            bu_code = None
        else:
            bu_code = int(bu_code_raw)  # will only run when non-empty


        # Optional segment name input
        segment_name = request.POST.get("segment_name", "").strip()

        try:
            logger.info(f"Running forecast with type: {forecast_type} and granularity : {granularity}")
            forecast_type_str = forecast_type.value if hasattr(forecast_type, "value") else str(forecast_type)

            # Get current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            logger.info(f"DEBUG forecast_type_str: {forecast_type_str}")

            # "Method overloading" behavior via kwargs
            kwargs = {}

            # only include account_name if relevant
            if forecast_type == ForecastType.ACCOUNT and account_name:
                kwargs["account_name"] = account_name

            if forecast_type == ForecastType.SERVICE:
                if service_name:
                    kwargs["service_name"] = service_name
                if account_name:
                    kwargs["account_name"] = account_name

            if forecast_type == ForecastType.BUCODE:
                if bu_code is not None:
                    kwargs["bu_code"] = bu_code

            if forecast_type == ForecastType.SEGMENT:
                if segment_name:
                    kwargs["segment_name"] = segment_name
                if service_name:
                    kwargs["service_name"] = service_name
                if account_name:
                    kwargs["account_name"] = account_name

            result = run_forecast(file_path, forecast_type, granularity=granularity, **kwargs)

            forecast_df = result["forecast"]
            historical_df = result["history"]

            # Convert forecast dataframe to JSON for Chart.js
            forecast_json = forecast_df.to_json(orient="records", date_format="iso")
            historical_json = historical_df.to_json(orient="records", date_format="iso")

            logger.info("Successfully converted forecast data for Chart.js")

            # Store the forecast data in session for later CSV download
            request.session['forecast_csv_json'] = forecast_df.to_json(orient="records", date_format="iso")
            request.session['csv_base_filename'] = filename  # original uploaded file name
            request.session['forecast_type'] = forecast_type.value if hasattr(forecast_type, "value") else str(
                forecast_type)
            request.session['account_name'] = account_name
            request.session['service_name'] = service_name
            request.session['bu_code'] = bu_code
            request.session['segment_name'] = segment_name

            logger.info(f"DEBUG result keys: {list(result.keys())}")
            # logger.info(f"DEBUG metrics: {result.get('metrics')}")

            return render(request, "forecast/dashboard.html", {
                # "metrics": result["metrics"],
                "forecast_data": forecast_json,
                "historical_data": historical_json,
                "forecast_type": forecast_type.value if hasattr(forecast_type, "value") else forecast_type,
                # "csv_filename": csv_file_name,
                "account_name": account_name if forecast_type in [ForecastType.ACCOUNT, ForecastType.SERVICE,
                                                                  ForecastType.SEGMENT] else None,
                "service_name": service_name if forecast_type in [ForecastType.SERVICE,
                                                                  ForecastType.SEGMENT] else None,
                "bu_code": bu_code if forecast_type == ForecastType.BUCODE else None,
                "segment_name": segment_name if forecast_type == ForecastType.SEGMENT else None,
            })
        except Exception as e:
            logger.error(f"Forecasting failed in views: {e}")
            return render(request, "forecast/upload.html", {"error": str(e)})

    return render(request, "forecast/upload.html")


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

