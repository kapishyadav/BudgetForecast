"""
prophet_model.py
----------------
Prophet-based forecasting module.
Loads CSV, trains Prophet model, and returns forecast + Plotly figure.
"""

from .legacy_prophet_model import *
from .enums import ForecastType
from .utils.setup_logging import setup_logging

def run_prophet_forecast(
        csv_path: str,
        forecast_type: ForecastType = ForecastType.MONTHLY,
        logger=None,
        account_name = None,
        service_name = None,
        bu_code = None,
        segment_name = None,
        periods: int = 24):
    """
    Train and forecast using Prophet on a monthly spend dataset.

    Args:
        csv_path (str): Path to CSV file with 'month' and 'spend' columns.
        periods (int): Months to forecast ahead (default=24).

    Returns:
        tuple: (forecast_df, metrics_dict, plotly_figure_dict)
    """
    if logger is None:
        logger = setup_logging()

    try:
        data = pd.read_csv(csv_path)
        logger.info(f"Dataset loaded successfully. Shape: {data.shape}")
    except FileNotFoundError:
        logger.error("Dataset file not found.")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Validate columns
    if "month" not in data.columns or "spend" not in data.columns:
        raise ValueError("CSV must contain 'month' and 'spend' columns.")

    if forecast_type == ForecastType.MONTHLY:
        forecast_df, historical_df = save_monthly_aggregate_forecasts(data, csv_path, logger)
        logger.info(f"DEBUG save_monthly_aggregate_forecasts complete!")
    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f"DEBUG starting save_forecast_by_accounts now!")
        forecast_df, historical_df = save_forecast_by_accounts(data, csv_path, logger, account_name)
        logger.info(f"DEBUG save_forecast_by_accounts complete!")
    elif forecast_type == ForecastType.SERVICE:
        forecast_df, historical_df = save_forecasts_by_service(data, csv_path, logger, account_name, service_name)
    elif forecast_type == ForecastType.BUCODE:
        logger.info(f"Value of bu Code in prophet_model.py : {bu_code}, type: {type(bu_code)}")
        forecast_df, historical_df = save_forecasts_by_bucode(data, csv_path, logger, bu_code)
    elif forecast_type == ForecastType.SEGMENT:
        logger.info(f"Value of segment in prophet_model.py : {segment_name}, type: {type(segment_name)}")
        forecast_df, historical_df = save_forecasts_by_segment(data, csv_path, logger, account_name, service_name, segment_name)
    else:
        raise ValueError(f"Invalid forecast type: {forecast_type}")


    return forecast_df, historical_df
