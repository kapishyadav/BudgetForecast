"""
Budget Forecasting Model - Main Script
=====================================

This script implements a comprehensive budget forecasting system using CatBoost and Linear Regression models.
It includes data preprocessing, model training, hyperparameter optimization, and future predictions.

Features:
- Time series data preprocessing with lag features
- CatBoost model with Bayesian or Grid Search optimization
- Linear Regression model for comparison
- Model persistence and versioning
- Comprehensive visualization and evaluation
- Future predictions for 24 months

Author: Budget Forecast Team
Date: 2025
"""

# =============================================================================
# IMPORTS
# =============================================================================
# Standard library imports
import os
import glob
import argparse
import logging
from datetime import datetime, timedelta

# Data manipulation and analysis
import pandas as pd
import numpy as np

# Machine learning libraries
import optuna
from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib

# CatBoost specific imports
from catboost import CatBoostRegressor, Pool

# Visualization - Plotly for interactive plots
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# =============================================================================
# LOGGING SETUP
# =============================================================================
def setup_logging():
    """
    Setup logging configuration with file and console handlers.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"budget_forecast_{timestamp}.log")
    
    # Configure logging
    logger = logging.getLogger('BudgetForecast')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler (detailed logging)
    file_handler = logging.FileHandler(log_filename, mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Console handler (simplified output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger

# Initialize logger
logger = setup_logging()

# =============================================================================
# CONFIGURATION PARAMETERS
# =============================================================================
# Training Control Flags
TRAIN = False  # Set to False to skip training and load existing models
BAYESIAN_OPTIMIZATION = True  # Use Optuna for hyperparameter tuning
GRID_SEARCH_OPTIMIZATION = False  # Use GridSearchCV for hyperparameter tuning
FORCE_RETRAIN = False  # Force retraining even if models exist
USE_LINEAR_REGRESSION = False  # Train and compare Linear Regression model

# Model Management
KEEP_MODEL_HISTORY = 5  # Number of recent models to keep

# =============================================================================
# DIRECTORY SETUP
# =============================================================================
# Create model directories if they don't exist
models_dir = 'models'
catboost_dir = os.path.join(models_dir, 'catboost')
linear_regression_dir = os.path.join(models_dir, 'linear_regression')

# Create plots directory for interactive visualizations
plots_dir = 'plots'
os.makedirs(catboost_dir, exist_ok=True)
os.makedirs(linear_regression_dir, exist_ok=True)
os.makedirs(plots_dir, exist_ok=True)

# Add timestamp to model filenames for versioning
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
MODEL_PATH_GRID_SEARCH = os.path.join(catboost_dir, f"catboost_gridsearch_model_{timestamp}.cbm")
MODEL_PATH_BAYESIAN_OPTIMIZATION = os.path.join(catboost_dir, f"catboost_bayesian_model_{timestamp}.cbm")
LINEAR_REGRESSION_MODEL_PATH = os.path.join(linear_regression_dir, f"linear_regression_model_{timestamp}.pkl")
LINEAR_REGRESSION_SCALER_PATH = os.path.join(linear_regression_dir, f"linear_regression_scaler_{timestamp}.pkl")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def find_latest_model(model_pattern, search_dir=None):
    """
    Find the most recent model file based on modification time.
    
    Args:
        model_pattern (str): Glob pattern to match model files
        search_dir (str, optional): Directory to search in
    
    Returns:
        str: Path to the most recent model file, or None if not found
    """
    if search_dir:
        search_path = os.path.join(search_dir, model_pattern)
    else:
        search_path = model_pattern
    
    models = glob.glob(search_path)
    if models:
        # Sort by modification time (newest first)
        models.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return models[0]
    return None


def cleanup_old_models():
    """
    Clean up old model files, keeping only the KEEP_MODEL_HISTORY most recent ones.
    """
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


def list_available_models():
    """
    List all available model files with their timestamps.
    """
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


def prepare_data_for_linear_regression(df, categorical_cols):
    """
    Prepare data for Linear Regression by one-hot encoding categorical variables.
    
    Args:
        df (pd.DataFrame): Input dataframe
        categorical_cols (list): List of categorical column names
    
    Returns:
        pd.DataFrame: Processed dataframe ready for linear regression
    """
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


def preprocess_future_df(future_df, df, categorical_cols):
    """
    Preprocess future dataframe to match training data format.
    
    Args:
        future_df (pd.DataFrame): Future dataframe to preprocess
        df (pd.DataFrame): Original training dataframe for reference
        categorical_cols (list): List of categorical column names
    
    Returns:
        pd.DataFrame: Preprocessed future dataframe
    """
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
    expected_columns = [col for col in df.columns if col != 'spend']
    future_df = future_df[expected_columns]
        
    return future_df

# =============================================================================
# HYPERPARAMETER OPTIMIZATION
# =============================================================================

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main(train=True, model='catboost', optimizer='bayesian'):
    """
    Main execution function for the budget forecasting model.
    
    Args:
        train (bool): Whether to train new models or load existing ones
        model (str): Model type ('catboost' or 'linearRegression')
        optimizer (str): Optimization method ('bayesian' or 'gridSearch')
    """
    try:
        global TRAIN, BAYESIAN_OPTIMIZATION, GRID_SEARCH_OPTIMIZATION, USE_LINEAR_REGRESSION
        
        # Update global configuration based on arguments
        TRAIN = train
        BAYESIAN_OPTIMIZATION = optimizer.lower() == 'bayesian'
        GRID_SEARCH_OPTIMIZATION = optimizer.lower() == 'gridsearch'
        USE_LINEAR_REGRESSION = model.lower() == 'linearregression'
        
        logger.info("="*60)
        logger.info("BUDGET FORECASTING MODEL EXECUTION STARTED")
        logger.info("="*60)
        
        logger.info(f"Configuration:")
        logger.info(f"  Train: {TRAIN}")
        logger.info(f"  Optimizer: {optimizer}")
        logger.info(f"  Model: {model}")
        logger.info(f"  Bayesian Optimization: {BAYESIAN_OPTIMIZATION}")
        logger.info(f"  Grid Search Optimization: {GRID_SEARCH_OPTIMIZATION}")
        logger.info(f"  Use Linear Regression: {USE_LINEAR_REGRESSION}")
        
        # =============================================================================
        # DATA PREPROCESSING
        # =============================================================================
        logger.info("="*60)
        logger.info("STAGE 1: DATA PREPROCESSING")
        logger.info("="*60)

        # Load the dataset
        logger.info("Loading dataset...")
        try:
            df = pd.read_csv('actual_detail_2025-08-14.csv')
            logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        except FileNotFoundError:
            logger.error("ERROR: Dataset file not found. Please ensure 'actual_detail_2025-08-14.csv' exists in the parent directory.")
            raise
        except Exception as e:
            logger.error(f"ERROR: Failed to load dataset: {str(e)}")
            raise

        # Convert 'month' column to datetime and extract year and month number
        logger.info("Processing date columns...")
        try:
            df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
            df['year'] = df['month'].dt.year
            df['month_num'] = df['month'].dt.month
            logger.info("Date columns processed successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to process date columns: {str(e)}")
            raise

        # Sort columns based on 'month' (datetime)
        df = df.sort_values('month').reset_index(drop=True)
        logger.info("Data sorted by month")

        # Drop 'estimate' column (it's same as 'spend') if it exists
        if 'estimate' in df.columns:
            df.drop(columns=['estimate'], inplace=True)
            logger.info("Dropped 'estimate' column (duplicate of 'spend')")
            
        # Convert other columns to categorical data type
        logger.info("Converting categorical columns...")
        categorical_cols = [
            'serviceName', 'usageFamily', 'accountName', 'accountID',
            'countryCode', 'buCode', 'region', 'segment', 'costString'
        ]
        for col in categorical_cols:
            df[col] = df[col].astype('category')
        logger.info(f"Converted {len(categorical_cols)} columns to categorical")
            
        # Drop the original 'month' column
        df.drop(columns=['month'], inplace=True)
        logger.info("Dropped original 'month' column")

        # Create lag features for time series analysis
        logger.info("Creating lag features...")
        try:
            for lag in [1, 2, 3, 6, 12]:
                df[f'lag_{lag}'] = df.groupby(categorical_cols, observed=False)['spend'].shift(lag)
            logger.info("Lag features created successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to create lag features: {str(e)}")
            raise

        # Create rolling statistics for additional signal
        logger.info("Creating rolling statistics...")
        try:
            df['rolling_mean_3'] = df.groupby(categorical_cols, observed=False)['spend'].shift(1).rolling(3).mean()
            df['rolling_mean_6'] = df.groupby(categorical_cols, observed=False)['spend'].shift(1).rolling(6).mean()
            logger.info("Rolling statistics created successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to create rolling statistics: {str(e)}")
            raise

        # Split the dataset into training and testing sets (80% train, 20% test)
        logger.info("Splitting data into training and testing sets...")
        try:
            train_size = int(len(df) * 0.8)  # 80% train
            train_data = df.iloc[:train_size]
            test_data = df.iloc[train_size:]

            X = df.drop(columns=['spend'])
            y = df['spend']

            # Define the features and target variable
            X_train = train_data.drop(columns=['spend'])
            y_train = train_data['spend']
            X_test = test_data.drop(columns=['spend'])
            y_test = test_data['spend']

            logger.info(f'Shape of training data: {train_data.shape}')
            logger.info(f'Shape of testing data: {test_data.shape}')
        except Exception as e:
            logger.error(f"ERROR: Failed to split data: {str(e)}")
            raise

        # =============================================================================
        # HYPERPARAMETER OPTIMIZATION FUNCTION
        # =============================================================================
        
        def objective(trial):
            """
            Objective function for Optuna hyperparameter optimization.
            
            Args:
                trial: Optuna trial object
            
            Returns:
                float: Mean RMSE score across cross-validation folds
            """
            try:
                params = {
                    'depth': trial.suggest_int('depth', 4, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                    'l2_leaf_reg': trial.suggest_int('l2_leaf_reg', 1, 10),
                    'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
                    'iterations': 200,
                    'loss_function': 'Tweedie:variance_power=1.5',
                    'random_seed': 42,
                    'verbose': 0
                }
                
                model = CatBoostRegressor(**params, cat_features=categorical_cols)
                
                # Time series split for cross-validation
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
            except Exception as e:
                logger.error(f"ERROR in objective function: {str(e)}")
                raise

        # =============================================================================
        # MODEL LOADING OR TRAINING
        # =============================================================================
        logger.info("="*60)
        logger.info("STAGE 2: MODEL LOADING OR TRAINING")
        logger.info("="*60)

        # Check if we should train or load existing model
        should_train = TRAIN
        model_loaded = False
        linear_regression_loaded = False

        if not TRAIN:
            logger.info("Attempting to load existing models...")
            # Try to load existing CatBoost model based on optimization type
            if BAYESIAN_OPTIMIZATION:
                latest_model = find_latest_model("catboost_bayesian_model_*.cbm", catboost_dir)
                if latest_model:
                    try:
                        model = CatBoostRegressor()
                        model.load_model(latest_model)
                        logger.info(f"Loaded existing Bayesian model: {latest_model}")
                        model_loaded = True
                    except Exception as e:
                        logger.error(f"ERROR: Failed to load Bayesian model: {str(e)}")
                        should_train = True
                else:
                    logger.info("No existing Bayesian model found. Starting training...")
                    should_train = True
            
            elif GRID_SEARCH_OPTIMIZATION:
                latest_model = find_latest_model("catboost_gridsearch_model_*.cbm", catboost_dir)
                if latest_model:
                    try:
                        model = CatBoostRegressor()
                        model.load_model(latest_model)
                        logger.info(f"Loaded existing Grid Search model: {latest_model}")
                        model_loaded = True
                    except Exception as e:
                        logger.error(f"ERROR: Failed to load Grid Search model: {str(e)}")
                        should_train = True
                else:
                    logger.info("No existing Grid Search model found. Starting training...")
                    should_train = True
            
            # Try to load Linear Regression model if enabled
            if USE_LINEAR_REGRESSION:
                latest_lr_model = find_latest_model("linear_regression_model_*.pkl", linear_regression_dir)
                latest_lr_scaler = find_latest_model("linear_regression_scaler_*.pkl", linear_regression_dir)
                if latest_lr_model and latest_lr_scaler:
                    try:
                        linear_regression_model = joblib.load(latest_lr_model)
                        linear_regression_scaler = joblib.load(latest_lr_scaler)
                        logger.info(f"Loaded existing Linear Regression model: {latest_lr_model}")
                        linear_regression_loaded = True
                    except Exception as e:
                        logger.error(f"ERROR: Failed to load Linear Regression model: {str(e)}")
                        should_train = True
                else:
                    logger.info("No existing Linear Regression model found. Will train new one...")
                    should_train = True

        # =============================================================================
        # MODEL TRAINING
        # =============================================================================
        if should_train:
            logger.info("="*60)
            logger.info("STAGE 3: MODEL TRAINING")
            logger.info("="*60)
            
            # Clean up old models and prepare for training
            try:
                cleanup_old_models()
                logger.info(f"Training new model with timestamp: {timestamp}")
                list_available_models()
            except Exception as e:
                logger.error(f"ERROR: Failed to cleanup old models: {str(e)}")
            
            # Train CatBoost model
            if BAYESIAN_OPTIMIZATION:
                logger.info("--- Bayesian Optimization (Optuna) ---")
                try:
                    # Use Optuna for hyperparameter tuning
                    study = optuna.create_study(direction='minimize')
                    study.optimize(objective, n_trials=20)  # 50 trials for comprehensive search

                    logger.info(f"Best Parameters: {study.best_params}")
                    logger.info(f"Best RMSE: {study.best_value}")
                    
                    best_params = study.best_params
                    best_params.update({
                        'iterations': 1000,
                        'loss_function': 'Tweedie:variance_power=1.5',
                        'random_seed': 42,
                        'verbose': 200
                    })

                    model = CatBoostRegressor(**best_params, cat_features=categorical_cols)
                    model.fit(X_train, y_train)
                    model.save_model(MODEL_PATH_BAYESIAN_OPTIMIZATION)
                    logger.info(f"Model saved to {MODEL_PATH_BAYESIAN_OPTIMIZATION}")
                except Exception as e:
                    logger.error(f"ERROR: Failed during Bayesian optimization: {str(e)}")
                    raise
                
            else:
                logger.info("--- Grid Search Optimization ---")
                try:
                    # Use GridSearchCV for hyperparameter tuning
                    model = CatBoostRegressor(
                        loss_function='RMSE',
                        cat_features=categorical_cols,
                        random_seed=42,
                        verbose=0
                    )
                    
                    grid = {
                        'depth': [3, 6, 8, 10, 12],
                        'learning_rate': [0.01, 0.05, 0.1],
                        'iterations': [200, 500, 800, 1000],
                        'bootstrap_type': ['Bayesian', 'Bernoulli'],
                        'l2_leaf_reg': [1, 3, 5]
                    }
                    
                    # Use GridSearchCV to find the best hyperparameters (takes a long time as per parameters)
                    grid_search_result = model.grid_search(
                        grid,
                        X_train,
                        y_train,
                        cv=3,                  # 3-fold cross-validation
                        plot=False,             # set True to plot learning curves
                        verbose=0               #set to 0 to avoid printing the progress bar
                    )

                    model.fit(X_train, y_train)
                    model.save_model(MODEL_PATH_GRID_SEARCH)
                    logger.info(f"Model saved to {MODEL_PATH_GRID_SEARCH}")
                except Exception as e:
                    logger.error(f"ERROR: Failed during Grid Search optimization: {str(e)}")
                    raise
            
            # Train Linear Regression model (if enabled)
            if USE_LINEAR_REGRESSION:
                logger.info("="*50)
                logger.info("Training Linear Regression Model")
                logger.info("="*50)
                
                try:
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
                    logger.info(f"Linear Regression model saved to {LINEAR_REGRESSION_MODEL_PATH}")
                    logger.info(f"Scaler saved to {LINEAR_REGRESSION_SCALER_PATH}")
                    
                    # Make predictions with Linear Regression
                    y_pred_lr = linear_regression_model.predict(X_test_scaled)
                    
                    # Calculate metrics for Linear Regression
                    rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
                    mae_lr = mean_absolute_error(y_test, y_pred_lr)
                    r2_lr = r2_score(y_test, y_pred_lr)
                    
                    logger.info(f"Linear Regression Results:")
                    logger.info(f"RMSE: {rmse_lr:.4f}")
                    logger.info(f"MAE: {mae_lr:.4f}")
                    logger.info(f"R²: {r2_lr:.4f}")
                    
                    linear_regression_loaded = True
                except Exception as e:
                    logger.error(f"ERROR: Failed to train Linear Regression model: {str(e)}")
                    raise

        # =============================================================================
        # MODEL EVALUATION
        # =============================================================================
        logger.info("="*60)
        logger.info("STAGE 4: MODEL EVALUATION")
        logger.info("="*60)

        # Make predictions with CatBoost
        try:
            y_pred = model.predict(X_test)

            # Calculate metrics for CatBoost
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            logger.info(f"CatBoost Model Results:")
            logger.info(f"RMSE: {rmse:.4f}")
            logger.info(f"MAE: {mae:.4f}")
            logger.info(f"R²: {r2:.4f}")
        except Exception as e:
            logger.error(f"ERROR: Failed to evaluate CatBoost model: {str(e)}")
            raise

        # Linear Regression predictions and metrics (if model is loaded)
        if linear_regression_loaded:
            try:
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
                
                logger.info(f"Linear Regression Model Results:")
                logger.info(f"RMSE: {rmse_lr:.4f}")
                logger.info(f"MAE: {mae_lr:.4f}")
                logger.info(f"R²: {r2_lr:.4f}")
                
                # Model comparison
                logger.info(f"Model Comparison:")
                logger.info(f"{'Metric':<15} {'CatBoost':<15} {'Linear Regression':<20} {'Winner':<10}")
                logger.info("-" * 60)
                logger.info(f"{'RMSE':<15} {rmse:<15.4f} {rmse_lr:<20.4f} {'CatBoost' if rmse < rmse_lr else 'Linear Regression'}")
                logger.info(f"{'MAE':<15} {mae:<15.4f} {mae_lr:<20.4f} {'CatBoost' if mae < mae_lr else 'Linear Regression'}")
                logger.info(f"{'R²':<15} {r2:<15.4f} {r2_lr:<20.4f} {'CatBoost' if r2 > r2_lr else 'Linear Regression'}")
                
                # Store predictions for plotting
                y_pred_lr_final = y_pred_lr
            except Exception as e:
                logger.error(f"ERROR: Failed to evaluate Linear Regression model: {str(e)}")
                y_pred_lr_final = None
        else:
            y_pred_lr_final = None

        # =============================================================================
        # VISUALIZATION - MONTHLY COMPARISONS
        # =============================================================================
        logger.info("="*60)
        logger.info("STAGE 5: GENERATING VISUALIZATIONS")
        logger.info("="*60)

        try:
            # Add predictions to the test dataset
            test_data = test_data.copy()
            test_data['predicted_spend_catboost'] = y_pred

            # Add Linear Regression predictions if available
            if y_pred_lr_final is not None:
                test_data['predicted_spend_lr'] = y_pred_lr_final

            # Recreate a proper year_month column for plotting
            test_data['year_month'] = pd.to_datetime(
                test_data['year'].astype(str) + '-' + test_data['month_num'].astype(str) + '-01'
            )

            # Aggregate by month for visualization
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

            # Plot 1: Monthly Actual vs Predicted Bar Chart
            logger.info("Generating monthly comparison bar chart...")
            if y_pred_lr_final is not None:
                # Plot with both models
                fig = make_subplots()  # no secondary_y needed

                fig.add_trace(
                    go.Bar(
                        x=monthly_compare['year_month'],
                        y=monthly_compare['spend'], 
                        name="Actual",
                        hovertemplate='<b>Month:</b> %{x}<br><b>Actual Spend:</b> $%{y:,.2f}<extra></extra>'
                    )
                )

                fig.add_trace(
                    go.Bar(
                        x=monthly_compare['year_month'],
                        y=monthly_compare['predicted_spend_catboost'], 
                        name="CatBoost",
                        hovertemplate='<b>Month:</b> %{x}<br><b>CatBoost Prediction:</b> $%{y:,.2f}<extra></extra>'
                    )
                )

                fig.add_trace(
                    go.Bar(
                        x=monthly_compare['year_month'],
                        y=monthly_compare['predicted_spend_lr'], 
                        name="Linear Regression",
                        hovertemplate='<b>Month:</b> %{x}<br><b>Linear Regression Prediction:</b> $%{y:,.2f}<extra></extra>'
                    )
                )

                fig.update_layout(
                    title="Actual vs Predicted Monthly Spend (CatBoost vs Linear Regression)",
                    xaxis_title="Month",
                    yaxis_title="Spend (USD)",
                    barmode='group',   # side-by-side bars
                    width=1000,
                    height=600,
                    hovermode='x unified',
                    template='plotly_white'
                )

                pyo.plot(fig, filename=os.path.join(plots_dir, "monthly_comparison_bar.html"))
                logger.info(f"Monthly comparison bar chart saved to {os.path.join(plots_dir, 'monthly_comparison_bar.html')}")
            else:
                # Plot with only CatBoost
                fig = make_subplots()

                fig.add_trace(
                    go.Bar(
                        x=monthly_compare['year_month'],
                        y=monthly_compare['spend'], 
                        name="Actual",
                        hovertemplate='<b>Month:</b> %{x}<br><b>Actual Spend:</b> $%{y:,.2f}<extra></extra>'
                    )
                )

                fig.add_trace(
                    go.Bar(
                        x=monthly_compare['year_month'],
                        y=monthly_compare['predicted_spend_catboost'], 
                        name="CatBoost",
                        hovertemplate='<b>Month:</b> %{x}<br><b>CatBoost Prediction:</b> $%{y:,.2f}<extra></extra>'
                    )
                )

                fig.update_layout(
                    title="Actual vs Predicted Monthly Spend (CatBoost)",
                    xaxis_title="Month",
                    yaxis_title="Spend (USD)",
                    barmode='group',
                    width=1000,
                    height=600,
                    hovermode='x unified',
                    template='plotly_white'
                )

                pyo.plot(fig, filename=os.path.join(plots_dir, "monthly_comparison_bar.html"))
                logger.info(f"Monthly comparison bar chart saved to {os.path.join(plots_dir, 'monthly_comparison_bar.html')}")

            # Plot 2: Monthly Actual vs Predicted Line Graph
            logger.info("Generating monthly comparison line graph...")

            fig = make_subplots()

            # Actual
            fig.add_trace(
                go.Scatter(
                    x=monthly_compare['year_month'], 
                    y=monthly_compare['spend'], 
                    mode='lines+markers', 
                    name="Actual",
                    hovertemplate='<b>Month:</b> %{x}<br><b>Actual Spend:</b> $%{y:,.2f}<extra></extra>'
                )
            )

            # CatBoost
            fig.add_trace(
                go.Scatter(
                    x=monthly_compare['year_month'], 
                    y=monthly_compare['predicted_spend_catboost'], 
                    mode='lines+markers', 
                    name="CatBoost",
                    hovertemplate='<b>Month:</b> %{x}<br><b>CatBoost Prediction:</b> $%{y:,.2f}<extra></extra>'
                )
            )

            # Linear Regression (only if available)
            if y_pred_lr_final is not None:
                fig.add_trace(
                    go.Scatter(
                        x=monthly_compare['year_month'], 
                        y=monthly_compare['predicted_spend_lr'], 
                        mode='lines+markers', 
                        name="Linear Regression",
                        hovertemplate='<b>Month:</b> %{x}<br><b>Linear Regression Prediction:</b> $%{y:,.2f}<extra></extra>'
                    )
                )
                title_text = "Actual vs Predicted Monthly Spend (CatBoost vs Linear Regression)"
            else:
                title_text = "Actual vs Predicted Monthly Spend (CatBoost)"

            # Layout
            fig.update_layout(
                title=title_text,
                xaxis_title="Month",
                yaxis_title="Spend (USD)",
                width=1000,
                height=600,
                hovermode='x unified',
                template='plotly_white'
            )

            # Save
            pyo.plot(fig, filename=os.path.join(plots_dir, "monthly_comparison_line.html"))
            logger.info(f"Monthly comparison line graph saved to {os.path.join(plots_dir, 'monthly_comparison_line.html')}")

            
            logger.info("Visualizations generated successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to generate visualizations: {str(e)}")

        # =============================================================================
        # FUTURE PREDICTIONS
        # =============================================================================
        logger.info("="*60)
        logger.info("STAGE 6: GENERATING FUTURE PREDICTIONS")
        logger.info("="*60)

        try:
            # Define the start and end dates for future predictions
            start_date = datetime(2025, 8, 1)

            # Generate a list of 24 months from start date
            month_range = pd.date_range(start=start_date, periods=24, freq='MS').strftime("%Y-%m").tolist()

            # Create a DataFrame with month column
            future_df = pd.DataFrame({'month': month_range})
            future_df = preprocess_future_df(future_df, df, categorical_cols)

            # Predict future spend with CatBoost
            future_pred = model.predict(future_df)

            # Linear Regression future predictions (if model is loaded)
            if linear_regression_loaded:
                # Prepare future data for Linear Regression
                future_df_lr = prepare_data_for_linear_regression(future_df, categorical_cols)
                
                # Ensure the future data has the same columns as training data
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

            # Create comprehensive future predictions visualization
            logger.info("Generating future predictions visualization...")
            
            # Create subplots for future predictions
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("24-Month Future Spend Predictions: Line Chart", "24-Month Future Spend Predictions: Bar Chart"),
                vertical_spacing=0.1
            )

            # Plot 1: Line graph comparison
            if linear_regression_loaded:
                fig.add_trace(
                    go.Scatter(x=month_labels, y=future_pred, mode='lines+markers', 
                              name='CatBoost Prediction', line=dict(color='blue', width=3), 
                              marker=dict(size=8)),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=month_labels, y=future_pred_lr, mode='lines+markers', 
                              name='Linear Regression Prediction', line=dict(color='red', width=3), 
                              marker=dict(size=8)),
                    row=1, col=1
                )
            else:
                fig.add_trace(
                    go.Scatter(x=month_labels, y=future_pred, mode='lines+markers', 
                              name='CatBoost Prediction', line=dict(color='blue', width=3), 
                              marker=dict(size=8)),
                    row=1, col=1
                )

            # Plot 2: Bar chart comparison
            if linear_regression_loaded:
                fig.add_trace(
                    go.Bar(x=month_labels, y=future_pred, name='CatBoost', 
                          marker_color='blue', opacity=0.7),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Bar(x=month_labels, y=future_pred_lr, name='Linear Regression', 
                          marker_color='red', opacity=0.7),
                    row=2, col=1
                )
            else:
                fig.add_trace(
                    go.Bar(x=month_labels, y=future_pred, name='CatBoost', 
                          marker_color='blue', opacity=0.7),
                    row=2, col=1
                )

            # Update layout
            fig.update_layout(
                title="24-Month Future Spend Predictions",
                width=1200,
                height=800,
                showlegend=True,
                barmode='group' if linear_regression_loaded else 'relative',
                hovermode='x unified',
                template='plotly_white'
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Month", row=1, col=1)
            fig.update_yaxes(title_text="Predicted Spend (USD)", row=1, col=1)
            fig.update_xaxes(title_text="Month", row=2, col=1)
            fig.update_yaxes(title_text="Predicted Spend (USD)", row=2, col=1)
            
            # Save the plot
            pyo.plot(fig, filename=os.path.join(plots_dir, "future_predictions.html"))
            logger.info(f"Future predictions visualization saved to {os.path.join(plots_dir, 'future_predictions.html')}")

            # =============================================================================
            # FUTURE PREDICTIONS SUMMARY
            # =============================================================================
            logger.info("="*80)
            logger.info("24-MONTH FUTURE PREDICTIONS COMPARISON")
            logger.info("="*80)

            if linear_regression_loaded:
                logger.info(f"{'Month':<12} {'CatBoost':<15} {'Linear Regression':<20} {'Difference':<15} {'% Difference':<15}")
                logger.info("-" * 80)
                
                for i, (month, cat_pred, lr_pred) in enumerate(zip(month_labels, future_pred, future_pred_lr)):
                    diff = cat_pred - lr_pred
                    pct_diff = (diff / lr_pred) * 100 if lr_pred != 0 else 0
                    logger.info(f"{month:<12} ${cat_pred:<14.2f} ${lr_pred:<19.2f} ${diff:<14.2f} {pct_diff:<14.1f}%")
                
                logger.info("="*80)
                logger.info("SUMMARY STATISTICS")
                logger.info("="*80)
                logger.info(f"CatBoost Average Prediction: ${np.mean(future_pred):.2f}")
                logger.info(f"Linear Regression Average Prediction: ${np.mean(future_pred_lr):.2f}")
                logger.info(f"Average Difference: ${np.mean(future_pred - future_pred_lr):.2f}")
                logger.info(f"Average % Difference: {np.mean((future_pred - future_pred_lr) / future_pred_lr) * 100:.1f}%")
                logger.info(f"CatBoost Prediction Range: ${np.min(future_pred):.2f} - ${np.max(future_pred):.2f}")
                logger.info(f"Linear Regression Prediction Range: ${np.min(future_pred_lr):.2f} - ${np.max(future_pred_lr):.2f}")
            else:
                logger.info(f"{'Month':<12} {'CatBoost Prediction':<20}")
                logger.info("-" * 35)
                for month, pred in zip(month_labels, future_pred):
                    logger.info(f"{month:<12} ${pred:<19.2f}")
                
                logger.info(f"Average Prediction: ${np.mean(future_pred):.2f}")
                logger.info(f"Prediction Range: ${np.min(future_pred):.2f} - ${np.max(future_pred):.2f}")
            
            logger.info("Future predictions generated successfully")
        except Exception as e:
            logger.error(f"ERROR: Failed to generate future predictions: {str(e)}")

        logger.info("="*60)
        logger.info("ANALYSIS COMPLETE - SUCCESS")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {str(e)}")
        logger.error("Analysis failed. Check the logs for details.")
        raise

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Budget Forecasting Model - Train and evaluate CatBoost and Linear Regression models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train CatBoost with Bayesian optimization
  python legacy_models.py --train true --optimizer bayesian --model catboost
  
  # Load existing models and run evaluation
  python legacy_models.py --train false --optimizer bayesian --model catboost
  
  # Train Linear Regression model
  python legacy_models.py --train true --optimizer bayesian --model linearRegression
  
  # Train CatBoost with Grid Search optimization
  python legacy_models.py --train true --optimizer gridSearch --model catboost
        """
    )
    
    parser.add_argument(
        '--train',
        type=str,
        choices=['true', 'false'],
        default='false',
        help='Whether to train new models (true) or load existing ones (false)'
    )
    
    parser.add_argument(
        '--optimizer',
        type=str,
        choices=['bayesian', 'gridSearch'],
        default='bayesian',
        help='Optimization method for CatBoost: bayesian (Optuna) or gridSearch (GridSearchCV)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=['catboost', 'linearRegression'],
        default='catboost',
        help='Model type to use: catboost or linearRegression'
    )
    
    args = parser.parse_args()
    
    # Convert string arguments to appropriate types
    train_bool = args.train.lower() == 'true'
    
    # Run the main function
    main(train=train_bool, model=args.model, optimizer=args.optimizer)
    