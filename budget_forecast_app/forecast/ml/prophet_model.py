"""
prophet_model.py
----------------
Prophet-based forecasting module.
Loads CSV, trains Prophet model, and returns forecast + Plotly figure.
"""
import plotly.io as pio
import json

from .legacy_prophet_model import *
from .enums import ForecastType
from .utils.setup_logging import setup_logging

def run_prophet_forecast(
        csv_path: str,
        forecast_type: ForecastType = ForecastType.MONTHLY,
        logger=None, periods: int = 24):
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

    #Saves as HTML File
    #TO DO: make sure that it resturns JSON response to display
    # in the dashboard using Django.
    if forecast_type == ForecastType.MONTHLY:
        forecast_df, metrics = save_monthly_aggregate_forecasts(data, csv_path, logger)
    elif forecast_type == ForecastType.ACCOUNT:
        forecast_df, metrics, fig = save_forecast_by_accounts(data, csv_path, logger)
    elif forecast_type == ForecastType.SERVICE:
        forecast_df, metrics, fig = save_forecasts_by_service(data, csv_path, logger)
    else:
        raise ValueError(f"Invalid forecast type: {forecast_type}")


    # # Prepare data
    # data["month"] = pd.to_datetime(data["month"])
    # monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    # prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})
    # logger.info(f"Data prepared for Prophet. Rows: {len(prophet_df)}")
    #
    # # Train Prophet model
    # m = Prophet(interval_width=0.95, yearly_seasonality=True)
    # m.fit(prophet_df)
    # logger.info("Prophet model trained successfully.")
    #
    #
    # # Forecast future months
    # future = m.make_future_dataframe(periods=periods, freq="M")
    # forecast = m.predict(future)
    #
    # # Evaluate metrics (on existing data)
    # merged = pd.merge(prophet_df, forecast[["ds", "yhat"]], on="ds", how="left")
    # actual = merged["y"].dropna()
    # predicted = merged["yhat"][: len(actual)]
    # metrics = {
    #     "RMSE": round(math.sqrt(mean_squared_error(actual, predicted)), 2),
    #     "MAE": round(mean_absolute_error(actual, predicted), 2),
    #     "R2": round(r2_score(actual, predicted), 3),
    # }
    # logger.info(f"Forecasting metrics: {metrics}")

    logger.info("Plotly figure created successfully.")
    return forecast_df, metrics
