# Create your views here.
from datetime import datetime

from django.shortcuts import render
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .ml.main import run_forecast
from .ml.utils.setup_logging import setup_logging
from .ml.enums import ForecastType

import plotly.io as pio
import json
import os
import pandas as pd
import traceback
from pathlib import Path

logger = setup_logging()


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

        # Make sure it's stored in session right away
        request.session["csv_base_filename"] = filename
        request.session["uploaded_file_path"] = file_path
        request.session.modified = True

        # Safely convert to enum
        selected_type = request.POST.get("forecast_type", "monthly")
        logger.info(f"DEBUG selected_type from POST: {selected_type}")
        try:
            forecast_type = ForecastType(selected_type)
        except ValueError:
            forecast_type = ForecastType.MONTHLY

        # Optional account name input
        account_name = request.POST.get("account_name", "").strip()

        # Optional service name input
        service_name = request.POST.get("service_name", "").strip()

        try:
            logger.info(f"Running forecast with type: {forecast_type}")
            forecast_type_str = forecast_type.value if hasattr(forecast_type, "value") else str(forecast_type)
            # Save CSV file
            # output_dir = Path("forecasts_results")
            # output_dir.mkdir(parents=True, exist_ok=True)

            # Strip .csv from filename if present
            # base_filename = Path(filename).stem

            # Get current timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create CSV filename
            # csv_file_name = f"{base_filename}-{forecast_type_str}-{timestamp}.csv"

            # csv_path = output_dir / forecast_type_str
            # csv_path.mkdir(parents=True, exist_ok=True)

            # full_csv_path = csv_path / csv_file_name

            logger.info(f"DEBUG forecast_type_str: {forecast_type_str}")
            # logger.info(f"DEBUG output_dir : {output_dir}")
            # logger.info(f"DEBUG csv_path : {csv_path}")
            # logger.info(f"DEBUG full_csv_path : {full_csv_path}")

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

            result = run_forecast(file_path, forecast_type, **kwargs)

            forecast_df = result["forecast"]

            # Convert forecast dataframe to JSON for Chart.js
            forecast_json = forecast_df.to_json(orient="records", date_format="iso")

            logger.info("Successfully converted forecast data for Chart.js")

            # if not os.path.exists(csv_path):
            #     logger.error(f"File does not exist at expected path: {csv_path}")
            # else:
            #     logger.info("File exists and is ready for access.")

            # logger.info(f"CSV filename repr: {repr(csv_file_name)}")

            # logger.info(f"DEBUG Forecast DF length: {len(forecast_df)}")
            # forecast_df.to_csv(full_csv_path, index=False)
            # logger.info(f"DEBUG Forecast CSV saved at: {full_csv_path}")
            # assert os.path.exists(full_csv_path), f"File not found after saving: {csv_path}"
            # logger.error(traceback.format_exc())

            # Store the forecast data in session for later CSV download
            request.session['forecast_csv_json'] = forecast_df.to_json(orient="records", date_format="iso")

            request.session['csv_base_filename'] = filename  # original uploaded file name
            request.session['forecast_type'] = forecast_type.value if hasattr(forecast_type, "value") else str(
                forecast_type)
            request.session['account_name'] = account_name
            request.session['service_name'] = service_name

            logger.info(f"DEBUG result keys: {list(result.keys())}")
            # logger.info(f"DEBUG metrics: {result.get('metrics')}")

            return render(request, "forecast/dashboard.html", {
                # "metrics": result["metrics"],
                "forecast_data": forecast_json,
                "forecast_type": forecast_type.value if hasattr(forecast_type, "value") else forecast_type,
                # "csv_filename": csv_file_name,
                "account_name": account_name if forecast_type in [ForecastType.ACCOUNT, ForecastType.SERVICE] else None,
                "service_name": service_name if forecast_type == ForecastType.SERVICE else None,
            })
        except Exception as e:
            logger.error(f"Forecasting failed in views: {e}")
            return render(request, "forecast/upload.html", {"error": str(e)})

    return render(request, "forecast/upload.html")


def get_suggestions(request):
    query = request.GET.get("q", "").strip().lower()
    field = request.GET.get("field")  # 'account' or 'service'

    filename = request.session.get("csv_base_filename")
    if not filename:
        print("❌ No file found in session — likely no upload in this session.")
        # Try to get the most recently uploaded file (as fallback)
        fs = FileSystemStorage()
        files = sorted(fs.listdir(fs.location)[1], key=lambda f: os.path.getctime(os.path.join(fs.location, f)),
                       reverse=True)
        if files:
            filename = files[0]
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

        if field == "account":
            col_name = "accountName"
        elif field == "service":
            col_name = "serviceName"
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
    csv_data = request.session.get("forecast_csv_json")
    forecast_df = pd.read_json(csv_data, orient="records")

    # Convert DataFrame to CSV string
    csv_string = forecast_df.to_csv(index=False)

    if not csv_data:
        return HttpResponse("No forecast data available. Please generate a forecast first.", status=404)

    base_filename = request.session.get("csv_base_filename", "forecast")
    account_name = request.session.get("account_name", "")
    service_name = request.session.get("service_name", "")
    forecast_type = request.session.get("forecast_type", "monthly")

    # Strip the .csv extension if present
    base_filename = os.path.splitext(base_filename)[0]

    # Clean up names (remove spaces, lower-case)
    def clean(name):
        return name.strip().replace(" ", "_").lower() if name else ""

    account_name = clean(account_name)
    service_name = clean(service_name)

    # Construct filename based on conditions
    if account_name and service_name:
        filename = f"{base_filename}-forecasts-{account_name}-{service_name}.csv"
    elif account_name:
        filename = f"{base_filename}-forecasts-{account_name}.csv"
    else:
        filename = f"{base_filename}-forecasts-{forecast_type}-aggregate.csv"

    forecast_df.to_csv(filename, index=False)

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
