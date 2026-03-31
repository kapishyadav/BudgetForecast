"""
prophet_model.py
----------------
Unified Prophet forecasting module.
Adheres to BaseForecaster interface while preserving strict data validations.
"""
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import warnings

from .enums import Granularity
from .base_model import BaseForecaster
from .utils.setup_logging import setup_logging

warnings.filterwarnings("ignore")

class ProphetForecaster(BaseForecaster):

    def _validate_and_filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """SRP: Preserved legacy validation and dynamic filtering logic."""
        if df is None or df.empty:
            raise ValueError("The provided dataset is empty and contains no historical spend data.")

        # 1. Dynamic Column Validation
        if self.granularity == Granularity.MONTHLY and ('month' not in df.columns or 'spend' not in df.columns):
            raise ValueError("DataFrame for monthly granularity must contain 'month' and 'spend' columns.")
        elif self.granularity == Granularity.DAILY and ('date' not in df.columns or 'spend' not in df.columns):
            raise ValueError("DataFrame for daily granularity must contain 'date' and 'spend' columns.")

        # 2. Dynamic Filtering using kwargs passed to the BaseForecaster
        data = df.copy()
        filter_mapping = {
            'account_name': 'account_name',
            'service_name': 'service_name',
            'bu_code': 'bu_code',
            'segment_name': 'segment'
        }

        for kwarg_key, df_column in filter_mapping.items():
            val = self.kwargs.get(kwarg_key)
            if val is not None:
                data = data[data[df_column] == val]

        # 3. Final Safety Check
        if data.empty:
            raise ValueError("The selected combination of filters resulted in an empty dataset. Cannot generate forecast.")

        return data

    def run(self, df: pd.DataFrame):
        """Main execution pipeline overriding the BaseForecaster abstract method."""
        if self.logger is None:
            self.logger = setup_logging()

        # Extract hyperparameters with safe defaults
        seasonality = self.hyperparameters.get("seasonality_mode", "additive")
        cps = self.hyperparameters.get("changepoint_prior_scale", 0.05)
        country_holidays = self.hyperparameters.get("holidays", None)

        # 1. Prepare Data (Custom Strict Validation)
        data = self._validate_and_filter_data(df)
        if self.logger:
            self.logger.info(f"Dataset prepared successfully. Shape: {data.shape}")

        # 2. Standardize & Aggregate (Inherited from BaseForecaster)
        clean_df = self._standardize_and_aggregate(data)

        # 3. Prophet Specific Formatting
        prophet_df = clean_df.rename(columns={"date": "ds", "spend": "y"}).dropna(subset=['ds'])
        last_date = prophet_df['ds'].max()

        # 4. Model Training
        m = Prophet(
            seasonality_mode=seasonality,
            changepoint_prior_scale=float(cps)
        )
        if country_holidays:
            m.add_country_holidays(country_name=country_holidays)

        gran_str = self.granularity.value if hasattr(self.granularity, 'value') else str(self.granularity).lower()
        if self.logger:
            self.logger.info(f"Fitting Prophet model for {gran_str} granularity. Rows: {len(prophet_df)}")

        m.fit(prophet_df)

        # 5. Cross Validation Metrics
        error_metrics = {"rmse": 0, "mse": 0, "mae": 0, "mape": 0}
        try:
            if self.logger:
                self.logger.info("Starting historical cross-validation for metrics...")

            df_cv = cross_validation(m, initial='180 days', period='30 days', horizon='90 days')
            df_p = performance_metrics(df_cv)

            error_metrics.update({
                "rmse": float(df_p['rmse'].mean()),
                "mse": float(df_p['mse'].mean()),
                "mae": float(df_p['mae'].mean()),
                "mape": float(df_p['mape'].mean()),
            })

            if self.logger:
                self.logger.info(f"Metrics calculated successfully: RMSE={error_metrics['rmse']:.2f}")

        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not calculate metrics (likely insufficient historical data): {e}")

        # 6. Forecasting
        # Utilizing self.periods and self.freq defined in BaseForecaster
        prophet_freq = 'D' if self.is_daily else 'MS'
        future = m.make_future_dataframe(periods=self.periods, freq=prophet_freq)
        forecast_full = m.predict(future)
        forecast_future = forecast_full[forecast_full['ds'] > last_date]

        # 7. Formatting Output
        # Rename 'ds' to 'date' and 'yhat' to 'forecast' to match the universal frontend contract
        forecast = forecast_future[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].rename(
            columns={'ds': 'date', 'yhat': 'forecast'}
        )

        # 8. Calculate unified metrics dictionary using the inherited method
        final_metrics = self._calculate_base_metrics(forecast, error_metrics)

        return forecast, clean_df, final_metrics