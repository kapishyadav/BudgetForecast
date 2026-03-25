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

    # --- DYNAMIC VALIDATION ---
    if granularity == Granularity.MONTHLY:
        if 'month' not in df.columns or 'spend' not in df.columns:
            raise ValueError("DataFrame for monthly granularity must contain 'month' and 'spend' columns.")
    elif granularity == Granularity.DAILY:
        if 'date' not in df.columns or 'spend' not in df.columns:
            raise ValueError("DataFrame for daily granularity must contain 'date' and 'spend' columns.")
    else:
        raise ValueError(f"Unsupported granularity: {granularity}")

    # We apply whichever filters were passed from the UI.
    # If a filter is None, it safely ignores it.
    if account_name:
        data = data[data['account_name'] == account_name]

    if service_name:
        data = data[data['service_name'] == service_name]

    if bu_code is not None:  # Using `is not None` in case a BU code is mathematically 0
        data = data[data['bu_code'] == bu_code]

    if segment_name:
        # Note: adjust 'segment' to match whatever you named the column in df renaming step
        data = data[data['segment'] == segment_name]

    # If the user's specific combination of filters yields no data, catch it before Prophet crashes
    if data.empty:
        raise ValueError(
            "The selected combination of filters resulted in an empty dataset. Cannot generate forecast.")

    # ==========================================
    # ROUTE TO PIPELINE
    # ==========================================
    if forecast_type == ForecastType.OVERALL_AGGREGATE:
        logger.info(f"DEBUG starting save_overall_aggregate_forecasts now!")
        forecast_df, historical_df, metrics_dict = save_overall_aggregate_forecasts(data, logger, granularity)

    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f"DEBUG starting save_forecast_by_accounts now!")
        forecast_df, historical_df, metrics_dict = save_forecast_by_accounts(data, logger, granularity)

    elif forecast_type == ForecastType.SERVICE:
        forecast_df, historical_df, metrics_dict = save_forecasts_by_service(data, logger, granularity)

    elif forecast_type == ForecastType.BUCODE:
        logger.info(f"Value of bu Code in prophet_model.py : {bu_code}")
        forecast_df, historical_df, metrics_dict = save_forecasts_by_bucode(data, logger,granularity)

    elif forecast_type == ForecastType.SEGMENT:
        logger.info(f"Value of segment in prophet_model.py : {segment_name}")
        forecast_df, historical_df, metrics_dict = save_forecasts_by_segment(data, logger, granularity)

    else:
        raise ValueError(f"Invalid forecast type: {forecast_type}")

    return forecast_df, historical_df, metrics_dict

