# Create your models here.
from django.db import models
import uuid
import pandas as pd


class ForecastDataset(models.Model):
    """Represents a single uploaded budget file/project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.created_at.date()})"


class HistoricalSpendManager(models.Manager):
    """Data Access Layer for Historical Spend data."""

    def get_cascading_suggestions(self, dataset_id: str, model_field: str, query: str, active_filters: dict) -> list:
        """Optimized database query to fetch unique column suggestions."""
        filter_kwargs = {"dataset_id": dataset_id}

        # Apply active cascading filters (ignore the field the user is currently typing in)
        for field, value in active_filters.items():
            if value and field != model_field:
                filter_kwargs[field] = value

        # Apply the search query
        if query:
            filter_kwargs[f"{model_field}__icontains"] = query

        # Execute optimized DB query
        suggestions = (
            self.filter(**filter_kwargs)
            .values_list(model_field, flat=True)
            .distinct()[:10]
        )
        return [str(val) for val in suggestions if val is not None]

    def get_dataset_as_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Fetches historical data and immediately returns a Pandas DataFrame."""
        historical_data = self.filter(dataset_id=dataset_id).values(
            'date', 'spend', 'account_name', 'service_name', 'bu_code', 'segment'
        )

        if not historical_data:
            raise ValueError(f"No historical data found for dataset {dataset_id}")

        return pd.DataFrame(list(historical_data))


class HistoricalSpend(models.Model):
    """Stores the actual row-by-row data from the CSV."""
    dataset = models.ForeignKey(ForecastDataset, on_delete=models.CASCADE, related_name='historical_data')
    date = models.DateField()
    spend = models.DecimalField(max_digits=14, decimal_places=2)

    # Optional granular fields based on your previous CSV structure
    account_name = models.CharField(max_length=255, null=True, blank=True)
    service_name = models.CharField(max_length=255, null=True, blank=True)
    bu_code = models.IntegerField(null=True, blank=True)
    segment = models.CharField(max_length=255, null=True, blank=True)

    # Attach the custom manager
    objects = HistoricalSpendManager()

    class Meta:
        indexes = [models.Index(fields=['dataset', 'date'])]


class ForecastRun(models.Model):
    """Tracks different ML runs (and their hyperparameters) on the same dataset."""
    dataset = models.ForeignKey(ForecastDataset, on_delete=models.CASCADE, related_name='runs')
    task_id = models.CharField(max_length=255, unique=True)  # The Celery Task ID

    # Hyperparameters
    changepoint_prior_scale = models.FloatField(default=0.05)
    seasonality_mode = models.CharField(max_length=50, default='additive')
    include_holidays = models.BooleanField(default=False)

    # Results
    status = models.CharField(max_length=50, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
