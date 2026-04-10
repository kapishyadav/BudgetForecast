import logging
import os
import time  # Fixed: changed from 'from datetime import time' so time.time() works
from datetime import timedelta
import pandas as pd
import json

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.utils import timezone

from .models import ForecastRun, HistoricalSpend
from .services.optuna_tuning_service import OptunaTuningService
from .ml.enums import ForecastType, Granularity

from .models import CloudIntegration
from .services.ingestion_service import DataIngestionService
from .services.llm_providers import OllamaProvider
from .services.prescriptive_service import PrescriptiveAnalysisService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_forecast_task(self, dataset_id,
                           forecast_type_str="overall_aggregate",
                           granularity_str="monthly",
                           model_name="prophet",
                           hyperparameters=None,
                           **kwargs):
    logger.info(f"Task {self.request.id}: Starting forecast generation for dataset id: {dataset_id}")
    if hyperparameters is None:
        hyperparameters = {}
    try:
        from .services.services import ForecastOrchestrationService
        service = ForecastOrchestrationService()
        result = service.execute_forecast_pipeline(
            task_id=self.request.id,
            dataset_id=dataset_id,
            forecast_type_str=forecast_type_str,
            granularity_str=granularity_str,
            model_name=model_name,
            hyperparameters=hyperparameters,
            **kwargs
        )

        insight = "Analyzing forecast patterns..."

        try:
            from .services.llm_providers import OllamaProvider
            from .services.prescriptive_service import PrescriptiveAnalysisService

            # Generate the insight
            llm_client = OllamaProvider()
            llm_service = PrescriptiveAnalysisService(llm_client)

            pipeline_metrics = result.get('metrics', {})

            # 1. Load the Historical Dataframe
            historical_df = HistoricalSpend.objects.get_dataset_as_dataframe(dataset_id=dataset_id)

            # 2. Dynamically calculate the number of historical months
            historical_months = len(historical_df)

            # 3. Pull the forecast period from the metrics (default to 12 if missing)
            forecast_months = pipeline_metrics.get('forecast_period', 12)
            total_forecast_spend = pipeline_metrics.get('total_forecasted_spend', 0)

            # 4. Calculate total spend
            if 'spend' in historical_df.columns:
                total_current_spend = historical_df['spend'].sum()
            elif 'y' in historical_df.columns:
                total_current_spend = historical_df['y'].sum()
            else:
                total_current_spend = 0.0

            insight = llm_service.generate_and_save_insight(
                task_id=self.request.id,
                total_current_spend=total_current_spend,
                total_forecast_spend=total_forecast_spend,
                historical_months = historical_months,
                forecast_months = forecast_months
            )

            logger.info(f"DEBUG : insight generated in celery task is : {insight}")

            # 1. EXPLICITLY set the key in the result dictionary so it cannot be overwritten
            result['prescriptive_insight'] = insight

            # 2. Save to database
            ForecastRun.objects.filter(task_id=self.request.id).update(
                prescriptive_insight=insight
            )
            logger.info(f"Task {self.request.id}: AI Insight generated successfully.")

        except Exception as ai_error:
            logger.error(f"Task {self.request.id}: Failed to generate AI insight - {str(ai_error)}")
            result['prescriptive_insight'] = "Insight generation temporarily unavailable."

        return {"status": "success",
                **result,
                "prescriptive_insight": insight
                }

    except Exception as e:
        logger.error(f"Task {self.request.id}: Forecasting failed - {str(e)}")
        # If anything in the pipeline crashes, safely update the DB so the UI knows it failed
        ForecastRun.objects.filter(task_id=self.request.id).update(
            # Assuming you add a status field, e.g., status='failed'
            status='failed'
        )
        return {
            "status": "error",
            "message": str(e)
        }


@shared_task(bind=True)
def run_optuna_tuning_task(self, dataset_id,
                           forecast_type_str="overall_aggregate",
                           granularity_str="monthly",
                           model_name="prophet",
                           tuning_trials=20,
                           **kwargs):
    """Runs Optuna hyperparameter tuning, then executes the forecast pipeline."""
    logger.info(f"Task {self.request.id}: Starting OPTUNA tuning ({tuning_trials} trials) for dataset: {dataset_id}")

    try:
        from .services.services import ForecastOrchestrationService
        from .models import HistoricalSpend

        # 1. Load the dataset into a pandas DataFrame using your custom manager!
        df = HistoricalSpend.objects.get_dataset_as_dataframe(dataset_id=dataset_id)

        # 2. Convert strings back to your Enum classes for the ML pipeline
        forecast_type = ForecastType(forecast_type_str)
        granularity = Granularity(granularity_str)

        # 3. Initialize and run the tuner
        tuner = OptunaTuningService(
            df=df,
            forecast_type=forecast_type,
            granularity=granularity,
            model_name=model_name,
            logger=logger,
            **kwargs
        )

        # Run the study to find the best parameters
        best_params = tuner.run_study(n_trials=tuning_trials)
        logger.info(f"Task {self.request.id}: Optuna found best params: {best_params}")

        # 4. Update the DB record, removing the "tuning_in_progress" placeholder
        ForecastRun.objects.filter(task_id=self.request.id).update(
            hyperparameters=best_params
        )

        # 5. Now, run the ACTUAL forecast pipeline using these newly found parameters!
        service = ForecastOrchestrationService()
        result = service.execute_forecast_pipeline(
            task_id=self.request.id,
            dataset_id=dataset_id,
            forecast_type_str=forecast_type_str,
            granularity_str=granularity_str,
            model_name=model_name,
            hyperparameters=best_params,
            **kwargs
        )

        insight = "Analyzing forecast patterns..."

        try:
            from .services.llm_providers import OllamaProvider
            from .services.prescriptive_service import PrescriptiveAnalysisService

            # Generate the insight
            llm_client = OllamaProvider()
            llm_service = PrescriptiveAnalysisService(llm_client)

            pipeline_metrics = result.get('metrics', {})

            # 1. Load the Historical Dataframe
            historical_df = HistoricalSpend.objects.get_dataset_as_dataframe(dataset_id=dataset_id)

            # 2. Dynamically calculate the number of historical months
            historical_months = len(historical_df)

            # 3. Pull the forecast period from the metrics (default to 12 if missing)
            forecast_months = pipeline_metrics.get('forecast_period', 12)
            total_forecast_spend = pipeline_metrics.get('total_forecasted_spend', 0)

            # 4. Calculate total spend
            if 'spend' in historical_df.columns:
                total_current_spend = historical_df['spend'].sum()
            elif 'y' in historical_df.columns:
                total_current_spend = historical_df['y'].sum()
            else:
                total_current_spend = 0.0

            insight = llm_service.generate_and_save_insight(
                task_id=self.request.id,
                total_current_spend=total_current_spend,
                total_forecast_spend=total_forecast_spend,
                historical_months=historical_months,
                forecast_months=forecast_months
            )

            logger.info(f"DEBUG : insight generated in celery task is : {insight}")

            # 1. EXPLICITLY set the key in the result dictionary so it cannot be overwritten
            result['prescriptive_insight'] = insight

            # 2. Save to database
            ForecastRun.objects.filter(task_id=self.request.id).update(
                prescriptive_insight=insight
            )
            logger.info(f"Task {self.request.id}: AI Insight generated successfully.")

        except Exception as ai_error:
            logger.error(f"Task {self.request.id}: Failed to generate AI insight - {str(ai_error)}")
            result['prescriptive_insight'] = "Insight generation temporarily unavailable."

        return {"status": "success",
                "tuned_params": best_params,
                **result,
                "prescriptive_insight": insight
                }

    except Exception as e:
        logger.error(f"Task {self.request.id}: Optuna tuning failed - {str(e)}")
        ForecastRun.objects.filter(task_id=self.request.id).update(
            status='failed'
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


@shared_task
def sync_all_cloud_billing():
    """Master task scheduled by Celery Beat to trigger all active syncs."""
    active_integrations = CloudIntegration.objects.filter(is_active=True)

    logger.info(f"Starting daily sync for {active_integrations.count()} active integrations.")

    for integration in active_integrations:
        # Dispatch a separate sub-task for each integration so a failure in one
        # doesn't crash the sync for the others.
        sync_integration_data.delay(integration.id)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def sync_integration_data(self, integration_id: int):
    """
    Worker sub-task to execute the API call.
    Uses exponential backoff (retry_backoff=True) to handle API rate limits natively.
    """
    try:
        integration = CloudIntegration.objects.get(id=integration_id)
    except CloudIntegration.DoesNotExist:
        logger.error(f"Integration ID {integration_id} not found.")
        return

    # Always pull the last 3 days to account for delayed billing adjustments from cloud providers
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=3)

    # Format exactly as the Cloud SDKs expect ('YYYY-MM-DD')
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    service = DataIngestionService()

    try:
        if integration.provider == 'AWS':
            service.process_aws_ingestion(integration, start_str, end_str)
        elif integration.provider == 'AZURE':
            service.process_azure_ingestion(integration, start_str, end_str)  # To be built
        elif integration.provider == 'GCP':
            service.process_gcp_ingestion(integration, start_str, end_str)  # To be built

        # Update health tracking on success
        integration.last_synced_at = timezone.now()
        integration.save(update_fields=['last_synced_at'])
        logger.info(f"Successfully synced {integration.provider} for dataset {integration.dataset.id}")

    except Exception as exc:
        logger.warning(f"Error syncing {integration.provider} integration {integration_id}: {exc}. Retrying...")
        try:
            # Raise exception to trigger Celery's autoretry mechanism
            raise exc
        except MaxRetriesExceededError:
            # If it fails 3 times in a row, flag it for the user in the UI
            logger.error(f"Max retries exceeded for integration {integration_id}.")
            integration.is_active = False
            integration.save(update_fields=['is_active'])
            # Optional: Trigger an email alert to yourself here

