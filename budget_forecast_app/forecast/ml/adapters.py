
from abc import ABC, abstractmethod
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BaseModelAdapter(ABC):
    """The standard contract for all ML models in the system."""

    def __init__(self, hyperparameters: dict = None):
        self.hyperparameters = hyperparameters or {}
        self.model = None

    @abstractmethod
    def fit(self, df: pd.DataFrame):
        """Trains the model on historical data."""
        pass

    @abstractmethod
    def predict(self, horizon: int, granularity: str) -> pd.DataFrame:
        """Generates future predictions."""
        pass


class ProphetAdapter(BaseModelAdapter):
    """Adapts the standard interface to Facebook Prophet's specific requirements."""

    def fit(self, df: pd.DataFrame):
        from prophet import Prophet
        logger.info(f"Training Prophet with params: {self.hyperparameters}")

        # Prophet strictly requires columns to be named 'ds' and 'y'
        train_df = df.rename(columns={'date': 'ds', 'spend': 'y'})

        # Inject dynamic hyperparameters safely
        self.model = Prophet(
            changepoint_prior_scale=self.hyperparameters.get('changepoint_prior_scale', 0.05),
            seasonality_mode=self.hyperparameters.get('seasonality_mode', 'additive')
        )

        if self.hyperparameters.get('include_holidays'):
            self.model.add_country_holidays(country_name='US')  # Or dynamic country

        self.model.fit(train_df)

    def predict(self, horizon: int, granularity: str) -> pd.DataFrame:
        freq_map = {'daily': 'D', 'weekly': 'W', 'monthly': 'MS', 'yearly': 'Y'}
        freq = freq_map.get(granularity, 'MS')

        future = self.model.make_future_dataframe(periods=horizon, freq=freq)
        forecast = self.model.predict(future)

        # Translate Prophet's output back to our standard format
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
            columns={'ds': 'date', 'yhat': 'forecast_spend', 'yhat_lower': 'lower_bound', 'yhat_upper': 'upper_bound'}
        )


class CatBoostAdapter(BaseModelAdapter):
    """Adapts the standard interface to CatBoost."""

    def fit(self, df: pd.DataFrame):
        from catboost import CatBoostRegressor
        logger.info(f"Training CatBoost with params: {self.hyperparameters}")

        # CatBoost requires feature engineering (e.g., extracting month/year from date)
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['year'] = pd.to_datetime(df['date']).dt.year

        X = df[['month', 'year']]
        y = df['spend']

        self.model = CatBoostRegressor(
            iterations=self.hyperparameters.get('iterations', 500),
            learning_rate=self.hyperparameters.get('learning_rate', 0.05),
            verbose=0
        )
        self.model.fit(X, y)

    def predict(self, horizon: int, granularity: str) -> pd.DataFrame:
        # Note: In a real scenario, you'd generate future dates and extract features
        # This is a simplified placeholder to show the contract
        import numpy as np

        # Fake future dataframe generation for demonstration
        future_dates = pd.date_range(start=pd.Timestamp.now(), periods=horizon, freq='MS')
        future_X = pd.DataFrame({'month': future_dates.month, 'year': future_dates.year})

        predictions = self.model.predict(future_X)

        return pd.DataFrame({
            'date': future_dates,
            'forecast_spend': predictions,
            'lower_bound': predictions * 0.9,  # Simplified bounds
            'upper_bound': predictions * 1.1
        })


class MLModelFactory:
    """Dynamically routes a model name to its corresponding Adapter implementation."""

    _adapters = {
        "prophet": ProphetAdapter,
        "catboost": CatBoostAdapter,
        # "linear_regression": LinearRegressionAdapter,
    }

    @classmethod
    def get_model(cls, model_name: str, hyperparameters: dict) -> BaseModelAdapter:
        adapter_class = cls._adapters.get(model_name.lower())
        if not adapter_class:
            raise ValueError(f"Unsupported ML Model: {model_name}")
        return adapter_class(hyperparameters=hyperparameters)
