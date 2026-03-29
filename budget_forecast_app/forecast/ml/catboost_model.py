import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error


def create_time_series_features(df, target_col='spend', lags=3):
    """
    Extracts time-based features and historical lags from the date column.
    """
    df = df.copy()

    # --- Convert the date column to datetime objects ---
    df['date'] = pd.to_datetime(df['date'])

    # 1. Date Component Features
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)

    # 2. Lag Features (e.g., lag_1 = spend from previous row)
    for i in range(1, lags + 1):
        df[f'lag_{i}'] = df[target_col].shift(i)

    return df


def run_catboost_forecast(df, granularity, logger=None, hyperparameters=None, **kwargs):
    """
    Main execution pipeline for CatBoost matching the orchestration signature.
    Assumes df has 'date' and 'spend' columns.
    """
    if hyperparameters is None:
        hyperparameters = {}

    # Extract string value safely
    gran_str = granularity.value if hasattr(granularity, 'value') else str(granularity).lower()

    if logger:
        logger.info(f"Starting XGBoost forecast with granularity: {gran_str}")

    # --- Standardize Date Column & Handle Enum ---
    is_daily = gran_str == 'daily'
    date_col = 'date' if is_daily else 'month'

    # If the date is hiding in the Index, bring it back to a column first
    if df.index.name in ['date', 'month', 'Month']:
        df = df.reset_index()

    # Rename whatever date variant we found to 'date'
    if date_col in df.columns:
        df = df.rename(columns={date_col: 'date'})
    elif 'month' in df.columns:  # Fallback if granularity is daily but only month exists
        df = df.rename(columns={'month': 'date'})
    elif 'Month' in df.columns:
        df = df.rename(columns={'Month': 'date'})

    # Final Catch: If we still don't have a 'date' column, we can't proceed
    if 'date' not in df.columns:
        raise KeyError(f"Expected a 'date' or 'month' column, but found: {df.columns.tolist()}")

    # 2. PROCEED WITH AGGREGATION
    df['date'] = pd.to_datetime(df['date'])
    df['spend'] = pd.to_numeric(df['spend'], errors='coerce').fillna(0)

    # Use resample to group everything by the time period
    df = df.set_index('date').sort_index()

    if is_daily:
        df = df.resample('D')['spend'].sum().reset_index()
    else:
        df = df.resample('MS')['spend'].sum().reset_index()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    if logger:
        logger.info(f"Aggregated dataset. New shape: {df.shape}")

    # --- 1. FEATURE ENGINEERING ---
    df_features = create_time_series_features(df, target_col='spend', lags=3)
    train_df = df_features.dropna(subset=['spend', 'lag_1', 'lag_2', 'lag_3']).copy()

    # Define feature columns (everything except the raw date and target)
    feature_cols = [col for col in train_df.columns if col not in ['date', 'spend']]

    X_train = train_df[feature_cols]
    y_train = train_df['spend']

    # --- 2. IDENTIFY CATEGORICAL FEATURES ---
    # CatBoost handles categories beautifully, but needs to know which columns they are.
    # It requires categorical data to be passed as strings.
    cat_features = []
    for col in feature_cols:
        # Bulletproof check for ANY text-like or categorical column
        is_text = pd.api.types.is_string_dtype(train_df[col])
        is_object = pd.api.types.is_object_dtype(train_df[col])
        is_cat = isinstance(train_df[col].dtype, pd.CategoricalDtype)

        if is_text or is_object or is_cat:
            cat_features.append(col)
            # CatBoost prefers categories to be cast to strings. Fill NaNs to prevent errors.
            train_df[col] = train_df[col].fillna('Unknown').astype(str)

    # --- 3. HYPERPARAMETER MAPPING ---
    # CatBoost uses slightly different naming conventions than XGBoost
    iterations = int(hyperparameters.get('n_estimators', 100))
    learning_rate = float(hyperparameters.get('learning_rate', 0.1))
    depth = int(hyperparameters.get('max_depth', 6))

    # --- 4. MODEL TRAINING ---
    model = CatBoostRegressor(
        iterations=iterations,
        learning_rate=learning_rate,
        depth=depth,
        verbose=False
    )

    model.fit(X_train, y_train, cat_features=cat_features)

    # --- 5. FUTURE FORECASTING (ITERATIVE) ---
    periods = kwargs.get('periods', 30 if is_daily else 12)
    freq = 'D' if is_daily else 'MS'

    last_date = df['date'].max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq=freq)

    future_records = []

    # FIX: Copy the entire dataframe to preserve static categories (like account_name)
    # rather than just copying ['date', 'spend'].
    current_history = df.copy()

    # Grab the last row's static features to carry forward into the future
    last_known_row = current_history.iloc[-1].copy()

    for f_date in future_dates:
        # Create a new row carrying forward any categorical/static data
        new_row = last_known_row.copy()
        new_row['date'] = f_date
        new_row['spend'] = np.nan

        # Append placeholder row
        current_history.loc[len(current_history)] = new_row

        # Recalculate features to update the lags
        temp_features = create_time_series_features(current_history, target_col='spend', lags=3)

        # Isolate the specific row we are predicting
        X_pred = temp_features.iloc[-1:][feature_cols].copy()

        # Ensure categorical formatting applies to the prediction row as well
        for col in cat_features:
            X_pred.loc[:, col] = X_pred[col].fillna('Unknown').astype(str)

        # Predict
        pred_val = model.predict(X_pred)[0]
        # Floor the prediction at 0.0
        pred_val = max(0.0, float(pred_val))

        # Store prediction and update history so the next iteration can use it as a lag
        future_records.append({'date': f_date, 'forecast': pred_val})
        current_history.loc[len(current_history) - 1, 'spend'] = pred_val

    forecast_df = pd.DataFrame(future_records)

    # --- 6. CALCULATE METRICS ---
    train_predictions = model.predict(X_train)
    mape = mean_absolute_percentage_error(y_train, train_predictions)
    rmse = np.sqrt(mean_squared_error(y_train, train_predictions))

    metrics_dict = {
        'mape': float(mape),
        'rmse': float(rmse)
    }

    historical_df = df.copy()

    if logger:
        logger.info("CatBoost forecast completed successfully.")

    return forecast_df, historical_df, metrics_dict