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

# -------------------
# PARAMETERS
# -------------------
TRAIN = True  # Set to False to skip training and load the model directly
BAYESIAN_OPTIMIZATION = True  # Set to True to use Optuna for hyperparameter tuning
GRID_SEARCH_OPTIMIZATION = False  # Set to True to use GridSearchCV for hyperparameter tuning

# Add timestamp to model filenames for versioning
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH_GRID_SEARCH = f"catboost_gridsearch_model_{timestamp}.cbm"  # Path to save/load the CatBoost model
MODEL_PATH_BAYESIAN_OPTIMIZATION = f"catboost_bayesian_model_{timestamp}.cbm"  # Path to save/load the CatBoost model
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

# Remove existing model files if TRAIN is True
if TRAIN:
    # Clean up old model files (keep only the 5 most recent)
    def cleanup_old_models():
        import glob
        # Find all model files
        grid_search_models = glob.glob("catboost_gridsearch_model_*.cbm")
        bayesian_models = glob.glob("catboost_bayesian_model_*.cbm")
        
        # Sort by modification time (newest first) and keep only the 5 most recent
        for model_list in [grid_search_models, bayesian_models]:
            if len(model_list) > 5:
                model_list.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                for old_model in model_list[5:]:
                    os.remove(old_model)
                    print(f"Cleaned up old model: {old_model}")
    
    cleanup_old_models()
    print(f"Training new model with timestamp: {timestamp}")

if not TRAIN and (os.path.exists(MODEL_PATH_GRID_SEARCH) or os.path.exists(MODEL_PATH_BAYESIAN_OPTIMIZATION)):
    # Load the pre-trained CatBoost model
    model = CatBoostRegressor()
    if GRID_SEARCH_OPTIMIZATION:
        model.load_model(MODEL_PATH_BAYESIAN_OPTIMIZATION)
    elif MODEL_PATH_BAYESIAN_OPTIMIZATION:
        model.load_model(MODEL_PATH_BAYESIAN_OPTIMIZATION)
    print("Model loaded")
else:
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

# Predictions
y_pred = model.predict(X_test)

# Metrics
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")

# ----------------------------
# Monthly Actual vs Predicted Bar Plot
# ----------------------------

# Add predictions to the test dataset
test_data = test_data.copy()
test_data['predicted_spend'] = y_pred

# Recreate a proper year_month column
# (since we dropped the original 'month' earlier)
test_data['year_month'] = pd.to_datetime(
    test_data['year'].astype(str) + '-' + test_data['month_num'].astype(str) + '-01'
)

# Aggregate by month
monthly_compare = (
    test_data.groupby('year_month')[['spend', 'predicted_spend']]
    .mean()
    .reset_index()
)

# Plot grouped bar chart
monthly_compare.plot(
    x='year_month',
    kind='bar',
    figsize=(12, 6),
    width=0.8
)
plt.title("Actual vs Predicted Monthly Spend", fontsize=16)
plt.xlabel("Month")
plt.ylabel("Spend (USD)")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend(["Actual", "Predicted"])
plt.show()

# ----------------------------
# Monthly Actual vs Predicted Line Graph
# ----------------------------
plt.figure(figsize=(12, 6))
plt.plot(monthly_compare['year_month'], monthly_compare['spend'], marker='o', label='Actual Spend')
plt.plot(monthly_compare['year_month'], monthly_compare['predicted_spend'], marker='o', label='Predicted Spend')

plt.title("Actual vs Predicted Monthly Spend", fontsize=16)
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

# Create month labels for plotting
month_labels = pd.date_range(start=start_date, periods=24, freq='MS').strftime("%Y-%m")

#visualize future predictions with a line graph
plt.figure(figsize=(12, 6))
plt.plot(range(len(future_pred)), future_pred, marker='o', label='Predicted Future Spend')
plt.title("Future Monthly Spend Predictions", fontsize=16)
plt.xlabel("Month")
plt.ylabel("Predicted Spend (USD)")
plt.xticks(range(len(month_labels)), month_labels, rotation=45)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend()
plt.tight_layout()
plt.show()

    
    