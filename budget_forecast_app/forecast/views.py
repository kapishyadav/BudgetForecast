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

logger = setup_logging()

def upload_file(request):
    """Renders the upload form and handles forecast display."""
    if request.method == "POST" and request.FILES.get("dataset"):
        file = request.FILES["dataset"]
        # forecast_type = request.POST.get("forecast_type", "monthly")  # default to monthly
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)

        # Safely convert to enum
        selected_type = request.POST.get("forecast_type", "monthly")
        logger.info(f"DEBUG selected_type from POST: {selected_type}")
        try:
            forecast_type = ForecastType(selected_type)
        except ValueError:
            forecast_type = ForecastType.MONTHLY

        # Optional account name input
        account_name = request.POST.get("account_name", "").strip()

        try:
            logger.info(f"Running forecast with type: {forecast_type}")

            # "Method overloading" behavior via kwargs
            kwargs = {}

            # only include account_name if relevant
            if forecast_type == ForecastType.ACCOUNT and account_name:
                kwargs["account_name"] = account_name

            result = run_forecast(file_path, forecast_type, **kwargs)

            forecast_df = result["forecast"]


            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file_name = f"{filename}-{forecast_type}-{timestamp}.csv"

            # Save CSV file
            forecast_type_str = forecast_type.value if hasattr(forecast_type, "value") else str(forecast_type)
            output_dir = os.path.join("forecasts", forecast_type_str)
            os.makedirs(output_dir, exist_ok=True)
            csv_path = os.path.join(output_dir, csv_file_name)

            logger.info(f"Saved forecast CSV: {csv_path}")

            # Convert forecast dataframe to JSON for Chart.js
            forecast_json = forecast_df.to_json(orient="records", date_format="iso")

            logger.info("Successfully converted forecast data for Chart.js")

            forecast_df.to_csv(csv_path, index=False)

            logger.info(f"DEBUG result keys: {list(result.keys())}")
            logger.info(f"DEBUG metrics: {result.get('metrics')}")

            return render(request, "forecast/dashboard.html", {
                "metrics": result["metrics"],
                "forecast_data": forecast_json,
                "forecast_type": forecast_type.value if hasattr(forecast_type, "value") else forecast_type,
                "csv_filename": csv_file_name,
                "account_name": account_name if forecast_type == ForecastType.ACCOUNT else None,
            })
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return render(request, "forecast/upload.html", {"error": str(e)})

    return render(request, "forecast/upload.html")

def download_forecast_csv(request, filename):
    # Forecasts are stored under /forecasts/<forecast_type>/<filename>
    forecast_type = filename.split("-")[1]  # e.g., "monthly" from "monthly-20251102_190900.csv"
    csv_path = os.path.join("forecasts", forecast_type, filename)

    if not os.path.exists(csv_path):
        return HttpResponse("Forecast CSV not found.", status=404)

    return FileResponse(open(csv_path, "rb"), as_attachment=True, filename=filename)


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

