from .prophet_model import run_prophet_forecast
from .xgboost_model import run_xgboost_forecast
from .catboost_model import run_catboost_forecast

class ModelEngineFactory:
    _engines = {
        "prophet": run_prophet_forecast,
        "xgboost": run_xgboost_forecast,
        "catboost": run_catboost_forecast,
    }

    @classmethod
    def get_engine(cls, model_name: str):
        engine = cls._engines.get(model_name.lower())
        if not engine:
            raise ValueError(f"Unsupported model engine: {model_name}")
        return engine
