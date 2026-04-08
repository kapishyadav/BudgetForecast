import boto3
import pandas as pd
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSCostExplorerClient:
    def __init__(self, access_key: str, secret_key: str, region: str = 'us-east-1'):
        try:
            self.client = boto3.client(
                'ce',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        except Exception as e:
            logger.error(f"Failed to initialize Boto3 Cost Explorer client: {e}")
            raise

    def fetch_daily_costs(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches granular daily costs from AWS and formats them into a DataFrame
        that semantic_column_mapper.py can easily understand.
        Dates must be in 'YYYY-MM-DD' format.
        """

        data = []
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}
                ]
            )

            # Parse AWS's deeply nested JSON response
            for result_by_time in response.get('ResultsByTime', []):
                date_str = result_by_time['TimePeriod']['Start']

                for group in result_by_time.get('Groups', []):
                    # Keys map to the GroupBy list above [SERVICE, LINKED_ACCOUNT]
                    service_name = group['Keys'][0]
                    account_name = group['Keys'][1]
                    cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])

                    data.append({
                        'Date': date_str,
                        'Cost Amount': cost_amount,
                        'AWS Service': service_name,
                        'AWS Account ID': account_name
                    })

        except ClientError as e:
            logger.error(f"AWS API Error: {e}")
            raise ValueError(f"Failed to fetch data from AWS: {e.response['Error']['Message']}")

        # Return a Pandas DataFrame.
        # When passed to _process_dataframe(), the SemanticColumnMapper will automatically
        # map 'Cost Amount' -> 'spend', 'AWS Service' -> 'serviceName', etc.
        return pd.DataFrame(data)
