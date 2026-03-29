# forecast/ml/main.py
"""
main.py
-------
Central forecasting engine orchestrator.
Delegates execution to specific ForecastStrategies based on user input.
"""
import pandas as pd

from .utils.setup_logging import setup_logging
from .enums import ForecastType, Granularity
from .strategies import ForecastStrategyFactory

logger = setup_logging()

def run_forecast(df: pd.DataFrame,
                 forecast_type: ForecastType = ForecastType.OVERALL_AGGREGATE,
                 granularity: Granularity = Granularity.MONTHLY, model_name: str = "prophet",
                 hyperparameters: dict = None, **kwargs):
    """Main entry point for the forecasting pipeline using the Strategy Pattern."""

    if hyperparameters is None:
        hyperparameters = {}

    logger.info(f"Running {model_name} forecast with type: {forecast_type.value}")

    if df is None or df.empty:
        raise ValueError("The provided dataset is empty and contains no historical spend data.")

    try:
        # 1. Retrieve the specific strategy using the Factory
        strategy = ForecastStrategyFactory.get_strategy(forecast_type)

        # 2. Validate the specific requirements for this strategy (OCP & SRP)
        strategy.validate(**kwargs)

        # 3. Execute the pipeline
        logger.info(f"{forecast_type.value} forecasting starting.")
        forecast_df, historical_df, metrics_dict = strategy.execute(
            df=df,
            granularity=granularity,
            logger=logger,
            model_name = model_name,
            hyperparameters = hyperparameters,
            **kwargs
        )
        logger.info(f"{forecast_type.value} forecasting complete.")

        return {
            "forecast": forecast_df,
            "history": historical_df,
            "metrics": metrics_dict
        }

    except Exception as e:
        logger.error(f"Forecasting failed in main : {e}")
        raise