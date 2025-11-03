import pandas as pd
from prophet.plot import add_changepoints_to_plot
from prophet import Prophet
# import matplotlib.pyplot as plt
from prophet.plot import plot_plotly, plot_components_plotly
import argparse
import os
import warnings
import numpy as np

from sklearn.metrics import mean_squared_error, mean_absolute_error

warnings.filterwarnings("ignore")

# from utils.setup_logging import setup_logging
# # Initialize logger
# logger = setup_logging()


import re


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>| ]+', "_", name)


def forecast_monthly_spend(data, logger):
    data['month'] = pd.to_datetime(data['month'], errors='coerce')
    monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})

    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

    forecast_full = m.predict(future)

    #Evaluation metrics
    # --- Merge to compare only historical months ---
    forecast_full['ds'] = pd.to_datetime(forecast_full['ds'], errors='coerce')
    forecast_eval = forecast_full[['ds', 'yhat']].merge(prophet_df, on='ds', how='inner')
    y_true = forecast_eval['y'].values
    y_pred = forecast_eval['yhat'].values

    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    metrics = {
        "RMSE": round(rmse, 2),
        "MAE": round(mae, 2),
        "MSE": round(mse, 2),
        "MAPE (%)": round(mape, 2)
    }

    if logger:
        logger.info(f" Computed metrics for monthly aggregate: {metrics}")

    # --- Step 5: Trim forecast to required fields only ---
    forecast = forecast_full[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    return forecast, metrics


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

    forecast, metrics = forecast_monthly_spend(data, logger)
    logger.info(f"DEBUG data columns : {list(data.columns)}")


    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "monthly_total")
    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "csv")

    os.makedirs(csv_dir, exist_ok=True)

    csv_path = os.path.join(csv_dir, "monthly_forecast.csv")

    logger.info("Forecasts formatted column names:", forecast.columns)
    logger.info("Successfully saved forecasts by monthly total!")
    return forecast, metrics


def save_forecast_by_accounts(data, file, logger, account_name):
    accounts_dict = get_accounts_dict(data, logger, account_name)
    account_data = accounts_dict[account_name]

    forecast, metrics = forecast_monthly_spend(account_data, logger)


    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "account_level")
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Successfully saved forecasts by account!")
    return forecast, metrics


def save_forecasts_by_service(data, file, logger):
    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "service_level")
    os.makedirs(output_dir, exist_ok=True)
    df_accounts_dict = get_accounts_dict(data, logger)
    # pivot table
    monthly_service_spend = data.pivot_table(
        index=["accountName", "month"],
        columns="serviceName",
        values="spend",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    # iterate over accounts and services
    for account, df_acc in monthly_service_spend.groupby("accountName"):
        account_dir = os.path.join(output_dir, sanitize_filename(account))
        os.makedirs(account_dir, exist_ok=True)

        csv_dir = os.path.join(account_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)
        html_dir = os.path.join(account_dir, "html")
        os.makedirs(html_dir, exist_ok=True)

        for service in [c for c in df_acc.columns if c not in ["accountName", "month"]]:
            df_service = df_acc[["month", service]].rename(columns={service: "spend"})

            # skip if less than 2 non-NaN rows
            if df_service["spend"].dropna().shape[0] < 2:
                logger.warning(f"Skipping {account} - {service}: not enough data points")
                continue

            # skip services with no spend
            if df_service["spend"].sum() == 0:
                continue
            try:
                # run forecast
                forecast, fig = forecast_service_spend(df_service)

                # save forecast CSV
                csv_path = os.path.join(csv_dir, f"{sanitize_filename(service)}_forecast.csv")
                # Ensure directories exist
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                if len(csv_path) > 210:
                    csv_path = csv_path[-200:] + ".csv"
                forecast_renamed = forecast.rename(columns={
                    'ds': 'date'
                })
                forecast_formatted = forecast_renamed[['date', 'yhat', 'yhat_lower', 'yhat_upper']]
                forecast_formatted.to_csv(csv_path, index=False)

                # save forecast plot
                html_path = os.path.join(html_dir, f"{sanitize_filename(service)}_forecast.html")
                os.makedirs(os.path.dirname(html_path), exist_ok=True)
                if len(html_path) > 210:
                    html_path = html_path[-200:] + ".csv"
                fig.write_html(html_path)

                logger.info(f"Saved forecast for {account} - {service}")
            except FileNotFoundError as fnf_error:
                logger.warning(f"Skipping {account} - {service} due to file path error: {fnf_error}")
            except Exception as e:
                logger.error(f"Unexpected error while saving forecast for {account} - {service}: {e}")


# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

# def main(file):
#
#     try:
#         data = pd.read_csv(file)
#         logger.info(f"Dataset loaded successfully. Shape: {data.shape}")
#     except FileNotFoundError:
#         logger.error("ERROR: Dataset file not found. Please ensure file: " + file + " exists in the parent directory.")
#         raise
#     except Exception as e:
#         logger.error(f"ERROR: Failed to load dataset: {str(e)}")
#         raise
#
#     column_names = data.columns
#
#     if 'month' not in data.columns:
#         data = data.rename(columns={'year_month': 'month'})
#     if 'accountName' not in data.columns:
#         data = data.rename(columns={'vendor_account_name': 'accountname'})
#     if 'accountId' not in data.columns:
#         data = data.rename(columns={'vendor_account_identifier': 'accountId'})
#     if 'accountName' not in data.columns:
#         data = data.rename(columns={'vendor_account_name': 'accountname'})
#     if 'spend' not in column_names and 'public_on_demand_cost' in column_names:
#         data = data.rename(columns={'public_on_demand_cost': 'spend'})
#
#     logger.info("Forecasting total spending...")
#     save_monthly_aggregate_forecasts(data, file)
#
#     logger.info("Forecasting by accounts... ")
#     accounts_dict = get_accounts_dict(data)
#     save_forecast_by_accounts(accounts_dict, file)
#
#     logger.info("Saved  by service name...")
#     save_forecasts_by_service(data, file)
#
#
# # =============================================================================
# # COMMAND LINE INTERFACE
# # =============================================================================
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(
#         description="Budget Forecasting Model - Train and evaluate prophet model",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Examples:
#   # Train CatBoost with Bayesian optimization
#   python prophet_model.py --file Forecast_Data-2022-205july.csv
#
#         """
#     )
#
#     parser.add_argument(
#         '--file',
#         type=str,
#         # choices=['Forecast_Data-2022-205july.csv', 'actual_detail_2025-08-14.csv'],
#         default='false',
#         help='Which file to use for predictions'
#     )
#
#     args = parser.parse_args()
#     # # Initialize logger
#     # logger = setup_logging()
#
#     # Run the main function
#     main(file=args.file)