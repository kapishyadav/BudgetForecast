from typing import Dict

# Centralized mapping for Pandas dataframe preprocessing
DATASET_COLUMN_MAPPINGS = {
    "accountName": ["accountName", "vendor_name", "vendor_account_name", "account"],
    "spend": ["spend", "cost", "public_on_demand", "public_on_demand_cost", "total_amortized_cost"],
    "serviceName": ["serviceName", "enhanced_service_name", "service"],
    "date": ["date", "month", "year_month", "Date", "Month"], # Consolidated date mappings
    "buCode": ["buCode", "business_unit", "bu_code"],
    "segment": ["segment", "segment_name"]
}

# Default Hyperparameters for Prophet Models
DEFAULT_CHANGEPOINT_PRIOR_SCALE = 0.05
DEFAULT_SEASONALITY_MODE = "additive"
DEFAULT_INCLUDE_HOLIDAYS = False

# Default application states
DEFAULT_FORECAST_TYPE = "overall_aggregate"
DEFAULT_GRANULARITY = "monthly"
