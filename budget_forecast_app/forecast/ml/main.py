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
import json
import numpy as np
import plotly.io as pio

from .prophet_model import run_prophet_forecast
from .utils.setup_logging import setup_logging
from .enums import ForecastType

logger = setup_logging()

def run_forecast(csv_path: str, forecast_type: ForecastType = ForecastType.MONTHLY ,model_type: str = "prophet"):
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
    logger.info(f"Starting forecast with model: {model_type.upper()}")
    logger.info(f"Running forecast with type: {forecast_type.value}")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    try:
        if model_type.lower() == "prophet":
            logger.info("Prophet forecasting starting.")
            forecast_df, metrics = run_prophet_forecast(csv_path, forecast_type, logger)
            logger.info("Prophet forecasting complete.")

            # Convert metrics safely (NumPy → Python)
            metrics = {k: float(v) if isinstance(v, np.generic) else v for k, v in metrics.items()}

            return {
                "forecast": forecast_df,
                "metrics": metrics,
            }

        elif model_type.lower() == "catboost":
            # Placeholder — to be implemented next
            # forecast_df, metrics, fig = run_catboost_forecast(csv_path, train)
            raise NotImplementedError("CatBoost model not implemented yet.")

        elif model_type.lower() == "linear":
            # Placeholder — to be implemented next
            # forecast_df, metrics, fig = run_linear_forecast(csv_path, train)
            raise NotImplementedError("Linear Regression model not implemented yet.")

        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    except Exception as e:
        logger.error(f"Forecasting failed: {e}")
        raise
