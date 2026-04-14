from abc import ABC, abstractmethod
import pandas as pd
from .enums import Granularity


class BaseForecaster(ABC):
    def __init__(self, granularity: Granularity, logger=None, hyperparameters=None, **kwargs):
        self.granularity = granularity
        self.logger = logger
        self.hyperparameters = hyperparameters or {}
        self.kwargs = kwargs

        gran_str = granularity.value if hasattr(granularity, 'value') else str(granularity)
        self.is_daily = gran_str.lower() == 'daily'
        self.freq = 'D' if self.is_daily else 'MS'
        self.periods = kwargs.get('periods', 90 if self.is_daily else 24)

    def _standardize_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles date extraction and period aggregation (SRP)"""
        df = df.copy()
        date_col = 'date' if self.is_daily else 'month'

        if df.index.name in ['date', 'month', 'Month']:
            df = df.reset_index()

        # Safely normalize the time column to 'date' without creating duplicates
        for col in ['date', 'month', 'Month', 'ds']:
            if col in df.columns and col != 'date':
                df = df.rename(columns={col: 'date'})
                break  # Only rename the first valid time column we find

        if 'date' not in df.columns:
            raise KeyError(f"Expected a date column, but found: {df.columns.tolist()}")

        df['date'] = pd.to_datetime(df['date'])
        df['spend'] = pd.to_numeric(df['spend'], errors='coerce').fillna(0)

        # Aggregate
        df = df.set_index('date').sort_index()
        resample_rule = 'D' if self.is_daily else 'MS'
        df = df.resample(resample_rule)['spend'].sum().reset_index()
        return df.sort_values('date').reset_index(drop=True)

    def _validate_and_filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """SRP: Preserved legacy validation and dynamic filtering logic."""
        if df is None or df.empty:
            raise ValueError("The provided dataset is empty and contains no historical spend data.")

        # 1. Dynamic Column Validation
        has_time_col = any(col in df.columns for col in ['date', 'month', 'Month'])
        if not has_time_col or 'spend' not in df.columns:
            raise ValueError(
                "DataFrame must contain a time column ('date', 'month', or 'Month') and a 'spend' column.")

        # 2. Dynamic Filtering using kwargs passed to the BaseForecaster
        data = df.copy()
        filter_mapping = {
            'account_name': 'account_name',
            'service_name': 'service_name',
            'bu_code': 'bu_code',
            'segment_name': 'segment'
        }

        for kwarg_key, df_column in filter_mapping.items():
            val = self.kwargs.get(kwarg_key)
            if val is not None:
                data = data[data[df_column] == val]

        # 3. Final Safety Check
        if data.empty:
            raise ValueError("The selected combination of filters resulted in an empty dataset. Cannot generate forecast.")

        return data

    def _calculate_base_metrics(self, forecast_df: pd.DataFrame, custom_metrics: dict) -> dict:
        """Standardizes the output dictionary calculation"""
        avg_multiplier = 30.44 if self.is_daily else 1

        base_metrics = {
            "total_forecasted_spend": float(forecast_df['forecast'].sum()),
            "average_monthly_spend": float(forecast_df['forecast'].mean() * avg_multiplier),
            "forecast_period": self.periods
        }

        # Merge model-specific metrics (RMSE, MAPE, etc.) with base metrics
        return {**custom_metrics, **base_metrics}

    @abstractmethod
    def run(self, df: pd.DataFrame):
        """The main orchestration method to be implemented by subclasses"""
        pass
