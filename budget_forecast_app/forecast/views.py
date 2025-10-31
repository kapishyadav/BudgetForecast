# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .ml.main import run_forecast
from .ml.utils.setup_logging import setup_logging
from .ml.enums import ForecastType

import plotly.io as pio
import json

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

            figure = result["figure_json"]

            if isinstance(figure, dict):
                figure_json = json.dumps(figure)
            else:
                figure_json = pio.to_json(figure)
            print("DEBUG figure_json:", type(figure_json), figure_json[:500])

            logger.info(f"Figure JSON: {result['figure_json']}")
            return render(request, "forecast/dashboard.html", {
                "metrics": result["metrics"],
                "figure_json": figure_json,
                "forecast_type": forecast_type.value if hasattr(forecast_type, "value") else forecast_type,
            })
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return render(request, "forecast/upload.html", {"error": str(e)})

    return render(request, "forecast/upload.html")


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

