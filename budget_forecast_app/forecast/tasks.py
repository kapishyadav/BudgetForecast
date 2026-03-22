
import logging
from celery import shared_task

# Import your ML logic and Enums
from .ml.main import run_forecast
from .ml.enums import ForecastType, Granularity

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generate_forecast_task(self, file_path, forecast_type_str, granularity_str, **kwargs):
    """
    Background task to run the Prophet ML pipeline.
    Receives simple strings/dicts and returns a JSON-serializable dictionary.
    """
    logger.info(f"Task {self.request.id}: Starting forecast generation for {file_path}")

    try:
        # 1. Convert strings back to Enums
        # (Since Celery only accepts basic data types via the message broker)
        try:
            forecast_type = ForecastType(forecast_type_str)
            granularity = Granularity(granularity_str)
        except ValueError:
            logger.warning("Invalid enums passed, falling back to defaults.")
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity = Granularity.MONTHLY

        # 2. Run the heavy ML pipeline
        result = run_forecast(file_path, forecast_type, granularity=granularity, **kwargs)

        # 3. Extract the Pandas DataFrames
        forecast_df = result["forecast"]
        historical_df = result["history"]
        metrics_dict = result["metrics"]

        # 4. Convert DataFrames to JSON strings
        # (This makes them safe to store in the Redis result backend)
        forecast_json = forecast_df.to_json(orient="records", date_format="iso")
        historical_json = historical_df.to_json(orient="records", date_format="iso")

        logger.info(f"Task {self.request.id}: Forecast complete. Saving results to Redis.")

        # 5. Return the payload.
        # Redis will hold onto this dictionary until your Django view asks for it!
        return {
            "status": "success",
            "forecast_json": forecast_json,
            "historical_json": historical_json,
            "metrics" : metrics_dict,
        }

    except Exception as e:
        logger.error(f"Task {self.request.id}: Forecasting failed - {str(e)}")
        # Return the error safely so the frontend can catch it and display a message
        return {
            "status": "error",
            "message": str(e)
        }
