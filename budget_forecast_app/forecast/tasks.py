
import logging

import pandas as pd
from celery import shared_task

# Import your ML logic and Enums
from .ml.main import run_forecast
from .ml.enums import ForecastType, Granularity
from .models import ForecastDataset, HistoricalSpend

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def generate_forecast_task(self, dataset_id, forecast_type_str, granularity_str, **kwargs):
    """
    Background task to run the Prophet ML pipeline.
    Receives simple strings/dicts and returns a JSON-serializable dictionary.
    """
    logger.info(f"Task {self.request.id}: Starting forecast generation for dataset id: {dataset_id}")

    try:

        historical_data = HistoricalSpend.objects.filter(dataset_id=dataset_id).values(
            'date', 'spend', 'account_name', 'service_name', 'bu_code', 'segment'
        )

        if not historical_data:
            raise ValueError(f"No historical data found for dataset {dataset_id}")

        df = pd.DataFrame(list(historical_data))
        # Rename columns back to what your Prophet script expects internally
        df.rename(columns={
            'date': 'month',  # Or 'Date', depending on what run_forecast uses
            'account_name': 'accountName',
            'service_name': 'serviceName',
            'bu_code': 'buCode'
        }, inplace=True)
        #  Convert strings back to Enums
        # (Since Celery only accepts basic data types via the message broker)
        try:
            forecast_type = ForecastType(forecast_type_str)
            granularity = Granularity(granularity_str)
        except ValueError:
            logger.warning("Invalid enums passed, falling back to defaults.")
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity = Granularity.MONTHLY

        #  Run the heavy ML pipeline
        result = run_forecast(df, forecast_type, granularity=granularity, **kwargs)

        # Extract the Pandas DataFrames
        forecast_df = result["forecast"]
        historical_df = result["history"]
        metrics_dict = result["metrics"]

        # Convert DataFrames to JSON strings
        # (This makes them safe to store in the Redis result backend)
        forecast_json = forecast_df.to_json(orient="records", date_format="iso")
        historical_json = historical_df.to_json(orient="records", date_format="iso")

        logger.info(f"Task {self.request.id}: Forecast complete. Saving results to Redis.")

        # Return the payload.
        # Redis will hold onto this dictionary until your Django view asks for it!
        return {
            "status": "success",
            "forecast_json": forecast_json,
            "historical_json": historical_json,
            "metrics" : metrics_dict,
            "dataset_id" : dataset_id
        }

    except Exception as e:
        logger.error(f"Task {self.request.id}: Forecasting failed - {str(e)}")
        # Return the error safely so the frontend can catch it and display a message
        return {
            "status": "error",
            "message": str(e)
        }
