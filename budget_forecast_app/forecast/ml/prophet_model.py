"""
prophet_model.py
----------------
Prophet-based forecasting module.
Loads CSV, trains Prophet model, and returns forecast + Plotly figure.
"""

from .legacy_prophet_model import *
from .enums import ForecastType, Granularity
from .utils.setup_logging import setup_logging
from typing import List, Dict

def run_prophet_forecast(
        csv_path: str,
        forecast_type: ForecastType = ForecastType.OVERALL_AGGREGATE,
        granularity: Granularity = Granularity.MONTHLY,
        logger=None,
        account_name = None,
        service_name = None,
        bu_code = None,
        segment_name = None):
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
        COLUMN_MAPPINGS = {
            "accountName": ["accountName", "vendor_name", "vendor_account_name"],
            "spend": ["spend", "cost", "public_on_demand", "public_on_demand_cost", "total_amortized_cost"],
            "serviceName": ["serviceName", "enhanced_service_name"],
            "month": ["month", "year_month", "Month(Year)"],
            "date": ["Date"]
        }

        mapped_columns = get_mapped_columns(data.columns.tolist(), COLUMN_MAPPINGS)
        logger.info(f"DEBUG mapped columns after get_mapped_columns method in prophet_model.py - {mapped_columns}")
        rename_dict = {actual_col: canonical_col for canonical_col, actual_col in mapped_columns.items()}
        logger.info(f"DEBUG Renamed Dict Column Names: {rename_dict}")
        # Apply the mapping to the DataFrame
        data = data.rename(columns=rename_dict)
        logger.info(f"DEBUG Data Column Names after renaming post remap: {data.columns}")


    except FileNotFoundError:
        logger.error("Dataset file not found.")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Validate columns
    if granularity == Granularity.MONTHLY:
        if "month" not in data.columns or "spend" not in data.columns:
            raise ValueError("CSV must contain 'month' and 'spend' columns for MONTHLY granularity.")
    elif granularity == Granularity.DAILY:
        if "date" not in data.columns or "spend" not in data.columns:
            raise ValueError("CSV must contain 'date' and 'spend' columns for DAILY granularity.")

    if forecast_type == ForecastType.OVERALL_AGGREGATE:
        forecast_df, historical_df = save_overall_aggregate_forecasts(data, csv_path, logger, granularity)
        logger.info(f"DEBUG save_monthly_aggregate_forecasts complete!")
    elif forecast_type == ForecastType.ACCOUNT:
        logger.info(f"DEBUG starting save_forecast_by_accounts now!")
        forecast_df, historical_df = save_forecast_by_accounts(data, csv_path, logger, account_name, granularity)
        logger.info(f"DEBUG save_forecast_by_accounts complete!")
    elif forecast_type == ForecastType.SERVICE:
        forecast_df, historical_df = save_forecasts_by_service(data, csv_path, logger, account_name, service_name, granularity)
    elif forecast_type == ForecastType.BUCODE:
        logger.info(f"Value of bu Code in prophet_model.py : {bu_code}, type: {type(bu_code)}")
        forecast_df, historical_df = save_forecasts_by_bucode(data, csv_path, logger, bu_code, granularity)
    elif forecast_type == ForecastType.SEGMENT:
        logger.info(f"Value of segment in prophet_model.py : {segment_name}, type: {type(segment_name)}")
        forecast_df, historical_df = save_forecasts_by_segment(data, csv_path, logger, account_name, service_name,
                                                               segment_name, granularity)
    else:
        raise ValueError(f"Invalid forecast type: {forecast_type}")


    return forecast_df, historical_df


def get_mapped_columns(available_columns, COLUMN_MAPPINGS: Dict[str, str]) -> Dict[str, str]:
    """
    Maps available column names to standardized canonical names based on COLUMN_MAPPINGS.
    """
    columns_dict = {}

    # 2. Iterate dynamically through the mappings
    for canonical_name, possible_names in COLUMN_MAPPINGS.items():
        # 3. Find the first matching column name
        match = next((name for name in possible_names if name in available_columns), None)

        if match:
            columns_dict[canonical_name] = match

    return columns_dict

