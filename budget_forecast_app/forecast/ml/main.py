"""
main.py
-------
Central forecasting engine for the Django time series application.

This module acts as an orchestrator that decides which forecasting model
(Prophet, CatBoost, or Linear Regression) to use based on user input.
It handles dataset loading, delegates to model-specific modules, and
returns standardized outputs (metrics + Plotly figures).
"""

import os
import pandas as pd

from .prophet_model import run_prophet_forecast
from .utils.setup_logging import setup_logging
from .enums import ForecastType, Granularity

logger = setup_logging()

def run_forecast(df: pd.DataFrame,
                 forecast_type: ForecastType = ForecastType.OVERALL_AGGREGATE,
                 granularity: Granularity = Granularity.MONTHLY,
                 account_name=None,
                 service_name=None,
                 bu_code=None,
                 segment_name=None):
    """
    Main entry point for the forecasting pipeline.
    """

    logger.info(f"Running forecast with type: {forecast_type.value}")

    if df is None or df.empty:
        raise ValueError("The provided dataset is empty and contains no historical spend data.")

    try:
        logger.info("Prophet forecasting starting.")

        # ==========================================
        # 1. VALIDATE PRIMARY REQUIREMENTS
        # ==========================================
        # We only check that the primary field required for the specific forecast type exists.
        if forecast_type == ForecastType.ACCOUNT and not account_name:
            raise ValueError("Account name must be provided for account-level forecast.")

        elif forecast_type == ForecastType.SERVICE and not service_name:
            raise ValueError("Service name must be provided for service-level forecast.")

        elif forecast_type == ForecastType.BUCODE and bu_code is None:
            raise ValueError("BU Code must be provided for bu-code-level forecast.")

        elif forecast_type == ForecastType.SEGMENT and not segment_name:
            raise ValueError("Segment name must be provided for segment-level forecast.")

        elif forecast_type not in [ForecastType.OVERALL_AGGREGATE, ForecastType.ACCOUNT, ForecastType.SERVICE, ForecastType.BUCODE, ForecastType.SEGMENT]:
            raise ValueError(f"Unsupported forecast type: {forecast_type}")

        # ==========================================
        # 2. TRIGGER THE PIPELINE
        # ==========================================
        # Because `run_prophet_forecast` now handles dynamic pre-filtering,
        # we can safely pass EVERY argument. It will dynamically slice the DataFrame
        # based on whatever combination the user selected in the UI.

        if forecast_type == ForecastType.BUCODE:
             logger.info(f"Value of bu Code in main.py : {bu_code}, type: {type(bu_code)}")

        forecast_df, historical_df, metrics_dict = run_prophet_forecast(
            df=df,
            forecast_type=forecast_type,
            granularity=granularity,
            logger=logger,
            account_name=account_name,
            service_name=service_name,
            bu_code=bu_code,
            segment_name=segment_name
        )

        logger.info("Prophet forecasting complete.")

        return {
            "forecast": forecast_df,
            "history": historical_df,
             "metrics": metrics_dict
        }

    except Exception as e:
        logger.error(f"Forecasting failed in main : {e}")
        raise