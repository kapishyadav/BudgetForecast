import pandas as pd
from prophet.plot import add_changepoints_to_plot
from prophet import Prophet
# import matplotlib.pyplot as plt
from prophet.plot import plot_plotly, plot_components_plotly
import argparse
import os
import math

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import logging
logger = logging.getLogger(__name__)

def get_accounts_dict(data):
    unique_accounts = list(data['accountName'].unique())
    logger.info("Unique accounts: %s", unique_accounts)

    df_accounts_dict = {}  # dictionary to store 3 DataFrames

    for acc in unique_accounts:
        df_acc = data[data["accountName"] == acc].copy()
        df_accounts_dict[acc] = df_acc
    return df_accounts_dict

def forecast_monthly_spend(data):
    monthly_spend = data.groupby("month", as_index=False)["spend"].sum()
    prophet_df = monthly_spend.rename(columns={"month": "ds", "spend": "y"})

    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

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

    forecast[['ds', 'yhat', 'yhat_lower',
              'yhat_upper', 'trend',
              'trend_lower', 'trend_upper']].tail()
    fig = plot_plotly(m, forecast)
    return forecast, metrics, fig


def forecast_service_spend(data, logger):
    prophet_df = data.rename(columns={"month": "ds", "spend": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])

    m = Prophet()
    m.fit(prophet_df)

    future = m.make_future_dataframe(periods=12 * 2,
                                     freq='M')

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

    forecast[['ds', 'yhat', 'yhat_lower',
              'yhat_upper', 'trend',
              'trend_lower', 'trend_upper']].tail()
    fig = plot_plotly(m, forecast)
    return forecast, metrics, fig.to_dict()


def save_monthly_aggregate_forecasts(data, file, logger):
    forecast_monthly_agg, metrics_monthly_agg, fig_monthly_agg = forecast_monthly_spend(data)
    # Make sure output directory exists
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_dir = os.path.join("forecasts", base_name, "monthly_total")
    os.makedirs(output_dir, exist_ok=True)
    csv_dir = os.path.join(output_dir, "csv")
    html_dir = os.path.join(output_dir, "html")
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    # store the forecasts as plotly html files
    # html_path = os.path.join(html_dir, "monthly_forecast.html")
    # fig_monthly_agg.write_html(html_path)
    # save forecast CSV
    csv_path = os.path.join(csv_dir, "monthly_forecast.csv")
    forecast_monthly_agg.to_csv(csv_path, index=False)
    logger.info("Successfully saved forecasts by monthly total!")
    return forecast_monthly_agg, metrics_monthly_agg, fig_monthly_agg


def save_forecast_by_accounts(df_accounts_dict, file, logger):
    # Make sure output directory exists
    global forecasts_by_account, metrics_by_account, fig_by_account
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_dir = os.path.join("forecasts", base_name, "account_level")
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

        forecasts_by_account, metrics_by_account, fig_by_account = forecast_monthly_spend(data)

        # store the forecasts as plotly html files
        # html_path = os.path.join(html_dir, f"{account}_forecast.html")
        # fig_by_account.write_html(html_path)
        # save forecast CSV
        csv_path = os.path.join(csv_dir, f"{account}_forecast.csv")
        forecasts_by_account.to_csv(csv_path, index=False)
    logger.info("Successfully saved forecasts by account!")
    return forecasts_by_account, metrics_by_account, fig_by_account


def save_forecasts_by_service(data, file, logger):
    # Make sure output directory exists
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_dir = os.path.join("forecasts", base_name, "service_level")
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
        account_dir = os.path.join(output_dir, account)
        os.makedirs(account_dir, exist_ok=True)

        csv_dir = os.path.join(account_dir, "csv")
        html_dir = os.path.join(account_dir, "html")

        os.makedirs(csv_dir, exist_ok=True)
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

            # run forecast
            forecast_by_service, metrics_by_service, fig_by_service = forecast_service_spend(df_service, logger)

            # save forecast CSV
            csv_path = os.path.join(csv_dir, f"{service}_forecast.csv")
            forecast_by_service.to_csv(csv_path, index=False)

            # save forecast plot
            # html_path = os.path.join(html_dir, f"{service}_forecast.html")
            # fig_by_service.write_html(html_path)

            logger.info(f"Saved forecast for {account} - {service}")
            return forecast_by_service, metrics_by_service, fig_by_service


# # =============================================================================
# # MAIN EXECUTION FUNCTION
# # =============================================================================
#
# def main(file):
#     # Initialize logger
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
#     if 'month' not in data.columns or 'spend' not in data.columns:
#         logger.error("ERROR: Data does not contain month or spend column!")
#
#     logger.info("Forecasting total spending...")
#     forecast_monthly_agg, metrics_monthly_agg, fig_monthly_agg = save_monthly_aggregate_forecasts(data, file)
#
#     logger.info("Forecasting by accounts... ")
#     accounts_dict = get_accounts_dict(data)
#     forecasts_by_account, metrics_by_account, fig_by_account = save_forecast_by_accounts(accounts_dict, file)
#
#     logger.info("Saved  by service name...")
#     forecast_by_service, metrics_by_service, fig_by_service = save_forecasts_by_service(data, file)
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
#     # Initialize logger
#     logger = setup_logging()
#
#     # Run the main function
#     main(file=args.file)
