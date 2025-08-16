import os
import pandas as pd
import numpy as np
import optuna
from sklearn.model_selection import train_test_split
from catboost import CatBoostRegressor, Pool
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib    

# -------------------
# PARAMETERS
# -------------------
TRAIN = False  # Set to False to skip training and load the model directly
BAYESIAN_OPTIMIZATION = True  # Set to True to use Optuna for hyperparameter tuning
GRID_SEARCH_OPTIMIZATION = False  # Set to True to use GridSearchCV for hyperparameter tuning
FORCE_RETRAIN = False  # Set to True to always retrain even if model exists
KEEP_MODEL_HISTORY = 5  # Number of recent models to keep
USE_LINEAR_REGRESSION = True  # Set to True to also train and compare Linear Regression

# Create model directories if they don't exist
import os
models_dir = 'models'
catboost_dir = os.path.join(models_dir, 'catboost')
linear_regression_dir = os.path.join(models_dir, 'linear_regression')

os.makedirs(catboost_dir, exist_ok=True)
os.makedirs(linear_regression_dir, exist_ok=True)

# Add timestamp to model filenames for versioning
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH_GRID_SEARCH = os.path.join(catboost_dir, f"catboost_gridsearch_model_{timestamp}.cbm")  # Path to save/load the CatBoost model
MODEL_PATH_BAYESIAN_OPTIMIZATION = os.path.join(catboost_dir, f"catboost_bayesian_model_{timestamp}.cbm")  # Path to save/load the CatBoost model
LINEAR_REGRESSION_MODEL_PATH = os.path.join(linear_regression_dir, f"linear_regression_model_{timestamp}.pkl")  # Path to save/load the Linear Regression model
LINEAR_REGRESSION_SCALER_PATH = os.path.join(linear_regression_dir, f"linear_regression_scaler_{timestamp}.pkl")  # Path to save/load the scaler
# -------------------
# -------------------

def objective(trial):
    params = {
        'depth': trial.suggest_int('depth', 4, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'l2_leaf_reg': trial.suggest_int('l2_leaf_reg', 1, 10),
        'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
        'iterations': 1000,
        'loss_function': 'RMSE',
        'random_seed': 42,
        'verbose': 0
    }
    
    model = CatBoostRegressor(**params, cat_features=categorical_cols)
    
    # Time series split
    tscv = TimeSeriesSplit(n_splits=3)
    rmse_scores = []
    
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        rmse_scores.append(rmse)
        
    return np.mean(rmse_scores)

# -------------------
# 1. Prepare the data
# -------------------
# Data loading
df = pd.read_csv('actual_detail_2025-08-14.csv')

# Convert 'month' column to datetime and extract year and month number
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
df['year'] = df['month'].dt.year
df['month_num'] = df['month'].dt.month

# Sort columns base on 'month' (datetime)
df = df.sort_values('month').reset_index(drop=True)

# Drop 'estimate' column (it's same as 'spend') if it exists
if 'estimate' in df.columns:
    df.drop(columns=['estimate'], inplace=True)
    
# Convert other columns to categorical data type
categorical_cols = [
    'serviceName', 'usageFamily', 'accountName', 'accountID',
    'countryCode', 'buCode', 'region', 'segment', 'costString'
]
for col in categorical_cols:
    df[col] = df[col].astype('category')
    
# Drop the original 'month' column
df.drop(columns=['month'], inplace=True)

# Create lag features (use all categorical combos implicitly by grouping later if needed)
for lag in [1, 2, 3, 6, 12]:
    df[f'lag_{lag}'] = df.groupby(categorical_cols, observed=False)['spend'].shift(lag)

# Optionally create rolling statistics for extra signal
df['rolling_mean_3'] = df.groupby(categorical_cols, observed=False)['spend'].shift(1).rolling(3).mean()
df['rolling_mean_6'] = df.groupby(categorical_cols, observed=False)['spend'].shift(1).rolling(6).mean()

#display data types of all columns
print(df.dtypes)

# Divide the dataset into training and testing sets
# 80% for training and 20% for testing
# DO NOT Shuffle the data as it is time series data
train_size = int(len(df) * 0.8)  # 80% train
train_data = df.iloc[:train_size]
test_data = df.iloc[train_size:]

X = df.drop(columns=['spend'])
y = df['spend']

# Shape of the training and testing datasets
print('Shape of training data :',train_data.shape)
print('Shape of testing data :',test_data.shape)

# Define the features and target variable
X_train = train_data.drop(columns=['spend'])
y_train = train_data['spend']
X_test  = test_data.drop(columns=['spend'])
y_test  = test_data['spend']

# Function to find the most recent model file
def find_latest_model(model_pattern, search_dir=None):
    import glob
    if search_dir:
        # Search in specific directory
        search_path = os.path.join(search_dir, model_pattern)
    else:
        # Search in current directory (for backward compatibility)
        search_path = model_pattern
    
    models = glob.glob(search_path)
    if models:
        # Sort by modification time (newest first)
        models.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return models[0]
    return None

# Function to clean up old models
def cleanup_old_models():
    import glob
    # Find all model files in their respective directories
    grid_search_models = glob.glob(os.path.join(catboost_dir, "catboost_gridsearch_model_*.cbm"))
    bayesian_models = glob.glob(os.path.join(catboost_dir, "catboost_bayesian_model_*.cbm"))
    linear_regression_models = glob.glob(os.path.join(linear_regression_dir, "linear_regression_model_*.pkl"))
    linear_regression_scalers = glob.glob(os.path.join(linear_regression_dir, "linear_regression_scaler_*.pkl"))
    
    # Sort by modification time (newest first) and keep only the KEEP_MODEL_HISTORY most recent
    for model_list in [grid_search_models, bayesian_models, linear_regression_models, linear_regression_scalers]:
        if len(model_list) > KEEP_MODEL_HISTORY:
            model_list.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            for old_model in model_list[KEEP_MODEL_HISTORY:]:
                os.remove(old_model)
                print(f"Cleaned up old model: {old_model}")

# Function to list available models
def list_available_models():
    import glob
    grid_search_models = glob.glob(os.path.join(catboost_dir, "catboost_gridsearch_model_*.cbm"))
    bayesian_models = glob.glob(os.path.join(catboost_dir, "catboost_bayesian_model_*.cbm"))
    linear_regression_models = glob.glob(os.path.join(linear_regression_dir, "linear_regression_model_*.pkl"))
    linear_regression_scalers = glob.glob(os.path.join(linear_regression_dir, "linear_regression_scaler_*.pkl"))
    
    print(f"\nAvailable models:")
    print(f"Grid Search models: {len(grid_search_models)}")
    for model in sorted(grid_search_models, reverse=True):
        print(f"  - {model}")
    print(f"Bayesian models: {len(bayesian_models)}")
    for model in sorted(bayesian_models, reverse=True):
        print(f"  - {model}")
    print(f"Linear Regression models: {len(linear_regression_models)}")
    for model in sorted(linear_regression_models, reverse=True):
        print(f"  - {model}")
    print(f"Linear Regression scalers: {len(linear_regression_scalers)}")
    for scaler in sorted(linear_regression_scalers, reverse=True):
        print(f"  - {scaler}")

# Function to prepare data for Linear Regression (one-hot encode categorical variables)
def prepare_data_for_linear_regression(df, categorical_cols):
    """Prepare data for Linear Regression by one-hot encoding categorical variables"""
    # Create a copy to avoid modifying the original dataframe
    df_lr = df.copy()
    
    # One-hot encode categorical variables
    for col in categorical_cols:
        if col in df_lr.columns:
            # Create dummy variables
            dummies = pd.get_dummies(df_lr[col], prefix=col, drop_first=True)
            # Drop the original categorical column
            df_lr = df_lr.drop(columns=[col])
            # Add the dummy variables
            df_lr = pd.concat([df_lr, dummies], axis=1)
    
    # Handle NaN values - fill with 0 for lag features and mean for other numeric features
    for col in df_lr.columns:
        if col.startswith('lag_') or col.startswith('rolling_mean_'):
            df_lr[col] = df_lr[col].fillna(0)
        elif df_lr[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            df_lr[col] = df_lr[col].fillna(df_lr[col].mean())
    
    return df_lr

# Check if we should train or load existing model
should_train = TRAIN
model_loaded = False
linear_regression_loaded = False

if not TRAIN:
    # Try to load existing model based on optimization type
    if BAYESIAN_OPTIMIZATION:
        latest_model = find_latest_model("catboost_bayesian_model_*.cbm", catboost_dir)
        if latest_model:
            model = CatBoostRegressor()
            model.load_model(latest_model)
            print(f"Loaded existing Bayesian model: {latest_model}")
            model_loaded = True
        else:
            print("No existing Bayesian model found. Starting training...")
            should_train = True
    
    elif GRID_SEARCH_OPTIMIZATION:
        latest_model = find_latest_model("catboost_gridsearch_model_*.cbm", catboost_dir)
        if latest_model:
            model = CatBoostRegressor()
            model.load_model(latest_model)
            print(f"Loaded existing Grid Search model: {latest_model}")
            model_loaded = True
        else:
            print("No existing Grid Search model found. Starting training...")
            should_train = True
    
    # Try to load Linear Regression model if enabled
    if USE_LINEAR_REGRESSION:
        latest_lr_model = find_latest_model("linear_regression_model_*.pkl", linear_regression_dir)
        latest_lr_scaler = find_latest_model("linear_regression_scaler_*.pkl", linear_regression_dir)
        if latest_lr_model and latest_lr_scaler:
            linear_regression_model = joblib.load(latest_lr_model)
            linear_regression_scaler = joblib.load(latest_lr_scaler)
            print(f"Loaded existing Linear Regression model: {latest_lr_model}")
            linear_regression_loaded = True
        else:
            print("No existing Linear Regression model found. Will train new one...")
            should_train = True

if should_train:
    # Clean up old models and prepare for training
    cleanup_old_models()
    print(f"Training new model with timestamp: {timestamp}")
    list_available_models()
    
    # -------------------
    # 2. Train the CatBoost model
    # -------------------
    if BAYESIAN_OPTIMIZATION:
        # Use Optuna for hyperparameter tuning
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=50)  # 30 trials, can increase for better search

        print("Best Parameters: ", study.best_params)
        print("Best RMSE: ", study.best_value)
        
        best_params = study.best_params
        best_params.update({
            'iterations': 1000,
            'loss_function': 'RMSE',
            'random_seed': 42,
            'verbose': 200
        })

        model = CatBoostRegressor(**best_params, cat_features=categorical_cols)
        model.fit(X, y)
        model.save_model(MODEL_PATH_BAYESIAN_OPTIMIZATION)
        print("Model saved to", MODEL_PATH_BAYESIAN_OPTIMIZATION)
        
    else:
            # Use GridSearchCV for hyperparameter tuning

        model = CatBoostRegressor(
                loss_function='RMSE',
                cat_features=categorical_cols,
                random_seed=42,
                verbose=3
            )
        
        grid = {
            'depth': [3, 6, 8, 10, 12],
            'learning_rate': [0.01, 0.05, 0.1],
            'iterations': [200, 500, 800, 1000],
            'bootstrap_type': ['Bayesian', 'Bernoulli'],
            'l2_leaf_reg': [1, 3, 5]
        }
        
        # Use GridSearchCV to find the best hyperparameters
        grid_search_result = model.grid_search(
            grid,
            X_train,
            y_train,
            cv=3,                  # 3-fold cross-validation
            plot=False             # set True to plot learning curves
        )

        model.fit(X_train, y_train)
        model.save_model(MODEL_PATH_GRID_SEARCH)
        print("Model saved to", MODEL_PATH_GRID_SEARCH)
    
    # -------------------
    # 3. Train Linear Regression model (if enabled)
    # -------------------
    if USE_LINEAR_REGRESSION:
        print("\n" + "="*50)
        print("Training Linear Regression Model")
        print("="*50)
        
        # Prepare data for Linear Regression (one-hot encode categorical variables)
        X_train_lr = prepare_data_for_linear_regression(X_train, categorical_cols)
        X_test_lr = prepare_data_for_linear_regression(X_test, categorical_cols)
        
        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_lr)
        X_test_scaled = scaler.transform(X_test_lr)
        
        # Train Linear Regression model
        linear_regression_model = LinearRegression()
        linear_regression_model.fit(X_train_scaled, y_train)
        
        # Save the model and scaler
        joblib.dump(linear_regression_model, LINEAR_REGRESSION_MODEL_PATH)
        joblib.dump(scaler, LINEAR_REGRESSION_SCALER_PATH)
        print(f"Linear Regression model saved to {LINEAR_REGRESSION_MODEL_PATH}")
        print(f"Scaler saved to {LINEAR_REGRESSION_SCALER_PATH}")
        
        # Make predictions with Linear Regression
        y_pred_lr = linear_regression_model.predict(X_test_scaled)
        
        # Calculate metrics for Linear Regression
        rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
        mae_lr = mean_absolute_error(y_test, y_pred_lr)
        r2_lr = r2_score(y_test, y_pred_lr)
        
        print(f"\nLinear Regression Results:")
        print(f"RMSE: {rmse_lr:.4f}")
        print(f"MAE: {mae_lr:.4f}")
        print(f"R²: {r2_lr:.4f}")
        
        linear_regression_loaded = True

# Predictions
y_pred = model.predict(X_test)

# Metrics for CatBoost
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n" + "="*50)
print("CatBoost Model Results:")
print("="*50)
print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")

# Linear Regression predictions and metrics (if model is loaded)
if linear_regression_loaded:
    # Prepare test data for Linear Regression
    X_test_lr = prepare_data_for_linear_regression(X_test, categorical_cols)
    # Load the scaler if not already loaded
    if 'linear_regression_scaler' not in locals():
        latest_scaler = find_latest_model("linear_regression_scaler_*.pkl", linear_regression_dir)
        if latest_scaler:
            linear_regression_scaler = joblib.load(latest_scaler)
    X_test_scaled = linear_regression_scaler.transform(X_test_lr)
    y_pred_lr = linear_regression_model.predict(X_test_scaled)
    
    # Calculate metrics for Linear Regression
    rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
    mae_lr = mean_absolute_error(y_test, y_pred_lr)
    r2_lr = r2_score(y_test, y_pred_lr)
    
    print(f"\n" + "="*50)
    print("Linear Regression Model Results:")
    print("="*50)
    print(f"RMSE: {rmse_lr:.4f}")
    print(f"MAE: {mae_lr:.4f}")
    print(f"R²: {r2_lr:.4f}")
    
    # Model comparison
    print(f"\n" + "="*50)
    print("Model Comparison:")
    print("="*50)
    print(f"{'Metric':<15} {'CatBoost':<15} {'Linear Regression':<20} {'Winner':<10}")
    print("-" * 60)
    print(f"{'RMSE':<15} {rmse:<15.4f} {rmse_lr:<20.4f} {'CatBoost' if rmse < rmse_lr else 'Linear Regression'}")
    print(f"{'MAE':<15} {mae:<15.4f} {mae_lr:<20.4f} {'CatBoost' if mae < mae_lr else 'Linear Regression'}")
    print(f"{'R²':<15} {r2:<15.4f} {r2_lr:<20.4f} {'CatBoost' if r2 > r2_lr else 'Linear Regression'}")
    
    # Store predictions for plotting
    y_pred_lr_final = y_pred_lr
else:
    y_pred_lr_final = None

# ----------------------------
# Monthly Actual vs Predicted Bar Plot
# ----------------------------

# Add predictions to the test dataset
test_data = test_data.copy()
test_data['predicted_spend_catboost'] = y_pred

# Add Linear Regression predictions if available
if y_pred_lr_final is not None:
    test_data['predicted_spend_lr'] = y_pred_lr_final

# Recreate a proper year_month column
# (since we dropped the original 'month' earlier)
test_data['year_month'] = pd.to_datetime(
    test_data['year'].astype(str) + '-' + test_data['month_num'].astype(str) + '-01'
)

# Aggregate by month
if y_pred_lr_final is not None:
    monthly_compare = (
        test_data.groupby('year_month')[['spend', 'predicted_spend_catboost', 'predicted_spend_lr']]
        .mean()
        .reset_index()
    )
else:
    monthly_compare = (
        test_data.groupby('year_month')[['spend', 'predicted_spend_catboost']]
        .mean()
        .reset_index()
    )

# Plot grouped bar chart
if y_pred_lr_final is not None:
    # Plot with both models
    ax = monthly_compare.plot(
        x='year_month',
        y=['spend', 'predicted_spend_catboost', 'predicted_spend_lr'],
        kind='bar',
        figsize=(15, 7),
        width=0.8
    )
    plt.title("Actual vs Predicted Monthly Spend (CatBoost vs Linear Regression)", fontsize=16)
    plt.legend(["Actual", "CatBoost", "Linear Regression"])
else:
    # Plot with only CatBoost
    ax = monthly_compare.plot(
        x='year_month',
        y=['spend', 'predicted_spend_catboost'],
        kind='bar',
        figsize=(12, 6),
        width=0.8
    )
    plt.title("Actual vs Predicted Monthly Spend (CatBoost)", fontsize=16)
    plt.legend(["Actual", "CatBoost"])

plt.xlabel("Month")
plt.ylabel("Spend (USD)")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# ----------------------------
# Monthly Actual vs Predicted Line Graph
# ----------------------------
plt.figure(figsize=(15, 7))
plt.plot(monthly_compare['year_month'], monthly_compare['spend'], marker='o', linewidth=2, label='Actual Spend', color='black')

if y_pred_lr_final is not None:
    plt.plot(monthly_compare['year_month'], monthly_compare['predicted_spend_catboost'], marker='s', linewidth=2, label='CatBoost Prediction', color='blue')
    plt.plot(monthly_compare['year_month'], monthly_compare['predicted_spend_lr'], marker='^', linewidth=2, label='Linear Regression Prediction', color='red')
    plt.title("Actual vs Predicted Monthly Spend (CatBoost vs Linear Regression)", fontsize=16)
else:
    plt.plot(monthly_compare['year_month'], monthly_compare['predicted_spend_catboost'], marker='s', linewidth=2, label='CatBoost Prediction', color='blue')
    plt.title("Actual vs Predicted Monthly Spend (CatBoost)", fontsize=16)

plt.xlabel("Month")
plt.ylabel("Spend (USD)")
plt.xticks(rotation=45)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()

#Basic Catboost - 1000 iterations
# RMSE: 47.2365
# MAE: 15.5730
# R²: 0.8414

#iterations/100
#RMSE: 89.3153
#MAE: 43.2676
#R²: 0.4328

#CatBoost with GridSearchCV
# RMSE: 42.8212
# MAE: 14.8235
# R²: 0.8696


# -------------------
# Future Predictions
# -------------------
from datetime import datetime, timedelta

def preprocess_future_df(future_df):
    # Convert 'month' to datetime
    future_df['month'] = pd.to_datetime(future_df['month'], format='%Y-%m')
    # Extract year and month number
    future_df['year'] = future_df['month'].dt.year
    future_df['month_num'] = future_df['month'].dt.month
    # Drop the original 'month' column
    future_df.drop(columns=['month'], inplace=True)
    
    # Ensure all categorical columns exist and fill with a string if missing
    for col in categorical_cols:
        if col not in future_df.columns:
            future_df[col] = 'default'
        future_df[col] = future_df[col].fillna('default').astype('category')
    
    # Create all lag features that were used in training
    for lag in [1, 2, 3, 6, 12]:
        future_df[f'lag_{lag}'] = df['spend'].iloc[-lag] if len(df) >= lag else df['spend'].iloc[-1]
    
    # Create rolling statistics features
    future_df['rolling_mean_3'] = df['spend'].iloc[-3:].mean() if len(df) >= 3 else df['spend'].iloc[-1]
    future_df['rolling_mean_6'] = df['spend'].iloc[-6:].mean() if len(df) >= 6 else df['spend'].iloc[-1]
    
    # Ensure the future_df has the same column order as the training data
    # Get the expected columns from the training data (excluding 'spend')
    expected_columns = [col for col in df.columns if col != 'spend']
    future_df = future_df[expected_columns]
        
    return future_df

# Define the start and end dates for future predictions
start_date = datetime(2025, 8, 1)

#Generate a list of 24 months from start date
month_range = pd.date_range(start=start_date, periods=24, freq='MS').strftime("%Y-%m").tolist()

#Create a DataFrame with month column
future_df = pd.DataFrame({'month': month_range})
future_df = preprocess_future_df(future_df)

#predict future spend
future_pred = model.predict(future_df)

# Linear Regression future predictions (if model is loaded)
if linear_regression_loaded:
    # Prepare future data for Linear Regression
    future_df_lr = prepare_data_for_linear_regression(future_df, categorical_cols)
    
    # Ensure the future data has the same columns as training data
    # Get the expected columns from the training data
    X_train_lr = prepare_data_for_linear_regression(X_train, categorical_cols)
    expected_columns = X_train_lr.columns.tolist()
    
    # Add missing columns with 0 values
    for col in expected_columns:
        if col not in future_df_lr.columns:
            future_df_lr[col] = 0
    
    # Reorder columns to match training data
    future_df_lr = future_df_lr[expected_columns]
    
    future_df_scaled = linear_regression_scaler.transform(future_df_lr)
    future_pred_lr = linear_regression_model.predict(future_df_scaled)

# Create month labels for plotting
month_labels = pd.date_range(start=start_date, periods=24, freq='MS').strftime("%Y-%m")

# Create a comprehensive future predictions comparison
plt.figure(figsize=(18, 10))

# Create subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 12))

# Plot 1: Line graph comparison
if linear_regression_loaded:
    ax1.plot(range(len(future_pred)), future_pred, marker='s', linewidth=3, label='CatBoost Prediction', color='blue', markersize=6)
    ax1.plot(range(len(future_pred_lr)), future_pred_lr, marker='^', linewidth=3, label='Linear Regression Prediction', color='red', markersize=6)
    ax1.set_title("24-Month Future Spend Predictions: CatBoost vs Linear Regression", fontsize=16, fontweight='bold')
else:
    ax1.plot(range(len(future_pred)), future_pred, marker='o', linewidth=3, label='CatBoost Prediction', color='blue', markersize=6)
    ax1.set_title("24-Month Future Spend Predictions: CatBoost", fontsize=16, fontweight='bold')

ax1.set_xlabel("Month", fontsize=12)
ax1.set_ylabel("Predicted Spend (USD)", fontsize=12)
ax1.set_xticks(range(len(month_labels)))
ax1.set_xticklabels(month_labels, rotation=45)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.legend(fontsize=12)
ax1.tick_params(axis='both', which='major', labelsize=10)

# Plot 2: Bar chart comparison
if linear_regression_loaded:
    x = np.arange(len(future_pred))
    width = 0.35
    
    ax2.bar(x - width/2, future_pred, width, label='CatBoost', color='blue', alpha=0.7)
    ax2.bar(x + width/2, future_pred_lr, width, label='Linear Regression', color='red', alpha=0.7)
    ax2.set_title("24-Month Future Spend Predictions: Bar Chart Comparison", fontsize=16, fontweight='bold')
else:
    ax2.bar(range(len(future_pred)), future_pred, color='blue', alpha=0.7, label='CatBoost')
    ax2.set_title("24-Month Future Spend Predictions: Bar Chart", fontsize=16, fontweight='bold')

ax2.set_xlabel("Month", fontsize=12)
ax2.set_ylabel("Predicted Spend (USD)", fontsize=12)
ax2.set_xticks(range(len(month_labels)))
ax2.set_xticklabels(month_labels, rotation=45)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.legend(fontsize=12)
ax2.tick_params(axis='both', which='major', labelsize=10)

plt.tight_layout()
plt.show()

# Print detailed future predictions comparison
print("\n" + "="*80)
print("24-MONTH FUTURE PREDICTIONS COMPARISON")
print("="*80)

if linear_regression_loaded:
    print(f"{'Month':<12} {'CatBoost':<15} {'Linear Regression':<20} {'Difference':<15} {'% Difference':<15}")
    print("-" * 80)
    
    for i, (month, cat_pred, lr_pred) in enumerate(zip(month_labels, future_pred, future_pred_lr)):
        diff = cat_pred - lr_pred
        pct_diff = (diff / lr_pred) * 100 if lr_pred != 0 else 0
        print(f"{month:<12} ${cat_pred:<14.2f} ${lr_pred:<19.2f} ${diff:<14.2f} {pct_diff:<14.1f}%")
    
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"CatBoost Average Prediction: ${np.mean(future_pred):.2f}")
    print(f"Linear Regression Average Prediction: ${np.mean(future_pred_lr):.2f}")
    print(f"Average Difference: ${np.mean(future_pred - future_pred_lr):.2f}")
    print(f"Average % Difference: {np.mean((future_pred - future_pred_lr) / future_pred_lr) * 100:.1f}%")
    print(f"CatBoost Prediction Range: ${np.min(future_pred):.2f} - ${np.max(future_pred):.2f}")
    print(f"Linear Regression Prediction Range: ${np.min(future_pred_lr):.2f} - ${np.max(future_pred_lr):.2f}")
else:
    print(f"{'Month':<12} {'CatBoost Prediction':<20}")
    print("-" * 35)
    for month, pred in zip(month_labels, future_pred):
        print(f"{month:<12} ${pred:<19.2f}")
    
    print(f"\nAverage Prediction: ${np.mean(future_pred):.2f}")
    print(f"Prediction Range: ${np.min(future_pred):.2f} - ${np.max(future_pred):.2f}")

    
# Model saved to catboost_gridsearch_model_20250815_184243.cbm
# RMSE: 38.6532
# MAE: 8.0275
# R²: 0.9372
    