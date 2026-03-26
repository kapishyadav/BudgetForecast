# forecast/services/services.py
import logging
from django.shortcuts import get_object_or_404

from ..dto import ForecastTriggerDTO, CustomScenarioDTO
from ..models import ForecastDataset, ForecastRun
from ..tasks import generate_forecast_task

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

        logger.info(f"Dispatching custom scenario task for dataset {dto.dataset_id}")
        task = generate_forecast_task.delay(
            dataset_id=dto.dataset_id,
            changepoint_prior_scale=dto.changepoint_prior_scale,
            seasonality_mode=dto.seasonality_mode,
            include_holidays=dto.include_holidays
        )

        ForecastRun.objects.create(
            dataset=dataset,
            task_id=task.id,
            changepoint_prior_scale=dto.changepoint_prior_scale,
            seasonality_mode=dto.seasonality_mode,
            include_holidays=dto.include_holidays
        )

        return {
            "status": "success",
            "task_id": task.id,
            "message": "Scenario triggered successfully."
        }
