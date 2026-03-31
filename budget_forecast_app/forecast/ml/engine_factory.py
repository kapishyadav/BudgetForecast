from .prophet_model import ProphetForecaster
from .xgboost_model import XGBoostForecaster
from .catboost_model import CatBoostForecaster


class ModelEngineFactory:
    _engines = {
        "prophet": ProphetForecaster,
        "xgboost": XGBoostForecaster,
        "catboost": CatBoostForecaster,
    }

    @classmethod
    def get_engine(cls, model_name: str):
        """
        Returns a wrapper function that perfectly matches the old
        functional signature expected by the orchestration layer.
        """
        engine_class = cls._engines.get(model_name.lower())
        if not engine_class:
            raise ValueError(f"Unsupported model engine: {model_name}")

        # Create a closure that matches the exact old function signature
        def engine_runner(df, granularity, logger=None, hyperparameters=None, **kwargs):
            # 1. Instantiate the newly refactored class
            forecaster = engine_class(
                granularity=granularity,
                logger=logger,
                hyperparameters=hyperparameters,
                **kwargs
            )
            # 2. Run the forecast pipeline passing the dataframe
            return forecaster.run(df)

        return engine_runner
