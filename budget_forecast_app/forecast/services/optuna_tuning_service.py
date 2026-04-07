import optuna
import pandas as pd
import logging
from ..ml.enums import ForecastType, Granularity
from ..ml.strategies import ForecastStrategyFactory


class OptunaTuningService:
    def __init__(self, df: pd.DataFrame, forecast_type: ForecastType,
                 granularity: Granularity, model_name: str, logger: logging.Logger, **kwargs):
        self.df = df.copy()
        # Ensure the column matches the strict BaseForecaster requirements
        if granularity == Granularity.MONTHLY and 'date' in self.df.columns:
            self.df.rename(columns={'date': 'month'}, inplace=True)

        self.forecast_type = forecast_type
        self.granularity = granularity
        self.model_name = model_name.lower()
        self.logger = logger
        self.kwargs = kwargs

    def _get_search_space(self, trial) -> dict:
        """Dynamically routes the search space based on the selected model."""
        if self.model_name == "prophet":
            return {
                "changepoint_prior_scale": trial.suggest_float("changepoint_prior_scale", 0.001, 0.5, log=True),
                "seasonality_mode": trial.suggest_categorical("seasonality_mode", ["additive", "multiplicative"]),
                # "holidays": trial.suggest_categorical("holidays", ["US", "IN", None]) # Optional addition
            }

        elif self.model_name == "xgboost":
            return {
                "learning_rate": trial.suggest_float("learning_rate", 1e-4, 0.3, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0)
            }

        elif self.model_name == "catboost":
            return {
                "learning_rate": trial.suggest_float("learning_rate", 1e-4, 0.3, log=True),
                "depth": trial.suggest_int("depth", 4, 10),
                "iterations": trial.suggest_int("iterations", 50, 300)
            }

        else:
            raise ValueError(f"No Optuna search space defined for {self.model_name}")

    def objective(self, trial):
        """The function Optuna will try to minimize."""

        # 1. Get the dynamic hyperparameters for this trial
        params = self._get_search_space(trial)

        # 2. Retrieve the requested strategy (Account, Segment, etc.)
        strategy = ForecastStrategyFactory.get_strategy(self.forecast_type)

        try:
            # 3. Execute your EXACT existing pipeline using the factory
            # We disable logging inside the trial to prevent log spam
            forecast_df, history_df, metrics = strategy.execute(
                df=self.df,
                granularity=self.granularity,
                logger=None,
                model_name=self.model_name,
                hyperparameters=params,
                **self.kwargs
            )

            # 4. Optuna attempts to minimize the RMSE returned by your model
            return metrics.get('rmse', float('inf'))

        except Exception as e:
            # If a specific parameter combination causes the model to crash, tell Optuna to prune it
            import traceback
            self.logger.error(f"TRIAL CRASHED: {str(e)}")
            self.logger.error(traceback.format_exc())

            raise e
            # raise optuna.TrialPruned()

    def run_study(self, n_trials: int = 20) -> dict:
        """Executes the tuning study and returns the best hyperparameters."""
        self.logger.info(f"Starting Optuna tuning for {self.model_name} with {n_trials} trials.")

        study = optuna.create_study(direction="minimize")
        study.optimize(self.objective, n_trials=n_trials)

        self.logger.info(f"Tuning complete. Best RMSE: {study.best_value}")
        return study.best_params
