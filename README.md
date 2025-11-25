# Budget Forecasting Model


A full-stack **time series forecasting platform** for predicting cloud infrastructure expenses using **Prophet**.  
It provides an interactive **Django + Chart.js dashboard** to visualize forecasts, manage uploaded data, and analyze metrics intuitively.

### Running the Main Script
```bash
# Install dependencies

# Create virutal environment (Optional)
pip install pipenv

#Enter virtual env (Optional) (cd /path/to/your/project)
pipenv shell

pip install -r requirements.txt

# Run Server to open localhost site
#Navigate to /BudgetForecast/budget_forecast_app and run
python manage.py runserver 
```

## 🎯 Overview
This application enables users to:
- Upload cloud cost data (e.g., AWS, GCP, Azure).
- Run forecasting pipelines using Prophet model.
- Visualize budget forecasts using **interactive Chart.js** plots.
- Filter forecasts by **Account Name** or **Service Name** dynamically.
- View key metrics and download forecast results as CSV files.


## ️ Detailed Flow Explanation

### User Uploads a File

- The user navigates to the **Upload Page** (`upload.html`).
- They select the **Account Name** and **Service Name** from dynamic dropdowns.
- Upon clicking **Upload**, the CSV file is sent via an HTTP **POST** request.

---

###  Django Handles the Request

- The request is routed through `forecast/urls.py` → handled by the `upload_forecast` view in `forecast/views.py`.
- The uploaded file is saved under the `/data/` directory for persistence.

---

###  Machine Learning Pipeline Invoked

- The backend invokes the core forecasting logic in `forecast/ml/main.py`.

#### The pipeline performs the following steps:
1. Reads the uploaded CSV.
2. Cleans and transforms data using `data_transformations.py`.
3. Loads the selected forecasting model (`prophet_model.py`, `legacy_models.py`, etc.).
4. Generates **future predictions**.

---

###  Result Visualization

- Predictions and metrics (**MAE**, **RMSE**, etc.) are prepared and serialized.
- The backend sends the results as **JSON** data to the frontend.
- The **Dashboard Page** (`dashboard.html`) dynamically renders charts via **Chart.js**.

---

### Interactive Updates

Users can:
- Switch between **Account** or **Service** forecasts dynamically.
- Upload new CSVs to refresh predictions.

Each new upload automatically triggers the entire forecasting pipeline.


## Features

### Core Functionality
- **Prophet Support**
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
├── README.md                            # Project documentation
├── requirements.txt                     # Python dependencies
│
├── data/                                # Data directory for input CSV files
│   ├── Forecast Data July 2022.csv
│   └── actual_detail_2025-08-14.csv
│
│
├── plots/                               # Generated visualizations and reports
│   ├── future_predictions.html           # ChartJS future forecast output
│   ├── monthly_comparison_bar.html       # Monthly comparison (bar chart)
│   ├── monthly_comparison_line.html      # Monthly comparison (line chart)
│   └── spend/html/                       # Detailed spend analysis reports
│       ├── 01_monthly_total_spend_trend.html
│       ├── 02_monthly_average_spend_trend.html
│       ├── 03_monthly_record_count.html
│       ├── ...
│       └── 18_monthly_spend_trend_by_region.html
│
│
├── budget_forecast_app/                 # Django application root
│   ├── db.sqlite3                       # SQLite database for development
│   ├── actual_detail_2025-08-14.csv     # Example input dataset
│   ├── manage.py                        # Django management script
│
│   ├── budget_forecast_app/             # Django project configuration
│   │   ├── __init__.py
│   │   ├── settings.py                  # Django settings (integrates ML & frontend)
│   │   ├── urls.py                      # Project-level URL routing
│   │   ├── asgi.py                      # ASGI entry point
│   │   └── wsgi.py                      # WSGI entry point
│
│   ├── forecast/                        # Main forecasting app
│   │   ├── admin.py                     # Django admin integration
│   │   ├── apps.py                      # App configuration
│   │   ├── models.py                    # (Optional) ORM models if used
│   │   ├── urls.py                      # URL routing for app views
│   │   ├── views.py                     # Handles dashboard, upload, and forecasting logic
│   │   ├── tests.py                     # Unit tests for the forecasting module
│   │
│   │   ├── ml/                          # Machine Learning pipeline modules
│   │   │   ├── main.py                  # Entry point for training & forecasting logic
│   │   │   ├── legacy_models.py         # Older ML implementations (CatBoost, LR)
│   │   │   ├── legacy_prophet_model.py  # Legacy Prophet-based model for time series
│   │   │   ├── prophet_model.py         # Updated Prophet-based forecasting module
│   │   │   ├── data_exploration.py      # Exploratory data analysis utilities
│   │   │   ├── enums.py                 # Enum definitions for forecast types
│   │   │   ├── utils/                   # Utility scripts
│   │   │   │   ├── data_transformations.py  # Data preprocessing and feature engineering
│   │   │   │   └── setup_logging.py         # Logging configuration
│   │   │   ├── models/                  # Trained models for CatBoost, Linear Regression
│   │   │   │   ├── catboost/
│   │   │   │   └── linear_regression/
│   │   │   └── catboost_info/           # Local CatBoost logs within app context
│   │
│   │   ├── templates/forecast/          # Frontend templates
│   │   │   ├── dashboard.html           # Main dashboard (ChartJS plots + metrics)
│   │   │   └── upload.html              # File upload interface for new datasets
│   │
│   │   └── migrations/                  # Django migrations for the app
│   │       └── __init__.py
│
└── __pycache__/                         # Cached Python files (auto-generated)

```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Django 4.2.25
- pip package manager
- Sufficient disk space for model storage

### Dependencies
The project requires the following Python packages:
- pandas: Data manipulation and analysis
- numpy: Numerical computing
- scikit-learn: Machine learning algorithms
- Django : Web framework
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
- Handles missing values appropriately



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