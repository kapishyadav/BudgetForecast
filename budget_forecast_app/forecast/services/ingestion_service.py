import pandas as pd
import logging
from typing import Dict, List
from django.db import transaction

from ..models import ForecastDataset, HistoricalSpend, CloudIntegration
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

        dataset = ForecastDataset.objects.create(name=dto.dataset_name)
        return self._process_dataframe(df, dataset)

    def process_aws_ingestion(self, integration: CloudIntegration, start_date: str, end_date: str) -> str:
        """Automated AWS ingestion method."""
        logger.info(f"Processing AWS ingestion for dataset: {integration.dataset.name}")
        from .aws_client import AWSCostExplorerClient  # Local import to prevent circular dependencies

        client = AWSCostExplorerClient(
            access_key=integration.access_key,
            secret_key=integration.secret_key
        )
        df = client.fetch_daily_costs(start_date, end_date)
        return self._process_dataframe(df, integration.dataset)

    def _process_dataframe(self, df: pd.DataFrame, dataset: ForecastDataset) -> str:
        """Shared core logic for dynamic mapping and DB insertion."""
        # Dynamic Column Mapping
        mapped_columns = self._get_mapped_columns(df.columns.tolist(), DATASET_COLUMN_MAPPINGS)
        rename_dict = {actual_col: canonical_col for canonical_col, actual_col in mapped_columns.items()}
        df = df.rename(columns=rename_dict)

        # Critical Validation
        if 'date' not in df.columns:
            raise ValueError("Data must contain a recognized date column.")
        if 'spend' not in df.columns:
            raise ValueError("Data must contain a recognized spend/cost column.")

        # Ensure timezone-naive dates to prevent merging overlaps
        df['date'] = pd.to_datetime(df['date']).dt.date

        spend_records = []
        has_account = 'accountName' in df.columns
        has_service = 'serviceName' in df.columns
        has_bucode = 'buCode' in df.columns
        has_segment = 'segment' in df.columns

        for index, row in df.iterrows():
            # Default to "Unallocated" if the cloud provider didn't return an account/service grouping
            service_val = row['serviceName'] if has_service and pd.notna(row['serviceName']) else 'Unallocated'
            account_val = row['accountName'] if has_account and pd.notna(row['accountName']) else 'Unallocated'

            record = HistoricalSpend(
                dataset=dataset,
                date=pd.to_datetime(row['date']).date(),
                spend=row['spend'],
                account_name=account_val,
                service_name=service_val,
                bu_code=int(row['buCode']) if has_bucode and pd.notna(row['buCode']) else None,
                segment=row['segment'] if has_segment and pd.notna(row['segment']) else None,
            )
            spend_records.append(record)

        # Bulk create wrapped in a transaction ensures all-or-nothing Idempotent saving.
        with transaction.atomic():
            HistoricalSpend.objects.bulk_create(
                spend_records,
                batch_size=5000,
                update_conflicts=True,
                unique_fields=['dataset', 'date', 'service_name', 'account_name'],
                update_fields=['spend'] # If a record exists, update the spend amount
            )

        logger.info(f"Idempotently merged {len(spend_records)} rows to Postgres for dataset {dataset.id}.")
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
