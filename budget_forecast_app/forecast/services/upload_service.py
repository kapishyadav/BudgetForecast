import pandas as pd
import logging
from typing import Dict, List
from django.db import transaction

from ..models import ForecastDataset, HistoricalSpend
from ..dto import DatasetUploadDTO
from ..config import DATASET_COLUMN_MAPPINGS
from .semantic_column_mapper import SemanticColumnMapper

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
        """Maps available column names to standardized canonical names using exact and semantic matching."""
        columns_dict = {}
        used_user_columns = set()

        # --- Tier 1: The Exact / Lexical Match (Fast Path) ---
        for canonical_name, possible_names in mappings.items():
            match = next((name for name in possible_names if name in available_columns), None)
            if match:
                columns_dict[canonical_name] = match
                used_user_columns.add(match)

        # --- Tier 2: Semantic Embeddings ---
        # 1. Identify what is left over
        unmapped_user_columns = [col for col in available_columns if col not in used_user_columns]
        missing_canonical_columns = [can for can in mappings.keys() if can not in columns_dict]

        # 2. Only invoke the ML model if there's actually work left to do
        if unmapped_user_columns and missing_canonical_columns:
            mapper = SemanticColumnMapper()  # Fetches the singleton instance instantly

            # Run the vector similarity search
            semantic_results = mapper.map_columns(unmapped_user_columns, threshold=0.65)

            # 3. Update our dictionary with the ML predictions
            for user_col, data in semantic_results.items():
                if data['status'] == 'mapped':
                    mapped_target = data['mapped_to']

                    # Crucial Check: Ensure we actually needed this target column
                    # AND that we don't overwrite an existing match from Tier 1.
                    if mapped_target in missing_canonical_columns and mapped_target not in columns_dict:
                        columns_dict[mapped_target] = user_col

                        #log this so you can track ML successes in production
                        logger.info(f"ML Mapped: '{user_col}' -> '{mapped_target}' (Score: {data['confidence']})")

        return columns_dict
