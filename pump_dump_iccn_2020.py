import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import time

# Load trading data
# Assumes data has columns: 'timestamp', 'price', 'volume', 'type' (buy/sell)
data = pd.read_csv("trading_data.csv")
data['timestamp'] = pd.to_datetime(data['timestamp'])

# Feature Engineering based on paper indicators

# Setting window sizes
chunk_size = 25  # in seconds, for rapid detection
window_size = 7 * 60 * 60  # 7 hours in seconds

# Helper functions
def calculate_rush_orders(trades, threshold_ms=1):
    # Detects "rush orders" by aggregating trades that occur within a millisecond threshold
    trades['time_diff'] = trades['timestamp'].diff().dt.total_seconds()
    rush_orders = trades[trades['time_diff'] < threshold_ms].shape[0]
    return rush_orders

def generate_features(df):
    df['price_diff'] = df['price'].diff()
    df['volatility'] = df['price_diff'].rolling(window=chunk_size).std()
    df['avg_volume'] = df['volume'].rolling(window=chunk_size).mean()
    df['std_volume'] = df['volume'].rolling(window=chunk_size).std()
    
    # Rush orders count within a time chunk
    df['rush_orders'] = df.groupby((df['timestamp'].diff().dt.total_seconds() > chunk_size).cumsum()).apply(calculate_rush_orders)

    # Price statistics
    df['avg_price'] = df['price'].rolling(window=chunk_size).mean()
    df['std_price'] = df['price'].rolling(window=chunk_size).std()
    df['max_price'] = df['price'].rolling(window=chunk_size).max()
    df['min_price'] = df['price'].rolling(window=chunk_size).min()
    
    return df

# Feature calculation
data = generate_features(data)

# Drop NaN values from rolling calculations
data.dropna(inplace=True)

# Target feature (Assuming pump and dump events are labeled in the data)
X = data[['volatility', 'avg_volume', 'std_volume', 'rush_orders', 'avg_price', 'std_price', 'max_price', 'min_price']]
y = data['pump_dump_label']  # 1 for pump-and-dump, 0 otherwise

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Classifier model based on Random Forest
model = RandomForestClassifier(n_estimators=200, max_depth=4, min_samples_leaf=6, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Feature importance analysis
feature_importances = model.feature_importances_
features = X.columns
importance_df = pd.DataFrame({'Feature': features, 'Importance': feature_importances})
importance_df.sort_values(by='Importance', ascending=False, inplace=True)
print(importance_df)
