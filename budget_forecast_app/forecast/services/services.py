# forecast/services/services.py
import logging
from django.shortcuts import get_object_or_404

from ..dto import ForecastTriggerDTO, CustomScenarioDTO
from ..models import ForecastDataset, ForecastRun
from ..tasks import generate_forecast_task, run_optuna_tuning_task
from ..ml.enums import ForecastType, Granularity
from ..models import HistoricalSpend
from ..ml.main import run_forecast

logger = logging.getLogger(__name__)


class ForecastOrchestrationService:
    """Encapsulates all business logic for initiating forecasts."""

    def trigger_standard_forecast(self, dto: ForecastTriggerDTO) -> dict:
        # Ensure the dataset exists before queuing a task
        dataset = get_object_or_404(ForecastDataset, id=dto.dataset_id)

        # Reconstruct the dynamic filters (kwargs) cleanly from the DTO, ignoring None values
        filters = {
            "account_name": dto.account_name,
            "service_name": dto.service_name,
            "bu_code": dto.bu_code,
            "segment_name": dto.segment_name
        }
        active_filters = {k: v for k, v in filters.items() if v is not None}

        logger.info(f"Dispatching standard forecast task for dataset {dto.dataset_id}")
        task = generate_forecast_task.delay(
            dataset_id=dto.dataset_id,
            forecast_type_str=dto.forecast_type,
            granularity_str=dto.granularity,
            **active_filters
        )

        # Isolate DB write logic
        ForecastRun.objects.create(dataset=dataset, task_id=task.id)

        return {
            "status": "success",
            "task_id": task.id,
            "message": "Processing started."
        }

    def trigger_custom_scenario(self, dto: CustomScenarioDTO) -> dict:
        dataset = get_object_or_404(ForecastDataset, id=dto.dataset_id)

        # Reconstruct the dynamic filters (kwargs) cleanly from the DTO
        filters = {
            "account_name": getattr(dto, 'account_name', None),
            "service_name": getattr(dto, 'service_name', None),
            "bu_code": getattr(dto, 'bu_code', None),
            "segment_name": getattr(dto, 'segment_name', None)
        }
        active_filters = {k: v for k, v in filters.items() if v is not None}

        # Check the DTO for the Optuna tuning flags
        tune_hyperparameters = getattr(dto, 'tune_hyperparameters', False)
        tuning_trials = getattr(dto, 'tuning_trials', 20)

        if tune_hyperparameters:
            logger.info(f"Dispatching OPTUNA TUNING scenario for {dto.model_name} on dataset {dto.dataset_id}")

            # Dispatch to the specific Optuna tuning worker
            task = run_optuna_tuning_task.delay(
                dataset_id=dto.dataset_id,
                forecast_type_str=getattr(dto, 'forecast_type', 'overall_aggregate'),
                granularity_str=getattr(dto, 'granularity', 'monthly'),
                model_name=dto.model_name,
                tuning_trials=tuning_trials,
                **active_filters
            )
            message = f"{dto.model_name.capitalize()} tuning scenario triggered with {tuning_trials} trials."
            db_hyperparameters = {"status": "tuning_in_progress", "trials": tuning_trials}
            workflow_type = "hyperparameter_tuning"

        else:
            logger.info(f"Dispatching standard {dto.model_name} scenario for dataset {dto.dataset_id}")

            # Pass ALL parameters to the standard Celery task
            task = generate_forecast_task.delay(
                dataset_id=dto.dataset_id,
                forecast_type_str=getattr(dto, 'forecast_type', 'overall_aggregate'),
                granularity_str=getattr(dto, 'granularity', 'monthly'),
                model_name=dto.model_name,
                hyperparameters=dto.hyperparameters,
                **active_filters
            )
            message = f"{dto.model_name.capitalize()} standard scenario triggered successfully."
            db_hyperparameters = dto.hyperparameters
            workflow_type = "standard_forecast"

        logger.info(f"Dispatching custom {dto.model_name} scenario for dataset {dto.dataset_id}")

        # Save the generic JSON field to the database
        # If tuning, it saves the 'tuning_in_progress' placeholder dict
        ForecastRun.objects.create(
            dataset=dataset,
            task_id=task.id,
            model_name=dto.model_name,
            hyperparameters=db_hyperparameters
        )

        return {
            "status": "success",
            "task_id": task.id,
            "workflow_type": workflow_type,
            "message": message
        }

    def execute_forecast_pipeline(self, task_id: str, dataset_id: str,
                                  forecast_type_str: str,
                                  granularity_str: str,
                                  model_name: str = "prophet",
                                  hyperparameters: dict = None,
                                  logger=logger, **kwargs) -> dict:
        """Executes the ML pipeline and manages DB state."""
        if hyperparameters is None:
            hyperparameters = {}
        run = ForecastRun.objects.filter(task_id=task_id).first()

        # 1. Fetch Data using Data Access Layer
        df = HistoricalSpend.objects.get_dataset_as_dataframe(dataset_id=dataset_id)

        # 2. Map strings to Enums
        try:
            forecast_type = ForecastType(forecast_type_str)
            granularity = Granularity(granularity_str)
        except ValueError:
            logger.warning("Invalid enums passed, falling back to defaults.")
            forecast_type = ForecastType.OVERALL_AGGREGATE
            granularity = Granularity.MONTHLY

        if granularity == Granularity.MONTHLY:
            df.rename(columns={'date': 'month'}, inplace=True)

        # 3. Execute Strategy Pattern Engine
        result = run_forecast(df, forecast_type, granularity=granularity, model_name = model_name,
                              hyperparameters = hyperparameters, **kwargs)

        # 4. Serialize
        forecast_json = result["forecast"].to_json(orient="records", date_format="iso")
        historical_json = result["history"].to_json(orient="records", date_format="iso")

        # 5. Success! (The Celery worker will catch exceptions if this fails)
        if run:
            # Here you could save the forecast_json to the DB if needed in the future
            run.status = 'completed'
            run.save(update_fields=['status'])

        return {
            "forecast_json": forecast_json,
            "historical_json": historical_json,
            "metrics": result["metrics"],
            "dataset_id": dataset_id
        }
