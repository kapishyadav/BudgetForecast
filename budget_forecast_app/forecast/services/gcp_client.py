import pandas as pd
import logging
from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GCPBillingClient:
    def __init__(self, service_account_info: dict):
        try:
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        except Exception as e:
            logger.error(f"Failed to initialize GCP BigQuery client: {e}")
            raise

    def fetch_daily_costs(self, table_id: str, start_date: str, end_date: str) -> pd.DataFrame:
        # Standardizing the GCP billing export schema into the expected dataframe structure
        query = f"""
            SELECT
                DATE(usage_start_time) as Date,
                service.description as GCP_Service,
                project.name as GCP_Project,
                SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)) as Cost_Amount
            FROM
                `{table_id}`
            WHERE
                DATE(usage_start_time) >= @start_date
                AND DATE(usage_start_time) <= @end_date
            GROUP BY
                1, 2, 3
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )

        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()

            data = []
            for row in results:
                data.append({
                    'Date': str(row.Date),
                    'GCP Service': row.GCP_Service,
                    'GCP Project': row.GCP_Project,
                    'Cost Amount': float(row.Cost_Amount)
                })
            return pd.DataFrame(data)

        except Exception as e:
            logger.error(f"BigQuery execution failed: {e}")
            raise ValueError(f"Failed to fetch data from GCP: {str(e)}")