from abc import ABC, abstractmethod
import pandas as pd
from .enums import Granularity


class BaseForecaster(ABC):
    def __init__(self, granularity: Granularity, logger=None, hyperparameters=None, **kwargs):
        self.granularity = granularity
        self.logger = logger
        self.hyperparameters = hyperparameters or {}
        self.kwargs = kwargs

        gran_str = granularity.value if hasattr(granularity, 'value') else str(granularity).lower()
        self.is_daily = gran_str == 'daily'
        self.freq = 'D' if self.is_daily else 'MS'
        self.periods = kwargs.get('periods', 30 if self.is_daily else 12)

    def _standardize_and_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handles date extraction and period aggregation (SRP)"""
        df = df.copy()
        date_col = 'date' if self.is_daily else 'month'

        if df.index.name in ['date', 'month', 'Month']:
            df = df.reset_index()

        # Rename columns to standard 'date'
        rename_map = {col: 'date' for col in ['month', 'Month', date_col] if col in df.columns}
        if rename_map:
            df = df.rename(columns=rename_map)

        if 'date' not in df.columns:
            raise KeyError(f"Expected a date column, but found: {df.columns.tolist()}")

        df['date'] = pd.to_datetime(df['date'])
        df['spend'] = pd.to_numeric(df['spend'], errors='coerce').fillna(0)

        # Aggregate
        df = df.set_index('date').sort_index()
        resample_rule = 'D' if self.is_daily else 'MS'
        df = df.resample(resample_rule)['spend'].sum().reset_index()
        return df.sort_values('date').reset_index(drop=True)

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