from abc import abstractmethod

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error
from .base_model import BaseForecaster


class TreeForecaster(BaseForecaster):
    """Handles feature engineering and iterative forecasting for all tree-based models."""

    def _create_features(self, df: pd.DataFrame, lags=3) -> pd.DataFrame:
        df = df.copy()
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['dayofweek'] = df['date'].dt.dayofweek
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)

        for i in range(1, lags + 1):
            df[f'lag_{i}'] = df['spend'].shift(i)
        return df

    def _get_metrics(self, y_true, y_pred) -> dict:
        return {
            'mape': float(mean_absolute_percentage_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mse': float(mean_squared_error(y_true, y_pred)),
            'mae': float(mean_absolute_error(y_true, y_pred))
        }

    @abstractmethod
    def _fit_model(self, X_train, y_train, cat_features):
        """Implemented by specific tree models (XGB/Cat)"""
        pass

    @abstractmethod
    def _format_categorical(self, df, cat_features):
        """CatBoost needs strings, XGBoost needs categories"""
        pass

    def run(self, df: pd.DataFrame):
        # Filter the data FIRST using the inherited base method
        data = self._validate_and_filter_data(df)
        # 1. Prepare Data
        df_clean = self._standardize_and_aggregate(data)
        df_features = self._create_features(df_clean)
        train_df = df_features.dropna(subset=['spend', 'lag_1', 'lag_2', 'lag_3']).copy()

        feature_cols = [col for col in train_df.columns if col not in ['date', 'spend']]

        # 2. Handle Categoricals
        cat_features = [col for col in feature_cols if
                        train_df[col].dtype == 'object' or pd.api.types.is_string_dtype(train_df[col])]
        train_df = self._format_categorical(train_df, cat_features)

        X_train = train_df[feature_cols]
        y_train = train_df['spend']

        # 3. Fit Model (Delegated to subclass)
        split_idx = int(len(X_train) * 0.85)  # Keep last 15% for validation

        X_train_split = X_train.iloc[:split_idx]
        y_train_split = y_train.iloc[:split_idx]

        X_val_split = X_train.iloc[split_idx:]
        y_val_split = y_train.iloc[split_idx:]

        self.model = self._fit_model(X_train_split, y_train_split, cat_features)

        # 4. Iterative Forecasting
        last_date = df_clean['date'].max()
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=self.periods, freq=self.freq)

        current_history = df_clean.copy()
        last_known_row = current_history.iloc[-1].copy()
        future_records = []

        for f_date in future_dates:
            new_row = last_known_row.copy()
            new_row['date'] = f_date
            new_row['spend'] = np.nan
            current_history.loc[len(current_history)] = new_row

            temp_features = self._create_features(current_history)
            X_pred = temp_features.iloc[-1:][feature_cols].copy()
            X_pred = self._format_categorical(X_pred, cat_features)

            pred_val = max(0.0, float(self.model.predict(X_pred)[0]))

            future_records.append({'date': f_date, 'forecast': pred_val})
            current_history.loc[len(current_history) - 1, 'spend'] = pred_val

        forecast_df = pd.DataFrame(future_records)

        # 5. Metrics (Score on the 15% holdout, NOT the training data!)
        val_preds = self.model.predict(X_val_split)

        # Now Optuna receives a true out-of-sample RMSE to minimize
        error_metrics = self._get_metrics(y_val_split, val_preds)
        final_metrics = self._calculate_base_metrics(forecast_df, error_metrics)

        return forecast_df, df_clean, final_metrics