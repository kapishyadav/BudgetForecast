
import logging

import pandas as pd
from celery import shared_task
from .models import ForecastRun

# Import your ML logic and Enums
from .ml.main import run_forecast
from .ml.enums import ForecastType, Granularity
from .models import ForecastDataset, HistoricalSpend

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_forecast_task(self, dataset_id, forecast_type_str="overall_aggregate", granularity_str="monthly", **kwargs):
    logger.info(f"Task {self.request.id}: Starting forecast generation for dataset id: {dataset_id}")

    try:
        from .services.services import ForecastOrchestrationService
        service = ForecastOrchestrationService()
        result = service.execute_forecast_pipeline(
            task_id=self.request.id,
            dataset_id=dataset_id,
            forecast_type_str=forecast_type_str,
            granularity_str=granularity_str,
            **kwargs
        )
        return {"status": "success", **result}

    except Exception as e:
        logger.error(f"Task {self.request.id}: Forecasting failed - {str(e)}")
        # If anything in the pipeline crashes, safely update the DB so the UI knows it failed
        ForecastRun.objects.filter(task_id=self.request.id).update(
            # Assuming you add a status field, e.g., status='failed'
            # status='failed',
            # error_message=str(e)
        )
        return {
            "status": "error",
            "message": str(e)
        }
