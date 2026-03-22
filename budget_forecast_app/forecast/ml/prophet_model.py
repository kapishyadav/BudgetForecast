"""
prophet_model.py
----------------
Prophet-based forecasting module.
Loads DataFrame, trains Prophet model, and returns forecast + Plotly figure.
"""
import pandas as pd

from .legacy_prophet_model import *
from .enums import ForecastType, Granularity
from .utils.setup_logging import setup_logging
from typing import List, Dict


def run_prophet_forecast(
        df: pd.DataFrame,
        forecast_type: ForecastType = ForecastType.OVERALL_AGGREGATE,
        granularity: Granularity = Granularity.MONTHLY,
        logger=None,
        account_name=None,
        service_name=None,
        bu_code=None,
        segment_name=None):
    if logger is None:
        logger = setup_logging()

    data = df
    logger.info(f"Dataset loaded successfully from DB. Shape: {data.shape}")

    # 1. Safety Check (Replaces the old FileNotFoundError)
    if data is None or data.empty:
        raise ValueError("The provided dataset is empty and contains no historical spend data.")

    # 2. Validate columns
    # Note: Since the Celery task renames your DB 'date' column back to 'month',
    # we just need to ensure 'month' and 'spend' are here.
    if "month" not in data.columns or "spend" not in data.columns:
        raise ValueError("DataFrame must contain 'month' and 'spend' columns.")

    # 3. Route to the correct pipeline
    if forecast_type == ForecastType.OVERALL_AGGREGATE:
        logger.info(f"DEBUG starting save_overall_aggregate_forecasts now!")
        forecast_df, historical_df, metrics_dict = save_overall_aggregate_forecasts(data, logger, granularity)

    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f"DEBUG starting save_forecast_by_accounts now!")
        forecast_df, historical_df, metrics_dict = save_forecast_by_accounts(data, logger, account_name, granularity)

    elif forecast_type == ForecastType.SERVICE:
        forecast_df, historical_df, metrics_dict = save_forecasts_by_service(data, logger, account_name, service_name,
                                                                             granularity)

    elif forecast_type == ForecastType.BUCODE:
        logger.info(f"Value of bu Code in prophet_model.py : {bu_code}")
        forecast_df, historical_df, metrics_dict = save_forecasts_by_bucode(data, logger, bu_code, granularity)

    elif forecast_type == ForecastType.SEGMENT:
        logger.info(f"Value of segment in prophet_model.py : {segment_name}")
        forecast_df, historical_df, metrics_dict = save_forecasts_by_segment(data, logger, account_name, service_name,
                                                                             segment_name, granularity)

    else:
        raise ValueError(f"Invalid forecast type: {forecast_type}")

    return forecast_df, historical_df, metrics_dict

