
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

        try:
            forecast_type = ForecastType(forecast_type_str)
            granularity = Granularity(granularity_str)
        except ValueError:
            logger.warning("Invalid enums passed, falling back to defaults.")
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity = Granularity.MONTHLY

        # 3. Handle the Date/Month column requirement safely
        # forecast_monthly_spend expects 'month', forecast_daily_spend expects 'date'
        if granularity == Granularity.MONTHLY:
            df.rename(columns={'date': 'month'}, inplace=True)

        # NOTICE: We completely removed the camelCase renaming for account_name, etc.
        # They will remain snake_case, which matches the new run_prophet_forecast filters!

        # 4. Run the heavy ML pipeline
        # **kwargs safely passes account_name, service_name, etc. directly into the pipeline
        logger.info(f"Task {self.request.id}: Passing kwargs to run_forecast: {kwargs}")
        result = run_forecast(df, forecast_type, granularity=granularity, **kwargs)

        # 5. Extract the Pandas DataFrames
        forecast_df = result["forecast"]
        historical_df = result["history"]
        metrics_dict = result["metrics"]

        # 6. Convert DataFrames to JSON strings safely
        forecast_json = forecast_df.to_json(orient="records", date_format="iso")
        historical_json = historical_df.to_json(orient="records", date_format="iso")

        logger.info(f"Task {self.request.id}: Forecast complete. Saving results to Redis.")

        # 7. Return the payload.
        return {
            "status": "success",
            "forecast_json": forecast_json,
            "historical_json": historical_json,
            "metrics": metrics_dict,
            "dataset_id": dataset_id
        }

    except Exception as e:
        logger.error(f"Task {self.request.id}: Forecasting failed - {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }
