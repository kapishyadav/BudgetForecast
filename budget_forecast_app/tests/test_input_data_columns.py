from django.test import TestCase
import pandas as pd

EXPECTED_COLUMNS = {
    "month",
    "serviceName",
    "usageFamily",
    "accountName",
    "accountID",
    "countryCode",
    "buCode",
    "region",
    "segment",
    "costString",
    "spend",
}

class InputDataFrameColumnTest(TestCase):

    def test_dataframe_has_required_columns_only(self):
        # Example input DataFrame (replace with real loader if needed)
        df = pd.DataFrame(columns=list(EXPECTED_COLUMNS))

        # Convert DataFrame columns to a set
        df_columns = set(df.columns)

        # Check missing columns
        missing = EXPECTED_COLUMNS - df_columns
        self.assertEqual(len(missing), 0, f"Missing columns: {missing}")

        # Check extra columns
        extra = df_columns - EXPECTED_COLUMNS
        self.assertEqual(len(extra), 0, f"Unexpected extra columns: {extra}")

        # Check exact match
        self.assertEqual(df_columns, EXPECTED_COLUMNS)
