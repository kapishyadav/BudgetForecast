import pandas as pd
import logging
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import QueryDefinition, QueryDataset, QueryTimePeriod, QueryGrouping

logger = logging.getLogger(__name__)


class AzureCostClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, subscription_id: str):
        self.subscription_id = subscription_id
        try:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            self.client = CostManagementClient(credential)
        except Exception as e:
            logger.error(f"Failed to initialize Azure Cost client: {e}")
            raise

    def fetch_daily_costs(self, start_date: str, end_date: str) -> pd.DataFrame:
        scope = f"/subscriptions/{self.subscription_id}"

        query_payload = QueryDefinition(
            type="ActualCost",
            timeframe="Custom",
            time_period=QueryTimePeriod(from_property=start_date, to=end_date),
            dataset=QueryDataset(
                granularity="Daily",
                grouping=[
                    QueryGrouping(type="Dimension", name="ServiceName"),
                    QueryGrouping(type="Dimension", name="SubscriptionName")
                ]
            )
        )

        response = self.client.query.usage(scope, query_payload)

        data = []
        # Azure returns rows as a list of lists. Column order matches response.columns
        for row in response.rows:
            data.append({
                'Cost Amount': float(row[0]),  # Pre-tax cost
                'Date': str(row[1]),
                'Azure Service': str(row[2]),
                'Subscription': str(row[3])
            })

        # The output naming perfectly aligns with the SemanticColumnMapper expectation
        return pd.DataFrame(data)