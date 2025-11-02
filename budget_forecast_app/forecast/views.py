# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse, Http404, FileResponse
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
        forecast_type = request.POST.get("forecast_type", "monthly")  # default to monthly
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)

        # Get forecast type from dropdown (string)
        selected_type = request.POST.get("forecast_type", "monthly")

        # Convert to Enum safely
        try:
            forecast_type = ForecastType(selected_type)
        except ValueError:
            forecast_type = ForecastType.MONTHLY  # fallback

        try:
            logger.info(f"Running forecast with type: {forecast_type}")
            result = run_forecast(file_path, forecast_type)

            forecast_df = result["forecast"]
            metrics = result["metrics"]

            # Convert forecast dataframe to JSON for Chart.js
            forecast_json = forecast_df.to_json(orient="records", date_format="iso")

            logger.info("Successfully converted forecast data for Chart.js")

            return render(request, "forecast/dashboard.html", {
                "metrics": metrics,
                "forecast_data": forecast_json,
                "forecast_type": forecast_type.value if hasattr(forecast_type, "value") else forecast_type,
            })
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return render(request, "forecast/upload.html", {"error": str(e)})

    return render(request, "forecast/upload.html")

def download_csv(request):
    csv_path = "path/to/your/generated/forecast_results.csv"  # update this

    if not os.path.exists(csv_path):
        raise Http404("CSV file not found.")

    return FileResponse(open(csv_path, "rb"), as_attachment=True, filename="forecast_results.csv")


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

