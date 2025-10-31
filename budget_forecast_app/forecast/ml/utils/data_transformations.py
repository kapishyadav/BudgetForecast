import os

from budget_forecast_app.forecast.ml.legacy_prophet_model import forecast_monthly_spend, logger


def save_monthly_aggregate_forecasts(data, file):
    forecast, fig = forecast_monthly_spend(data)
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
    forecast.to_csv(csv_path, index=False)
    logger.info("Successfully saved forecasts by monthly total!")

def save_forecast_by_accounts(df_accounts_dict, file):
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
        csv_path = os.path.join(csv_dir, f"{account}_forecast.csv")
        forecasts.to_csv(csv_path, index=False)
    logger.info("Successfully saved forecasts by account!")
