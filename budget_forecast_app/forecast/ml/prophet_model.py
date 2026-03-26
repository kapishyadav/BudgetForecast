"""
prophet_model.py
----------------
Unified Prophet forecasting module.
Handles data validation, dynamic filtering, and Prophet model execution.
"""
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import warnings

from .enums import Granularity
from .utils.setup_logging import setup_logging

warnings.filterwarnings("ignore")


def validate_and_filter_data(df: pd.DataFrame, granularity: Granularity, **kwargs) -> pd.DataFrame:
    """SRP: This function ONLY handles data validation and filtering."""
    if df is None or df.empty:
        raise ValueError("The provided dataset is empty and contains no historical spend data.")

    # 1. Dynamic Column Validation
    if granularity == Granularity.MONTHLY and ('month' not in df.columns or 'spend' not in df.columns):
        raise ValueError("DataFrame for monthly granularity must contain 'month' and 'spend' columns.")
    elif granularity == Granularity.DAILY and ('date' not in df.columns or 'spend' not in df.columns):
        raise ValueError("DataFrame for daily granularity must contain 'date' and 'spend' columns.")

    # 2. Dynamic Filtering
    data = df.copy()
    filter_mapping = {
        'account_name': 'account_name',
        'service_name': 'service_name',
        'bu_code': 'bu_code',
        'segment_name': 'segment'
    }

    for kwarg_key, df_column in filter_mapping.items():
        val = kwargs.get(kwarg_key)
        if val is not None:
            data = data[data[df_column] == val]

    # 3. Final Safety Check
    if data.empty:
        raise ValueError("The selected combination of filters resulted in an empty dataset. Cannot generate forecast.")

    return data


def run_prophet_forecast(df: pd.DataFrame, granularity: Granularity = Granularity.MONTHLY, logger=None, **kwargs):
    """
    Main entry point. Prepares data and runs the universal Prophet pipeline.
    """
    if logger is None:
        logger = setup_logging()

    # 1. Prepare Data
    data = validate_and_filter_data(df, granularity, **kwargs)
    logger.info(f"Dataset prepared successfully. Shape: {data.shape}")

    # 2. Configuration Map based on Granularity
    if granularity == Granularity.MONTHLY:
        date_col = 'month'
        freq = 'ME'
        periods = 24
        avg_multiplier = 1
        period_label = "24 mo"
    elif granularity == Granularity.DAILY:
        date_col = 'date'
        freq = 'D'
        periods = 90
        avg_multiplier = 30.44
        period_label = "90 days"
    else:
        raise ValueError("Granularity must be MONTHLY or DAILY.")

    # 3. Grouping and Prophet Formatting
    data[date_col] = pd.to_datetime(data[date_col], errors='coerce')
    grouped_spend = data.groupby(date_col, as_index=False)["spend"].sum()

    prophet_df = grouped_spend.rename(columns={date_col: "ds", "spend": "y"}).dropna(subset=['ds'])
    last_date = prophet_df['ds'].max()

    # 4. Model Training
    m = Prophet()
    logger.info(f"Fitting Prophet model for {granularity.value} granularity. Rows: {len(prophet_df)}")
    m.fit(prophet_df)

    # 5. Cross Validation Metrics
    metrics_dict = {"rmse": 0, "mse": 0, "mae": 0, "mape": 0, "total_forecasted_spend": 0}
    try:
        logger.info("Starting historical cross-validation for metrics...")
        df_cv = cross_validation(m, initial='180 days', period='30 days', horizon='90 days')
        df_p = performance_metrics(df_cv)

        metrics_dict.update({
            "rmse": float(df_p['rmse'].mean()),
            "mse": float(df_p['mse'].mean()),
            "mae": float(df_p['mae'].mean()),
            "mape": float(df_p['mape'].mean()),
        })
        logger.info(f"Metrics calculated successfully: RMSE={metrics_dict['rmse']:.2f}")
    except Exception as e:
        logger.warning(f"Could not calculate metrics (likely insufficient historical data): {e}")

    # 6. Forecasting
    future = m.make_future_dataframe(periods=periods, freq=freq)
    forecast_full = m.predict(future)
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    # 7. Formatting Output
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    metrics_dict["total_forecasted_spend"] = float(forecast['yhat'].sum())
    metrics_dict["average_monthly_spend"] = float(forecast['yhat'].mean() * avg_multiplier)
    metrics_dict["forecast_period"] = period_label

    return forecast, prophet_df, metrics_dict
