"""
Example script for uploading data from Google Colab to Oracle ATP
Copy this to your Colab notebook
"""

# Install required packages in Colab
# !pip install oracledb pandas

import oracledb
import pandas as pd
from google.colab import files
import os

# Step 1: Upload wallet to Colab
print("Upload your Oracle wallet ZIP file:")
uploaded = files.upload()
wallet_file = list(uploaded.keys())[0]

# Extract wallet
!unzip {wallet_file} -d wallet/

# Step 2: Set credentials
DB_USER = 'admin'  # Your ATP username
DB_PASSWORD = 'YourPassword'  # Your ATP password
DB_DSN = 'your_atp_connection_string'  # From tnsnames.ora

# Step 3: Connect to database
oracledb.init_oracle_client(config_dir='wallet/')
connection = oracledb.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    dsn=DB_DSN
)
print("✓ Connected to Oracle ATP")

# Step 4: Upload your CSV data
def upload_csv_to_oracle(csv_path, table_name):
    """Upload CSV to Oracle table"""
    df = pd.read_csv(csv_path)
    print(f"Uploading {len(df)} rows to {table_name}...")
    
    columns = df.columns.tolist()
    placeholders = ', '.join([f':{i+1}' for i in range(len(columns))])
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    cursor = connection.cursor()
    rows = [tuple(row) for row in df.values]
    cursor.executemany(sql, rows)
    connection.commit()
    cursor.close()
    
    print(f"✓ Uploaded {len(df)} rows successfully")

# Example: Upload features
upload_csv_to_oracle('features.csv', 'ml_features')

# Example: Upload raw data
upload_csv_to_oracle('raw_weather_data.csv', 'raw_weather_data')

# Example: Save model metadata
def save_model_metadata(model_info):
    cursor = connection.cursor()
    sql = """
    INSERT INTO model_metadata (
        model_name, model_version, model_type, training_date,
        accuracy_score, mae, rmse, r2_score, feature_count,
        training_samples, model_path, is_active
    ) VALUES (
        :1, :2, :3, SYSDATE, :4, :5, :6, :7, :8, :9, :10, :11
    )
    """
    cursor.execute(sql, (
        model_info['name'],
        model_info['version'],
        model_info['type'],
        model_info['accuracy'],
        model_info['mae'],
        model_info['rmse'],
        model_info['r2'],
        model_info['features'],
        model_info['samples'],
        model_info['path'],
        1  # is_active
    ))
    connection.commit()
    cursor.close()
    print(f"✓ Saved metadata for {model_info['name']}")

# Save XGBoost metadata
save_model_metadata({
    'name': 'XGBoost',
    'version': 'v1.0',
    'type': 'regression',
    'accuracy': 0.95,
    'mae': 0.5,
    'rmse': 0.8,
    'r2': 0.92,
    'features': 16,
    'samples': 10000,
    'path': 'oci://bucket/models/xgboost_v1.joblib'
})

# Close connection
connection.close()
print("✓ Database connection closed")
