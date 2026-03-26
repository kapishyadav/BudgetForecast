import pandas as pd
import logging
from typing import Dict, List
from django.db import transaction

from ..models import ForecastDataset, HistoricalSpend
from ..dto import DatasetUploadDTO
from ..config import DATASET_COLUMN_MAPPINGS

logger = logging.getLogger(__name__)


class DatasetUploadService:
    """Handles parsing, validating, and persisting uploaded budget datasets."""

    def process_csv_upload(self, dto: DatasetUploadDTO) -> str:
        """Processes the CSV and saves records to the database. Returns the Dataset ID."""
        logger.info(f"Processing upload for dataset: {dto.dataset_name}")

        # Read CSV directly into memory
        try:
            df = pd.read_csv(dto.file)
            df.columns = df.columns.str.strip()
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {str(e)}")

        # Dynamic Column Mapping
        mapped_columns = self._get_mapped_columns(df.columns.tolist(), DATASET_COLUMN_MAPPINGS)
        rename_dict = {actual_col: canonical_col for canonical_col, actual_col in mapped_columns.items()}
        df = df.rename(columns=rename_dict)

        # Critical Validation
        if 'date' not in df.columns:
            raise ValueError("CSV must contain a recognized date column (e.g., date, month, Date).")
        if 'spend' not in df.columns:
            raise ValueError("CSV must contain a recognized spend/cost column.")

        # Database Insertion
        dataset = ForecastDataset.objects.create(name=dto.dataset_name)
        spend_records = []

        # Check for optional columns safely
        has_account = 'accountName' in df.columns
        has_service = 'serviceName' in df.columns
        has_bucode = 'buCode' in df.columns
        has_segment = 'segment' in df.columns

        for index, row in df.iterrows():
            record = HistoricalSpend(
                dataset=dataset,
                date=pd.to_datetime(row['date']).date(),
                spend=row['spend'],
                account_name=row['accountName'] if has_account and pd.notna(row['accountName']) else None,
                service_name=row['serviceName'] if has_service and pd.notna(row['serviceName']) else None,
                bu_code=int(row['buCode']) if has_bucode and pd.notna(row['buCode']) else None,
                segment=row['segment'] if has_segment and pd.notna(row['segment']) else None,
            )
            spend_records.append(record)

        # Bulk create wrapped in a transaction ensures all-or-nothing saving
        with transaction.atomic():
            HistoricalSpend.objects.bulk_create(spend_records, batch_size=5000)

        logger.info(f"Successfully saved {len(spend_records)} rows to Postgres for dataset {dataset.id}.")
        return str(dataset.id)

    def _get_mapped_columns(self, available_columns: list, mappings: Dict[str, List[str]]) -> Dict[str, str]:
        """Maps available column names to standardized canonical names."""
        columns_dict = {}
        for canonical_name, possible_names in mappings.items():
            match = next((name for name in possible_names if name in available_columns), None)
            if match:
                columns_dict[canonical_name] = match
        return columns_dict
