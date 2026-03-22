# Create your models here.
from django.db import models
import uuid


class ForecastDataset(models.Model):
    """Represents a single uploaded budget file/project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.created_at.date()})"


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
