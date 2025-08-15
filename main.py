import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from catboost import CatBoostRegressor, Pool
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

#import CSV file
df = pd.read_csv('actual_detail_2025-08-14.csv')


# Drop 'estimate' column (as it is same as 'spend') if it exists
if 'estimate' in df.columns:
    df.drop(columns=['estimate'], inplace=True)
    
# Convert other columns to categorical data type
categorical_cols = [
    'serviceName', 'usageFamily', 'accountName', 'accountID',
    'countryCode', 'buCode', 'region', 'segment', 'costString'
]
for col in categorical_cols:
    df[col] = df[col].astype('category')
    
#Convert 'month' column to datetime and extract year and month number
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')
df['year'] = df['month'].dt.year
df['month_num'] = df['month'].dt.month

# Drop the original 'month' column
df.drop(columns=['month'], inplace=True)

#display data types of all columns
print(df.dtypes)

# Divide the dataset into training and testing sets
# 80% for training and 20% for testing
# Ensure that the split is random but reproducible by setting a random state
# Shuffle the data before splitting
train_data, test_data = train_test_split(df, test_size=0.2, random_state=42, shuffle=True)

# Shape of the training and testing datasets
print('Shape of training data :',train_data.shape)
print('Shape of testing data :',test_data.shape)

# Define the features and target variable
X_train = train_data.drop(columns=['spend'])
y_train = train_data['spend']
X_test  = test_data.drop(columns=['spend'])
y_test  = test_data['spend']

# Model CatBoostRegressor
model = CatBoostRegressor(
    cat_features=categorical_cols,
    iterations=1000,
    learning_rate=0.05,
    depth=8,
    loss_function='RMSE',
    random_seed=42,
    verbose=200
)

model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Metrics
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse:.4f}")
print(f"MAE: {mae:.4f}")
print(f"R²: {r2:.4f}")

# Plot the model performance
plt.figure(figsize=(8,6))
plt.scatter(y_test, y_pred, alpha=0.6)
plt.plot([y_test.min(), y_test.max()],
         [y_test.min(), y_test.max()],
         'r--', lw=2)  # perfect prediction line
plt.xlabel('Actual Spend')
plt.ylabel('Predicted Spend')
plt.title('CatBoost Regression: Predicted vs Actual Spend')
plt.show()


