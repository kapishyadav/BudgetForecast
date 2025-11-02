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


def forecast_monthly_spend(data):
    monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})

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


def get_accounts_dict(data):
    unique_accounts = list(data['accountName'].unique())
    logger.info("Unique accounts: %s", unique_accounts)

    df_accounts_dict = {}  # dictionary to store 3 DataFrames

    for acc in unique_accounts:
        df_acc = data[data["accountName"] == acc].copy()
        df_accounts_dict[acc] = df_acc
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
    forecast, fig = forecast_monthly_spend(data)

    # --- Compute metrics ---
    # Merge to align actuals (y) with predicted (yhat)
    if 'y' in data.columns:
        merged = data.merge(forecast[['ds', 'yhat']], on='ds', how='inner')
        y_true = merged['y'].values
        y_pred = merged['yhat'].values

        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        metrics = {
            "RMSE": round(rmse, 3),
            "MAE": round(mae, 3),
            "MSE": round(mse, 3)
        }
    else:
        logger.warning("No 'y' column found in data — cannot compute metrics.")
        metrics = {}


    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "monthly_total")
    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "csv")
    html_dir = os.path.join(output_dir, "html")
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    # store the forecasts as plotly html files
    html_path = os.path.join(html_dir, "monthly_forecast.html")
    fig.write_html(html_path)
    # save forecast CSV
    csv_path = os.path.join(csv_dir, "monthly_forecast.csv")
    forecast_renamed = forecast.rename(columns={
        'ds': 'date'
    })
    logger.info("Forecasts renamed column names:", forecast_renamed.columns)
    forecast_formatted = forecast_renamed[['date', 'yhat', 'yhat_lower', 'yhat_upper']]
    forecast_formatted.to_csv(csv_path, index=False)
    logger.info("Forecasts formatted column names:", forecast_formatted.columns)
    logger.info("Successfully saved forecasts by monthly total!")
    return forecast_formatted, metrics


def save_forecast_by_accounts(df_accounts_dict, file, logger):
    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "account_level")
    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "csv")

    html_dir = os.path.join(output_dir, "html")

    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    for account, data in df_accounts_dict.items():
        # Aggregate monthly spend
        monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
        # skip if less than 2 non-NaN rows
        if monthly_spend.shape[0] < 2:
            logger.warning(f"Skipping {account}: not enough data points")
            continue

        forecasts, fig = forecast_monthly_spend(data)

        # store the forecasts as plotly html files
        html_path = os.path.join(html_dir, f"{account}_forecast.html")
        fig.write_html(html_path)
        # save forecast CSV
        forecast_renamed = forecasts.rename(columns={
            'ds': 'date'
        })
        print("Forecasts renamed column names:", forecast_renamed.columns)
        forecast_formatted = forecast_renamed[['date', 'yhat', 'yhat_lower', 'yhat_upper']]
        csv_path = os.path.join(csv_dir, f"{account}_forecast.csv")
        forecast_formatted.to_csv(csv_path, index=False)

    logger.info("Successfully saved forecasts by account!")


def save_forecasts_by_service(data, file, logger):
    file = os.path.splitext(os.path.basename(file))[0]
    # Make sure output directory exists
    output_dir = os.path.join("forecasts", file, "service_level")
    os.makedirs(output_dir, exist_ok=True)
    df_accounts_dict = get_accounts_dict(data)
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