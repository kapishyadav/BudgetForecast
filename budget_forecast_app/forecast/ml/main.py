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

from .prophet_model import run_prophet_forecast
from .utils.setup_logging import setup_logging
from .enums import ForecastType
from .legacy_prophet_model import *

logger = setup_logging()

def run_forecast(csv_path: str,
                 forecast_type: ForecastType = ForecastType.MONTHLY ,
                 account_name = None,
                 service_name = None,
                 bu_code = None,
                 segment_name = None):
    """
    Main entry point for the forecasting pipeline.

    Args:
        csv_path (str): Path to uploaded CSV file.
        model_type (str): One of ["prophet", "catboost", "linear"].
        train (bool): If True, retrains the model (for ML models only).

    Returns:
        tuple:
            - predictions: list or DataFrame of forecasted values
            - metrics: dict with RMSE, MAE, R²
            - figures: list of Plotly figure JSONs
    """

    logger.info(f"Running forecast with type: {forecast_type.value}")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    try:

        logger.info("Prophet forecasting starting.")
        if forecast_type == ForecastType.ACCOUNT:
            if not account_name:
                raise ValueError("Account name must be provided for account-level forecast.")
            # forecast_df, metrics = run_prophet_forecast(csv_path,
            #                                             forecast_type,
            #                                             logger,
            #                                             account_name)
            forecast_df, historical_df = run_prophet_forecast(csv_path,
                                                forecast_type,
                                                logger,
                                                account_name)

        elif forecast_type == ForecastType.MONTHLY:
            forecast_df, historical_df = run_prophet_forecast(csv_path, forecast_type, logger)
            logger.info(f"DEBUG run_prophet_forecast complete!")

        elif forecast_type == ForecastType.SERVICE:
            if not service_name and not account_name:
                raise ValueError("Service name and Account name must be provided for service-level forecast.")
            forecast_df, historical_df = run_prophet_forecast(csv_path,
                                                        forecast_type,
                                                        logger,
                                                        account_name,
                                                        service_name)

        elif forecast_type == ForecastType.BUCODE:
            if not bu_code:
                raise ValueError("BU Code must be provided for bu-code-level forecast.")
            logger.info(f"Value of bu Code in main.py : {bu_code}, type: {type(bu_code)}")
            forecast_df, historical_df = run_prophet_forecast(
                csv_path=csv_path,
                forecast_type=forecast_type,
                logger=logger,
                bu_code=bu_code
            )

        elif forecast_type == ForecastType.SEGMENT:
            if not segment_name and not service_name and not account_name:
                raise ValueError("Segment Name, Service name and Account name must be provided for "
                                 "segment-level forecast.")
            forecast_df, historical_df = run_prophet_forecast(
                csv_path=csv_path,
                forecast_type=forecast_type,
                logger=logger,
                account_name= account_name,
                service_name= service_name,
                segment_name=segment_name
            )

        else:
            raise ValueError(f"Unsupported forecast type: {forecast_type}")
        logger.info("Prophet forecasting complete.")


        return {
            "forecast": forecast_df,
            "history": historical_df,
            # "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Forecasting failed in main : {e}")
        raise