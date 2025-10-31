"""
prophet_model.py
----------------
Prophet-based forecasting module.
Loads CSV, trains Prophet model, and returns forecast + Plotly figure.
"""

import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import math

from .utils.setup_logging import setup_logging


def run_prophet_forecast(csv_path: str, periods: int = 24):
    """
    Train and forecast using Prophet on a monthly spend dataset.

    Args:
        csv_path (str): Path to CSV file with 'month' and 'spend' columns.
        periods (int): Months to forecast ahead (default=24).

    Returns:
        tuple: (forecast_df, metrics_dict, plotly_figure_dict)
    """
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

    # Prepare data
    data["month"] = pd.to_datetime(data["month"])
    monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})
    logger.info(f"Data prepared for Prophet. Rows: {len(prophet_df)}")

    # Train Prophet model
    m = Prophet(interval_width=0.95, yearly_seasonality=True)
    m.fit(prophet_df)
    logger.info("Prophet model trained successfully.")


    # Forecast future months
    future = m.make_future_dataframe(periods=periods, freq="M")
    forecast = m.predict(future)

    # Evaluate metrics (on existing data)
    merged = pd.merge(prophet_df, forecast[["ds", "yhat"]], on="ds", how="left")
    actual = merged["y"].dropna()
    predicted = merged["yhat"][: len(actual)]
    metrics = {
        "RMSE": round(math.sqrt(mean_squared_error(actual, predicted)), 2),
        "MAE": round(mean_absolute_error(actual, predicted), 2),
        "R2": round(r2_score(actual, predicted), 3),
    }
    logger.info(f"Forecasting metrics: {metrics}")

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prophet_df["ds"], y=prophet_df["y"], mode="lines+markers", name="Actual Spend"))
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], mode="lines", name="Forecast"))
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_upper"], mode="lines", name="Upper Bound", line=dict(dash="dot", color="gray")))
    fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat_lower"], mode="lines", name="Lower Bound", line=dict(dash="dot", color="gray")))

    fig.update_layout(
        title="Prophet Forecast: Actual vs Predicted Spend",
        xaxis_title="Month",
        yaxis_title="Spend",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    fig.show()

    logger.info("Plotly figure created successfully.")
    return forecast, metrics, fig.to_dict()
