from abc import ABC, abstractmethod
import pandas as pd
import logging

from .prophet_model import run_prophet_forecast
from .enums import ForecastType


class ForecastStrategy(ABC):
    """Abstract base class defining the contract for all forecast strategies."""

    @abstractmethod
    def validate(self, **kwargs):
        """Validates that the required parameters exist for this specific strategy."""
        pass

    @abstractmethod
    def execute(self, df: pd.DataFrame, granularity, logger: logging.Logger, **kwargs):
        """Executes the specific ML pipeline for this strategy."""
        pass


class OverallAggregateStrategy(ForecastStrategy):
    def validate(self, **kwargs):
        pass  # No specific filters required for an overall aggregate

    def execute(self, df, granularity, logger, **kwargs):
        return run_prophet_forecast(df, granularity=granularity, logger=logger, **kwargs)


class AccountForecastStrategy(ForecastStrategy):
    def validate(self, **kwargs):
        if not kwargs.get('account_name'):
            raise ValueError("Account name must be provided for account-level forecast.")

    def execute(self, df, granularity, logger, **kwargs):
        return run_prophet_forecast(df, granularity=granularity, logger=logger, **kwargs)


class ServiceForecastStrategy(ForecastStrategy):
    def validate(self, **kwargs):
        if not kwargs.get('service_name'):
            raise ValueError("Service name must be provided for service-level forecast.")

    def execute(self, df, granularity, logger, **kwargs):
        return run_prophet_forecast(df, granularity=granularity, logger=logger, **kwargs)


class BuCodeForecastStrategy(ForecastStrategy):
    def validate(self, **kwargs):
        if kwargs.get('bu_code') is None:
            raise ValueError("BU Code must be provided for bu-code-level forecast.")

    def execute(self, df, granularity, logger, **kwargs):
        logger.info(f"Executing BU Code Strategy with BU: {kwargs.get('bu_code')}")
        return run_prophet_forecast(df, granularity=granularity, logger=logger, **kwargs)


class SegmentForecastStrategy(ForecastStrategy):
    def validate(self, **kwargs):
        if not kwargs.get('segment_name'):
            raise ValueError("Segment name must be provided for segment-level forecast.")

    def execute(self, df, granularity, logger, **kwargs):
        return run_prophet_forecast(df, granularity=granularity, logger=logger, **kwargs)


class ForecastStrategyFactory:
    """Dynamically routes a ForecastType to its corresponding Strategy implementation."""

    _strategies = {
        ForecastType.OVERALL_AGGREGATE: OverallAggregateStrategy(),
        ForecastType.ACCOUNT: AccountForecastStrategy(),
        ForecastType.SERVICE: ServiceForecastStrategy(),
        ForecastType.BUCODE: BuCodeForecastStrategy(),
        ForecastType.SEGMENT: SegmentForecastStrategy(),
    }

    @classmethod
    def get_strategy(cls, forecast_type: ForecastType) -> ForecastStrategy:
        strategy = cls._strategies.get(forecast_type)
        if not strategy:
            raise ValueError(f"Unsupported forecast type: {forecast_type}")
        return strategy