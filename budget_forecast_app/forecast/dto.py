# forecast/dtos.py
from dataclasses import dataclass
from typing import Optional
from django.core.files.uploadedfile import UploadedFile


@dataclass(frozen=True)
class ForecastTriggerDTO:
    """Contract for triggering a standard budget forecast."""
    dataset_id: str
    forecast_type: str
    granularity: str

    # Optional cascading filters
    account_name: Optional[str] = None
    service_name: Optional[str] = None
    bu_code: Optional[int] = None
    segment_name: Optional[str] = None

    def __post_init__(self):
        """Basic boundary validation before the service layer even sees the data."""
        if not self.dataset_id:
            raise ValueError("dataset_id is strictly required to trigger a forecast.")

        # Ensures bu_code is an integer if it exists, preventing DB type errors later
        if self.bu_code is not None and not isinstance(self.bu_code, int):
            object.__setattr__(self, 'bu_code', int(self.bu_code))


@dataclass(frozen=True)
class CustomScenarioDTO:
    """Contract for running a forecast with custom hyperparameters."""
    dataset_id: str
    changepoint_prior_scale: float
    seasonality_mode: str
    include_holidays: bool

    def __post_init__(self):
        if not self.dataset_id:
            raise ValueError("dataset_id is required.")
        if self.changepoint_prior_scale <= 0:
            raise ValueError("Changepoint prior scale must be greater than 0.")
        if self.seasonality_mode not in ["additive", "multiplicative"]:
            raise ValueError("Seasonality mode must be 'additive' or 'multiplicative'.")

@dataclass(frozen=True)
class DatasetUploadDTO:
    """Contract for uploading and processing a new dataset."""
    file: UploadedFile
    dataset_name: str

    def __post_init__(self):
        # Fail-fast validation before the service even touches the file
        if not self.file.name.lower().endswith('.csv'):
            raise ValueError("Only CSV files are currently supported.")
        if self.file.size == 0:
            raise ValueError("The uploaded file is empty.")
