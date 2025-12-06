from django.test import TestCase
from prophet import Prophet
import pandas as pd

class ProphetModelTest(TestCase):

    def test_prophet_forecast(self):
        # Create synthetic training data
        df = pd.DataFrame({
            "ds": pd.date_range(start="2023-01-01", periods=24, freq="D"),
            "y": range(24)
        })

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=24)
        forecast = model.predict(future)

        # Check forecast shape
        self.assertEqual(len(forecast), 48)

        # Check required columns exist
        for col in ["ds", "yhat", "yhat_lower", "yhat_upper"]:
            self.assertIn(col, forecast.columns)
