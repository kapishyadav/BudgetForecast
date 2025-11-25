import pandas as pd
from prophet.plot import add_changepoints_to_plot
from prophet import Prophet
# import matplotlib.pyplot as plt
from prophet.plot import plot_plotly, plot_components_plotly
import argparse
import os
import warnings
import numpy as np
import hashlib
from .enums import ForecastType

from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

import re


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>| ]+', "_", name)


def forecast_account_spend(data, logger):
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    monthly_account_spend = data.groupby(['month', 'accountName'], as_index=False)['spend'].sum()

    prophet_df = monthly_account_spend.rename(columns={"month": "ds", "spend": "y"})

    # Get the last date from your historical data
    last_date = prophet_df['ds'].max()

    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

    forecast_full = m.predict(future)

    # Filter forecast_full to include only future predictions
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    rows, columns = forecast_future.shape

    if logger:
        logger.info(f" no of months rows forecast_future: {rows}")

    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecast


def forecast_monthly_spend(data, logger, forecast_type):
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    if forecast_type == ForecastType.MONTHLY:
        monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    elif forecast_type == ForecastType.ACCOUNT:
        monthly_spend = data.groupby(['month', 'accountName'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.SERVICE:
        monthly_spend = data.groupby(['month', 'accountName', 'serviceName'], as_index=False)['spend'].sum()
    else:
        raise ValueError(f"Unsupported forecast type: {forecast_type}")

    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})

    # Get the last date from your historical data
    last_date = prophet_df['ds'].max()

    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

    forecast_full = m.predict(future)

    # Filter forecast_full to include only future predictions
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    # Optional: Reset index for clean output
    # forecast_future = forecast_future.reset_index(drop=True)

    rows, columns = forecast_future.shape

    if logger:
        logger.info(f" no of months rows forecast_future: {rows}")

    # Evaluation metrics
    # --- Merge to compare only historical months ---
    # forecast_full['ds'] = pd.to_datetime(forecast_full['ds'], errors='coerce')
    # forecast_eval = forecast_full[['ds', 'yhat']].merge(prophet_df, on='ds', how='inner')
    # y_true = forecast_eval['y'].values
    # y_pred = forecast_eval['yhat'].values

    # --- Standard deviation and variance ---
    # y_std = np.std(y_true, ddof=1)        # sample standard deviation
    # y_var = np.var(y_true, ddof=1)
    # y_pred_std = np.std(y_pred, ddof=1)
    # y_pred_var = np.var(y_pred, ddof=1)

    # mse = mean_squared_error(y_true, y_pred)
    # rmse = np.sqrt(mse)
    # mae = mean_absolute_error(y_true, y_pred)
    # mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    # metrics = {
    #     "RMSE": round(rmse, 2),
    #     "MAE": round(mae, 2),
    #     "MSE": round(mse, 2),
    #     "MAPE (%)": round(mape, 2),
    #     "Y Std Dev": round(y_std, 2),
    #     "Y Variance": round(y_var, 2),
    #     "Y_Pred Std Dev": round(y_pred_std, 2),
    #     "Y_Pred Variance": round(y_pred_var, 2),
    # }

    # if logger:
    #     logger.info(f" Computed metrics for monthly aggregate: {metrics}")

    # --- Step 5: Trim forecast to required fields only ---
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecast


def get_accounts_dict(data, logger, account_name):
    """
    Filters the dataset for the given account name and returns a dictionary
    mapping that single account name to its DataFrame.

    Args:
        data (pd.DataFrame): Input dataframe containing 'accountName' column.
        logger (logging.Logger): Logger instance for debug/info messages.
        account_name (str): The specific account name to filter for.

    Returns:
        dict: { df_accounts_dict: filtered dataframe by account}
    """
    unique_accounts = list(data['accountName'].unique())
    if account_name not in unique_accounts:
        raise ValueError(f"Account name not found!: {account_name}")
    logger.info("Unique accounts: %s", unique_accounts)

    # Filter only that account
    df_account = data[data["accountName"] == account_name].copy()
    df_accounts_dict = {account_name: df_account}

    return df_accounts_dict


def forecast_service_spend(data):
    prophet_df = data.rename(columns={"month": "ds", "spend": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

    forecast = m.predict(future)
    forecast[['ds', 'yhat', 'yhat_lower',
              'yhat_upper', 'trend',
              'trend_lower', 'trend_upper']].tail()
    fig = plot_plotly(m, forecast)
    return forecast, fig


def save_monthly_aggregate_forecasts(data, file, logger):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger

    Returns: (forecast_df, metrics, figure_dict)
    forecasts_formatted: forecast ds with only yhat, yhat_upper, yhat_lower
    metrics: RMSE, MAE, MSE
    """

    file = os.path.splitext(os.path.basename(file))[0]

    forecast = forecast_monthly_spend(data, logger, ForecastType.MONTHLY)
    logger.info(f"DEBUG data columns : {list(data.columns)}")

    # Shorten file name to avoid path length issues
    short_name = hashlib.md5(file.encode()).hexdigest()[:8]

    # Make sure output directory exists
    output_dir = os.path.join("forecasts", short_name, "monthly_total")
    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "csv")

    os.makedirs(csv_dir, exist_ok=True)

    csv_path = os.path.join(csv_dir, "monthly_forecast.csv")

    # Save forecast
    forecast.to_csv(csv_path, index=False)

    logger.info("Forecasts formatted column names:", forecast.columns)
    logger.info("Successfully saved forecasts by monthly total!")
    return forecast


def save_forecast_by_accounts(data, file, logger, account_name):
    accounts_dict = get_accounts_dict(data, logger, account_name)
    account_data = accounts_dict[account_name]

    # forecast, metrics = forecast_monthly_spend(account_data, logger)
    forecast = forecast_monthly_spend(account_data, logger, ForecastType.ACCOUNT)

    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "account_level")
    os.makedirs(output_dir, exist_ok=True)

    rows, columns = forecast.shape

    if logger:
        logger.info(f" no of months in forecast account rows: {rows}")

    logger.info("Successfully saved forecasts by account!")
    # return forecast, metrics
    return forecast


def save_forecasts_by_service(data, file, logger, account_name, service_name):
    accounts_dict = get_accounts_dict(data, logger, account_name)
    account_data = accounts_dict[account_name]

    # check if service_name exists in this account
    if service_name not in account_data["serviceName"].unique():
        raise ValueError(f"Service name '{service_name}' not found under account '{account_name}'")

    # Filter for only that service
    service_data = account_data[account_data["serviceName"] == service_name].copy()
    logger.info(f"Filtered data for only account '{account_name}' : {len(account_data)} rows")
    logger.info(f"Filtered data for account '{account_name}' and service '{service_name}': {len(service_data)} rows")

    forecast = forecast_monthly_spend(service_data, logger, ForecastType.SERVICE)
    logger.info(f"DEBUG service_data columns : {list(service_data.columns)}")

    return forecast

