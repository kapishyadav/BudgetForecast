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
from .enums import ForecastType, Granularity

from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

def forecast_monthly_spend(data, logger, forecast_type):
    """_summary_

    Args:
        data (_type_): input historical data containing 'month' and 'spend' columns
        logger (_type_): logger instance for logging
        forecast_type (_type_): forecast type from ForecastType enum : OVERALL_AGGREGATE, ACCOUNT, SERVICE, BUCODE or SEGMENT

    Returns:
        forecast: forecast dataframe with future predictions
        history: historical dataframe used for training the model and plotting history for Chartly JS
    """
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    if forecast_type == ForecastType.OVERALL_AGGREGATE:
        monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f" DEBUG in forecast_monthly_spend's ACCOUNT forecast, grouping data by 'month' and 'accountName'")
        monthly_spend = data.groupby(['month', 'accountName'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.SERVICE:
        monthly_spend = data.groupby(['month', 'accountName', 'serviceName'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.BUCODE:
        monthly_spend = data.groupby(['month','buCode'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.SEGMENT:
        monthly_spend = data.groupby(['month', 'accountName', 'serviceName', 'segment'], as_index=False)['spend'].sum()
    else:
        raise ValueError(f"Unsupported forecast type: {forecast_type}")

    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})

    # Get the last date from your historical data
    last_date = prophet_df['ds'].max()

    m = Prophet()
    logger.info(f" DEBUG Fitting Prophet model in forecast_monthly_spend!")
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='ME')

    forecast_full = m.predict(future)

    # Filter forecast_full to include only future predictions
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    rows, columns = forecast_future.shape
    logger.info(f"DEBUG forecast_future computed successfully. Shape: {forecast_future.shape}")

    if logger:
        logger.info(f" no of months rows forecast_future: {rows}")

    # --- Step 5: Trim forecast to required fields only ---
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecast, prophet_df

def forecast_daily_spend(data, logger, forecast_type):
    """_summary_

    Args:
        data (_type_): input historical data containing 'date' and 'spend' columns
        logger (_type_): logger instance for logging
        forecast_type (_type_): forecast type from ForecastType enum : OVERALL_AGGREGATE, ACCOUNT, SERVICE, BUCODE or SEGMENT

    Returns:
        forecast: forecast dataframe with future predictions
        history: historical dataframe used for training the model and plotting history for Chartly JS
    """
    data['date'] = pd.to_datetime(data['date'], errors='coerce')
    if forecast_type == ForecastType.OVERALL_AGGREGATE:
        daily_spend = data.groupby("date", as_index=False)["spend"].sum()
    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f" DEBUG in forecast_daily_spend's ACCOUNT forecast, grouping data by 'date' and 'accountName'")
        daily_spend = data.groupby(['date', 'accountName'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.SERVICE:
        daily_spend = data.groupby(['date', 'accountName', 'serviceName'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.BUCODE:
        daily_spend = data.groupby(['date','buCode'], as_index=False)['spend'].sum()
    elif forecast_type == ForecastType.SEGMENT:
        daily_spend = data.groupby(['date', 'accountName', 'serviceName', 'segment'], as_index=False)['spend'].sum()
    else:
        raise ValueError(f"Unsupported forecast type: {forecast_type}")

    prophet_df = daily_spend.rename(columns={"date": "ds", "spend": "y"})
    # 1. Keep ONLY the columns Prophet needs (drops accountName, serviceName, etc.)
    prophet_df = prophet_df[['ds', 'y']]
    # 2. Drop any rows where the date couldn't be parsed (NaT)
    prophet_df = prophet_df.dropna(subset=['ds'])
    # 3. Force unique dates by aggregating any accidental same-day duplicates
    prophet_df = prophet_df.groupby('ds', as_index=False)['y'].sum()
    logger.info(f" DEBUG Force unique dates by aggregating any accidental same-day duplicates in Prophet model!")

    # Get the last date from your historical data
    last_date = prophet_df['ds'].max()

    m = Prophet()
    logger.info(f" DEBUG Fitting Prophet model in forecast_daily_spend!")
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=90,
                                     freq='D')

    forecast_full = m.predict(future)

    # Filter forecast_full to include only future predictions
    forecast_future = forecast_full[forecast_full['ds'] > last_date]

    rows, columns = forecast_future.shape
    logger.info(f"DEBUG forecast_future computed successfully. Shape: {forecast_future.shape}")

    if logger:
        logger.info(f" no of months rows forecast_future: {rows}")

    # --- Step 5: Trim forecast to required fields only ---
    forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecast, prophet_df


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
    logger.info(f"DEBUG unique_accounts in legacy_prophet_model.py -> get_accounts_dict() :  {unique_accounts}")

    # Filter only that account
    df_account = data[data["accountName"] == account_name].copy()
    df_accounts_dict = {account_name: df_account}
    logger.info(f"DEBUG df_accounts_dict accounts:  {df_accounts_dict}")

    return df_accounts_dict


def save_overall_aggregate_forecasts(data, file, logger, granularity):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger

    Returns: (forecast_df, historical_df)
    forecasts formatted with: forecast ds with only yhat, yhat_upper, yhat_lower
    """

    file = os.path.splitext(os.path.basename(file))[0]

    if granularity == Granularity.MONTHLY:
        logger.info(f"DEBUG Running overall aggregate MONTHLY")
        forecast, history = forecast_monthly_spend(data, logger, ForecastType.OVERALL_AGGREGATE)
    elif granularity == Granularity.DAILY:
        logger.info(f"DEBUG Running overall aggregate DAILY")
        forecast, history = forecast_daily_spend(data, logger, ForecastType.OVERALL_AGGREGATE)
    else:
        raise ValueError(f"Granularity field must be MONTHLY OR DAILY. Currently: {granularity} with type {type(granularity)}")
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

    logger.info(f"Forecasts formatted column names: {forecast.columns}")
    logger.info(f"History formatted column names: {history.columns}")
    logger.info("Successfully saved forecasts by monthly total!")
    return forecast, history


def save_forecast_by_accounts(data, file, logger, account_name, granularity):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger
    account_name -> account name to filter

    Returns: (forecast_df, historical_df)
    forecasts formatted with: forecast ds with only yhat, yhat_upper, yhat_lower
    """
    logger.info(f" DEBUG calling get_accounts_dict in legacy_prophet_model!")
    accounts_dict = get_accounts_dict(data, logger, account_name)
    account_data = accounts_dict[account_name]

    # forecast, metrics = forecast_monthly_spend(account_data, logger)
    logger.info(f" DEBUG account_data field in legacy_prophet_model : {account_data}")

    if granularity == Granularity.MONTHLY:
        logger.info(f"DEBUG Running account forecasts MONTHLY")
        forecast, history = forecast_monthly_spend(account_data, logger, ForecastType.ACCOUNT)
    elif granularity == Granularity.DAILY:
        logger.info(f"DEBUG Running account forecasts DAILY")
        forecast, history = forecast_daily_spend(account_data, logger, ForecastType.ACCOUNT)
    else:
        raise ValueError("Granularity field must be MONTHLY OR DAILY.")

    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "account_level")
    os.makedirs(output_dir, exist_ok=True)

    rows, columns = forecast.shape

    if logger:
        logger.info(f" no of months in forecast account rows: {rows}")

    logger.info("Successfully saved forecasts by account!")
    # return forecast, metrics
    return forecast, history


def save_forecasts_by_service(data, file, logger, account_name, service_name, granularity):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger
    service_name -> service name to filter

    Returns: (forecast_df, historical_df)
    forecasts formatted with: forecast ds with only yhat, yhat_upper, yhat_lower
    """
    accounts_dict = get_accounts_dict(data, logger, account_name)
    account_data = accounts_dict[account_name]

    # check if service_name exists in this account
    if service_name not in account_data["serviceName"].unique():
        raise ValueError(f"Service name '{service_name}' not found under account '{account_name}'")

    # Filter for only that service
    service_data = account_data[account_data["serviceName"] == service_name].copy()
    logger.info(f"Filtered data for only account '{account_name}' : {len(account_data)} rows")
    logger.info(f"Filtered data for account '{account_name}' and service '{service_name}': {len(service_data)} rows")

    if granularity == Granularity.MONTHLY:
        logger.info(f"DEBUG Running service forecasts MONTHLY")
        forecast, history = forecast_monthly_spend(service_data, logger, ForecastType.SERVICE)
    elif granularity == Granularity.DAILY:
        logger.info(f"DEBUG Running service forecasts DAILY")
        forecast, history = forecast_daily_spend(service_data, logger, ForecastType.SERVICE)
    else:
        raise ValueError("Granularity field must be MONTHLY OR DAILY.")

    logger.info(f"DEBUG service_data columns : {list(service_data.columns)}")

    return forecast, history

def save_forecasts_by_bucode(data, file, logger, bu_code, granularity):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger
    bu_code -> bu_code to filter

    Returns: (forecast_df, historical_df)
    forecasts formatted with: forecast ds with only yhat, yhat_upper, yhat_lower
    """
    logger.info(f"DEBUG In save_forecasts_by_bucode function with bu_code type:", type(bu_code))
    # Filter for only that service
    bu_data = data[data["buCode"] == int(bu_code)].copy()
    logger.info(f"Filtered data for only bu code '{bu_code}' : {len(bu_data)} rows")

    if granularity == Granularity.MONTHLY:
        logger.info(f"DEBUG Running bu code forecasts MONTHLY")
        forecast, history = forecast_monthly_spend(bu_data, logger, ForecastType.BUCODE)
    elif granularity == Granularity.DAILY:
        logger.info(f"DEBUG Running bu code forecasts DAILY")
        forecast, history = forecast_daily_spend(bu_data, logger, ForecastType.BUCODE)
    else:
        raise ValueError("Granularity field must be MONTHLY OR DAILY.")

    logger.info(f"DEBUG bu_data columns : {list(bu_data.columns)}")

    return forecast, history

def save_forecasts_by_segment(data, file, logger, account_name, service_name, segment_name, granularity):
    """
    Arguments:
    csv file -> data
    csv path -> file
    logger setup -> logger
    account_name -> account name to filter
    service_name -> service name to filter
    segment_name -> segment name to filter

    Returns: (forecast_df, historical_df)
    forecasts formatted with: forecast ds with only yhat, yhat_upper, yhat_lower
    """
    logger.info(f"DEBUG In save_forecasts_by_segment function with segment type: {type(segment_name)},"
                f" segment name: {segment_name}")
    # Filter for only that service
    segment_data = data[data["segment"] == segment_name].copy()

    accounts_dict = get_accounts_dict(segment_data, logger, account_name)
    account_data = accounts_dict[account_name]

    # check if service_name exists in this account
    if service_name not in account_data["serviceName"].unique():
        raise ValueError(f"Service name '{service_name}' not found under account '{account_name}'")

    # Filter for only that service
    service_data = account_data[account_data["serviceName"] == service_name].copy()
    logger.info(f"Filtered data for only account '{account_name}' : {len(account_data)} rows")
    logger.info(f"Filtered data for account '{account_name}' and service '{service_name}': {len(service_data)} rows")
    logger.info(f"Filtered data for segment '{segment_name}' , account '{account_name}' "
                f"and service '{service_name}': {len(service_data)} rows")

    if granularity == Granularity.MONTHLY:
        logger.info(f"DEBUG Running segment forecasts MONTHLY")
        forecast, history = forecast_monthly_spend(service_data, logger, ForecastType.SEGMENT)
    elif granularity == Granularity.DAILY:
        logger.info(f"DEBUG Running segment forecasts DAILY")
        forecast, history = forecast_daily_spend(service_data, logger, ForecastType.SEGMENT)
    else:
        raise ValueError("Granularity field must be MONTHLY OR DAILY.")

    logger.info(f"DEBUG segment columns : {list(service_data.columns)}")

    return forecast, history

