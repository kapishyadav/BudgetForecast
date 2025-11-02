# Budget Forecasting Model

A comprehensive machine learning system for predicting budget spending using advanced time series forecasting techniques. This project implements multiple models with hyperparameter optimization to provide accurate budget predictions for financial planning and analysis.

### Running the Main Script
```bash
# Install dependencies
pip install -r requirements.txt

# Run with plotly visualizations
#Example 1:
python src/legacy_models.py --train true --optimizer bayesian --model catboost

#Example 2:
python src/legacy_models.py --train false --optimizer gridSearch --model linearRegression
```

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Data Requirements](#data-requirements)
- [Usage](#usage)
- [Models](#models)
- [Optimization Techniques](#optimization-techniques)
- [Visualization Features](#visualization-features)
- [Model Evaluation](#model-evaluation)
- [Future Predictions](#future-predictions)
- [Configuration Options](#configuration-options)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Budget Forecasting Model is designed to predict future spending patterns based on historical financial data. It employs sophisticated machine learning algorithms with time series analysis capabilities to provide accurate forecasts for budget planning and financial decision-making.

The system supports multiple model types and optimization strategies, allowing users to choose the most appropriate approach for their specific use case. It includes comprehensive evaluation metrics, visualization tools, and automated model management features.

## ✨ Features

### Core Functionality
- **Multi-Model Support**: CatBoost and Linear Regression models
- **Advanced Optimization**: Bayesian optimization and Grid Search techniques
- **Time Series Analysis**: Lag features and rolling statistics
- **Automated Model Management**: Version control and cleanup
- **Comprehensive Evaluation**: Multiple performance metrics
- **Rich Visualizations**: Interactive plots and comparisons
- **Future Predictions**: 24-month forecasting capabilities

### Technical Features
- **Reproducible Results**: Fixed random seeds for consistency
- **Model Persistence**: Automatic saving and loading of trained models
- **Cross-Validation**: Time series aware validation strategies
- **Feature Engineering**: Automatic lag feature creation
- **Data Preprocessing**: Categorical encoding and scaling
- **Error Handling**: Robust error management and recovery

## 📁 Project Structure

```
BudgetForecast/
├── README.md                           # Project documentation
├── actual_detail_2025-08-14.csv       # Input dataset
├── src/
│   ├── main.py                        # Main execution script
│   └── data_exploration.py            # Data analysis utilities
├── models/                            # Trained model storage
│   ├── catboost/                      # CatBoost model files
│   └── linear_regression/             # Linear Regression models
├── plots/                             # Generated visualizations
│   ├── spend/                         # Spending analysis plots
│   └── *.png                          # Model comparison plots
└── catboost_info/                     # CatBoost training logs
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Sufficient disk space for model storage

### Dependencies
The project requires the following Python packages:
- pandas: Data manipulation and analysis
- numpy: Numerical computing
- scikit-learn: Machine learning algorithms
- catboost: Gradient boosting framework
- optuna: Hyperparameter optimization
- matplotlib: Data visualization
- joblib: Model serialization

### Setup Instructions
1. Clone the repository to your local machine
2. Navigate to the project directory
3. Install required dependencies using pip
4. Ensure your dataset is placed in the root directory
5. Verify the project structure matches the expected layout

## 📊 Data Requirements

### Input Format
The system expects a CSV file with the following structure:
- **month**: Date column in YYYY-MM format
- **spend**: Target variable (numerical spending amounts)
- **serviceName**: Categorical service identifier
- **usageFamily**: Categorical usage category
- **accountName**: Categorical account identifier
- **accountID**: Categorical account ID
- **countryCode**: Categorical country code
- **buCode**: Categorical business unit code
- **region**: Categorical region identifier
- **segment**: Categorical segment identifier
- **costString**: Categorical cost string

### Data Preprocessing
The system automatically performs the following preprocessing steps:
- Converts date columns to datetime format
- Extracts year and month components
- Converts categorical columns to appropriate data types
- Creates lag features for time series analysis
- Generates rolling statistics for additional signals
- Handles missing values appropriately

## 🎮 Usage

### Command Line Interface
The main script supports command-line arguments for flexible execution:

**Basic Usage:**
- Load existing models and run evaluation
- Train new models with specified optimization
- Compare different model types
- Generate future predictions

**Argument Options:**
- **train**: Boolean flag to control training vs loading
- **optimizer**: Choice between Bayesian and Grid Search optimization
- **model**: Selection between CatBoost and Linear Regression

### Execution Examples
- Load existing CatBoost model with Bayesian optimization
- Train new Linear Regression model
- Compare CatBoost vs Linear Regression performance
- Generate 24-month future predictions

### Interactive Mode
The system provides detailed progress information during execution:
- Data preprocessing status
- Model training progress
- Optimization trial results
- Evaluation metrics display
- Visualization generation status

## 🤖 Models

### CatBoost Model
**Description**: Gradient boosting framework optimized for categorical features
**Strengths**: 
- Handles categorical variables natively
- Robust to overfitting
- Excellent performance on structured data
- Built-in feature importance analysis

**Configuration**:
- Loss function: RMSE (Root Mean Square Error)
- Random seed: 42 (for reproducibility)
- Iterations: 1000 (configurable)
- Verbose output for monitoring

**Hyperparameters**:
- Tree depth: 4-10 (optimizable)
- Learning rate: 0.01-0.1 (log scale)
- L2 regularization: 1-10
- Bagging temperature: 0.0-1.0

### Linear Regression Model
**Description**: Traditional linear regression with feature engineering
**Strengths**:
- Interpretable results
- Fast training and prediction
- Good baseline performance
- Feature importance through coefficients

**Configuration**:
- One-hot encoding for categorical variables
- Standard scaling for numerical features
- Ridge regularization support
- Cross-validation for model selection

**Preprocessing**:
- Automatic categorical encoding
- Feature scaling and normalization
- Missing value imputation
- Dimensionality management

## 🔧 Optimization Techniques

### Bayesian Optimization (Optuna)
**Method**: Sequential model-based optimization
**Advantages**:
- Efficient hyperparameter search
- Intelligent trial selection
- Parallel optimization support
- Early stopping capabilities

**Configuration**:
- Number of trials: 50 (configurable)
- Optimization direction: Minimize RMSE
- Study creation: In-memory storage
- Trial timeout: Automatic handling

**Search Space**:
- Tree depth: Integer range 4-10
- Learning rate: Float range 0.01-0.1 (log scale)
- L2 regularization: Integer range 1-10
- Bagging temperature: Float range 0.0-1.0

### Grid Search Optimization
**Method**: Exhaustive parameter search
**Advantages**:
- Guaranteed optimal solution within grid
- Systematic parameter exploration
- Reproducible results
- Comprehensive coverage

**Configuration**:
- Cross-validation folds: 3
- Parameter grid: Predefined combinations
- Evaluation metric: RMSE
- Parallel processing support

**Search Space**:
- Tree depth: [3, 6, 8, 10, 12]
- Learning rate: [0.01, 0.05, 0.1]
- Iterations: [200, 500, 800, 1000]
- Bootstrap type: ['Bayesian', 'Bernoulli']
- L2 regularization: [1, 3, 5]

## 📈 Visualization Features

### Model Comparison Plots
**Monthly Bar Charts**:
- Actual vs predicted spending comparison
- Side-by-side model performance visualization
- Monthly aggregation for trend analysis
- Color-coded legend for easy interpretation

**Time Series Line Graphs**:
- Continuous spending trends over time
- Model prediction accuracy visualization
- Seasonal pattern identification
- Anomaly detection capabilities

### Future Predictions Visualization
**24-Month Forecasts**:
- Line graph comparison of model predictions
- Bar chart representation of future spending
- Confidence interval visualization
- Trend analysis and pattern recognition

**Statistical Summaries**:
- Average prediction comparisons
- Prediction range analysis
- Percentage difference calculations
- Model agreement assessment

### Performance Metrics Visualization
**Evaluation Dashboard**:
- RMSE comparison charts
- MAE performance analysis
- R-squared coefficient plots
- Model ranking visualizations

## 📊 Model Evaluation

### Performance Metrics
**Root Mean Square Error (RMSE)**:
- Measures prediction accuracy
- Penalizes large errors heavily
- Standard regression metric
- Scale-dependent measurement

**Mean Absolute Error (MAE)**:
- Average absolute prediction error
- Robust to outliers
- Easy to interpret
- Scale-dependent measurement

**R-squared Coefficient**:
- Proportion of variance explained
- Range: 0 to 1 (higher is better)
- Model fit assessment
- Scale-independent metric

### Cross-Validation Strategy
**Time Series Split**:
- Respects temporal order
- Prevents data leakage
- Realistic performance estimation
- Multiple fold validation

**Validation Process**:
- 3-fold time series cross-validation
- Sequential data splitting
- Consistent evaluation methodology
- Robust performance assessment

## 🔮 Future Predictions

### Forecasting Capabilities
**24-Month Horizon**:
- Extended prediction timeline
- Long-term trend analysis
- Strategic planning support
- Risk assessment capabilities

**Prediction Generation**:
- Automated future data preparation
- Lag feature extrapolation
- Rolling statistics projection
- Categorical feature handling

### Output Analysis
**Detailed Comparisons**:
- Month-by-month predictions
- Model agreement assessment
- Statistical significance testing
- Confidence interval estimation

**Summary Statistics**:
- Average prediction values
- Prediction range analysis
- Percentage differences
- Trend direction identification

## ⚙️ Configuration Options

### Training Parameters
**Model Selection**:
- CatBoost vs Linear Regression
- Single model or comparison mode
- Custom hyperparameter ranges
- Optimization strategy selection

**Data Processing**:
- Train/test split ratio (default: 80/20)
- Lag feature periods (1, 2, 3, 6, 12 months)
- Rolling window sizes (3, 6 months)
- Categorical encoding strategies

### Model Management
**Version Control**:
- Timestamped model files
- Automatic cleanup of old models
- Configurable retention policy
- Model history tracking

**Storage Options**:
- Local file system storage
- Compressed model formats
- Metadata preservation
- Backup and recovery

## 🛠️ Troubleshooting

### Common Issues
**Data Loading Errors**:
- Verify file path and format
- Check column names and types
- Ensure sufficient memory
- Validate data quality

**Model Training Issues**:
- Monitor memory usage
- Check hyperparameter ranges
- Verify optimization settings
- Review error messages

**Visualization Problems**:
- Ensure matplotlib backend
- Check display settings
- Verify plot data availability
- Monitor system resources

### Performance Optimization
**Memory Management**:
- Reduce batch sizes if needed
- Optimize data types
- Use efficient algorithms
- Monitor resource usage

**Speed Improvements**:
- Parallel processing options
- Reduced optimization trials
- Simplified model configurations
- Hardware acceleration

---

**Note**: This documentation is comprehensive and designed to help users understand and effectively use the Budget Forecasting Model. For specific implementation details, refer to the source code and inline documentation. 