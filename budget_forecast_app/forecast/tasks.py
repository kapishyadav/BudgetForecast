
import logging
import os
from datetime import time

from celery import shared_task
from .models import ForecastRun
from django.conf import settings

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


@shared_task
def delete_old_files_task(max_age_hours=24):
    """Periodic task to clean up old CSV uploads."""
    logger.info("Starting background file cleanup...")

    # Define your upload directory (ensure this matches your actual setup)
    upload_dir = os.path.join(settings.BASE_DIR, 'uploads')

    if not os.path.exists(upload_dir):
        return "Upload directory does not exist."

    current_time = time.time()
    deleted_count = 0

    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            # Check file age
            file_age_seconds = current_time - os.path.getctime(file_path)
            if file_age_seconds > (max_age_hours * 3600):
                os.remove(file_path)
                logger.info(f"Deleted old file: {filename}")
                deleted_count += 1

    return f"Cleanup complete. Deleted {deleted_count} files."
