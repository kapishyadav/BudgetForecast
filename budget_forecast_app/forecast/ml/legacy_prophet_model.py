import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import plot_plotly, plot_components_plotly
import warnings
from .enums import ForecastType, Granularity

warnings.filterwarnings("ignore")


# ==========================================
# CORE PROPHET PIPELINES
# ==========================================

def forecast_monthly_spend(data, logger, forecast_type):
    """Generates monthly Prophet forecasts from pre-filtered data."""
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    monthly_spend = data.groupby("month", as_index=False)["spend"].sum()

    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})
    last_date = prophet_df['ds'].max()

    m = Prophet()
    logger.info(f"DEBUG Fitting Prophet model in forecast_monthly_spend for {forecast_type}!")
    m.fit(prophet_df)

    # Calculate Accuracy Metrics
    metrics_dict = {}
    try:
        logger.info("Starting historical cross-validation for metrics...")
        df_cv = cross_validation(m, initial='180 days', period='30 days', horizon='90 days')
        df_p = performance_metrics(df_cv)

        metrics_dict = {
            "rmse": float(df_p['rmse'].mean()),
            "mse": float(df_p['mse'].mean()),
            "mae": float(df_p['mae'].mean()),
            "mape": float(df_p['mape'].mean()),
            "total_forecasted_spend": 0
        }
        logger.info(f"Metrics calculated successfully: RMSE={metrics_dict['rmse']:.2f}")
    except Exception as e:
        logger.warning(f"Could not calculate metrics: {e}")
        metrics_dict = {"rmse": 0, "mse": 0, "mae": 0, "mape": 0, "total_forecasted_spend": 0}

    future = m.make_future_dataframe(periods=12 * 2, freq='ME')
    forecast_full = m.predict(future)
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    # Trim forecast
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    metrics_dict["total_forecasted_spend"] = float(forecast['yhat'].sum())

    return forecast, prophet_df, metrics_dict


def forecast_daily_spend(data, logger, forecast_type):
    """Generates daily Prophet forecasts from pre-filtered data."""
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    daily_spend = data.groupby("date", as_index=False)["spend"].sum()

    prophet_df = daily_spend.rename(columns={"date": "ds", "spend": "y"})
    prophet_df = prophet_df.dropna(subset=['ds'])

    last_date = prophet_df['ds'].max()

    m = Prophet()
    logger.info(f"DEBUG Fitting Prophet model in forecast_daily_spend for {forecast_type}!")
    m.fit(prophet_df)

    # Calculate Accuracy Metrics
    metrics_dict = {}
    try:
        logger.info("Starting historical cross-validation for metrics...")
        df_cv = cross_validation(m, initial='180 days', period='30 days', horizon='90 days')
        df_p = performance_metrics(df_cv)

        metrics_dict = {
            "rmse": float(df_p['rmse'].mean()),
            "mse": float(df_p['mse'].mean()),
            "mae": float(df_p['mae'].mean()),
            "mape": float(df_p['mape'].mean()),
            "total_forecasted_spend": 0
        }
    except Exception as e:
        logger.warning(f"Could not calculate metrics: {e}")
        metrics_dict = {"rmse": 0, "mse": 0, "mae": 0, "mape": 0, "total_forecasted_spend": 0}

    future = m.make_future_dataframe(periods=90, freq='D')
    forecast_full = m.predict(future)
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    # Trim forecast
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    metrics_dict["total_forecasted_spend"] = float(forecast['yhat'].sum())

    return forecast, prophet_df, metrics_dict


# ==========================================
# ROUTING FUNCTIONS (Simplified!)
# ==========================================
# Note: I kept the exact same function signatures (arguments) so your
# run_prophet_forecast function doesn't break, but we just ignore the
# redundant arguments like 'account_name' since 'data' is already filtered.

def save_overall_aggregate_forecasts(data, logger, granularity):
    if granularity == Granularity.MONTHLY:
        return forecast_monthly_spend(data, logger, ForecastType.OVERALL_AGGREGATE)
    elif granularity == Granularity.DAILY:
        return forecast_daily_spend(data, logger, ForecastType.OVERALL_AGGREGATE)
    raise ValueError("Granularity field must be MONTHLY OR DAILY.")


def save_forecast_by_accounts(data, logger, granularity):
    # data is ALREADY filtered to 'account_name'.
    if granularity == Granularity.MONTHLY:
        return forecast_monthly_spend(data, logger, ForecastType.ACCOUNT)
    elif granularity == Granularity.DAILY:
        return forecast_daily_spend(data, logger, ForecastType.ACCOUNT)
    raise ValueError("Granularity field must be MONTHLY OR DAILY.")


def save_forecasts_by_service(data, logger, granularity):
    # data is ALREADY filtered to 'service_name' & 'account_name'.
    if granularity == Granularity.MONTHLY:
        return forecast_monthly_spend(data, logger, ForecastType.SERVICE)
    elif granularity == Granularity.DAILY:
        return forecast_daily_spend(data, logger, ForecastType.SERVICE)
    raise ValueError("Granularity field must be MONTHLY OR DAILY.")


def save_forecasts_by_bucode(data, logger, granularity):
    # data is ALREADY filtered to 'bu_code'.
    if granularity == Granularity.MONTHLY:
        return forecast_monthly_spend(data, logger, ForecastType.BUCODE)
    elif granularity == Granularity.DAILY:
        return forecast_daily_spend(data, logger, ForecastType.BUCODE)
    raise ValueError("Granularity field must be MONTHLY OR DAILY.")


def save_forecasts_by_segment(data, logger, granularity):
    # data is ALREADY filtered.
    if granularity == Granularity.MONTHLY:
        return forecast_monthly_spend(data, logger, ForecastType.SEGMENT)
    elif granularity == Granularity.DAILY:
        return forecast_daily_spend(data, logger, ForecastType.SEGMENT)
    raise ValueError("Granularity field must be MONTHLY OR DAILY.")