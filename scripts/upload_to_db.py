"""
Upload CSV data from Colab to Oracle Autonomous Database
"""

import oracledb
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseUploader:
    """Upload data to Oracle Autonomous Database"""
    
    def __init__(self, username, password, dsn, wallet_location=None):
        """
        Initialize database connection
        
        Args:
            username: Oracle DB username
            password: Oracle DB password  
            dsn: Database connection string
            wallet_location: Path to wallet directory (for ATP)
        """
        self.username = username
        self.password = password
        self.dsn = dsn
        
        if wallet_location:
            oracledb.init_oracle_client(config_dir=wallet_location)
        
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn
            )
            logger.info("Connected to Oracle Autonomous Database")
            return self.connection
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise
    
    def upload_csv_to_table(self, csv_path, table_name, batch_size=1000):
        """
        Upload CSV data to database table
        
        Args:
            csv_path: Path to CSV file
            table_name: Target table name
            batch_size: Number of rows per batch
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Read {len(df)} rows from {csv_path}")
            
            # Get column names
            columns = df.columns.tolist()
            placeholders = ', '.join([f':{i+1}' for i in range(len(columns))])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Upload in batches
            cursor = self.connection.cursor()
            total_inserted = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                rows = [tuple(row) for row in batch.values]
                
                cursor.executemany(insert_sql, rows)
                self.connection.commit()
                
                total_inserted += len(rows)
                logger.info(f"Inserted {total_inserted}/{len(df)} rows")
            
            cursor.close()
            logger.info(f"Successfully uploaded {total_inserted} rows to {table_name}")
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def upload_features(self, csv_path):
        """Upload ML features from CSV"""
        self.upload_csv_to_table(csv_path, 'ml_features')
    
    def upload_raw_data(self, csv_path):
        """Upload raw weather data from CSV"""
        self.upload_csv_to_table(csv_path, 'raw_weather_data')
    
    def upload_predictions(self, csv_path):
        """Upload predictions from CSV"""
        self.upload_csv_to_table(csv_path, 'predictions')
    
    def save_model_metadata(self, model_info):
        """
        Save model metadata to database
        
        Args:
            model_info: Dict with model metadata
        """
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO model_metadata (
                model_name, model_version, model_type, training_date,
                accuracy_score, mae, rmse, r2_score, feature_count,
                training_samples, model_path, is_active
            ) VALUES (
                :model_name, :model_version, :model_type, :training_date,
                :accuracy_score, :mae, :rmse, :r2_score, :feature_count,
                :training_samples, :model_path, :is_active
            )
            """
            
            cursor.execute(sql, model_info)
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Saved metadata for model: {model_info['model_name']}")
            
        except Exception as e:
            logger.error(f"Failed to save model metadata: {e}")
            if self.connection:
                self.connection.rollback()
            raise
    
    def log_to_db(self, level, service, message, error_details=None):
        """
        Write log entry to database
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            service: Service name
            message: Log message
            error_details: Optional error details
        """
        try:
            cursor = self.connection.cursor()
            
            sql = """
            INSERT INTO app_logs (log_level, service_name, message, error_details)
            VALUES (:level, :service, :message, :error_details)
            """
            
            cursor.execute(sql, {
                'level': level,
                'service': service,
                'message': message,
                'error_details': error_details
            })
            
            self.connection.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# Example usage for Colab
if __name__ == "__main__":
    # Configuration
    DB_USER = os.getenv('ORACLE_USER', 'admin')
    DB_PASSWORD = os.getenv('ORACLE_PASSWORD')
    DB_DSN = os.getenv('ORACLE_DSN')
    WALLET_DIR = os.getenv('ORACLE_WALLET_LOCATION')
    
    # Initialize uploader
    uploader = DatabaseUploader(DB_USER, DB_PASSWORD, DB_DSN, WALLET_DIR)
    uploader.connect()
    
    # Upload CSV files
    uploader.upload_features('path/to/features.csv')
    uploader.upload_raw_data('path/to/raw_data.csv')
    
    # Save model metadata
    model_info = {
        'model_name': 'XGBoost',
        'model_version': 'v1.0',
        'model_type': 'regression',
        'training_date': datetime.now(),
        'accuracy_score': 0.95,
        'mae': 0.5,
        'rmse': 0.8,
        'r2_score': 0.92,
        'feature_count': 16,
        'training_samples': 10000,
        'model_path': 'oci://bucket/models/xgboost_v1.joblib',
        'is_active': 1
    }
    uploader.save_model_metadata(model_info)
    
    # Log to database
    uploader.log_to_db('INFO', 'data_upload', 'Successfully uploaded training data')
    
    uploader.close()
