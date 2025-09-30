# Orchestration Module

Apache Airflow DAGs for orchestrating the AquaPredict data pipeline.

## Features

- **Automated Pipelines**: End-to-end data processing workflows
- **Scheduling**: Daily/weekly/monthly data updates
- **Monitoring**: Pipeline health and performance tracking
- **Error Handling**: Retry logic and alerting
- **Parallel Processing**: Distributed task execution

## DAGs

### 1. Data Ingestion DAG (`data_ingestion_dag.py`)

**Schedule**: Daily at 2:00 AM UTC

**Tasks**:
1. `fetch_precipitation` - Fetch CHIRPS data from GEE
2. `fetch_temperature` - Fetch ERA5 data
3. `fetch_elevation` - Fetch SRTM data (once)
4. `fetch_landcover` - Fetch ESA WorldCover
5. `validate_data` - Data quality checks
6. `store_raw_data` - Store in OCI Object Storage

### 2. Feature Engineering DAG (`feature_engineering_dag.py`)

**Schedule**: Daily at 4:00 AM UTC (after ingestion)

**Tasks**:
1. `load_raw_data` - Load from Object Storage
2. `preprocess_data` - Clean and normalize
3. `compute_twi` - Calculate TWI
4. `compute_spi` - Calculate SPI (multiple timescales)
5. `compute_spei` - Calculate SPEI
6. `compute_temporal_features` - Temporal statistics
7. `store_features` - Store in Oracle ADB

### 3. Model Training DAG (`model_training_dag.py`)

**Schedule**: Weekly on Sunday at 3:00 AM UTC

**Tasks**:
1. `load_training_data` - Load features and labels
2. `train_aquifer_classifier` - Train RF/XGBoost
3. `train_recharge_forecaster` - Train LSTM
4. `evaluate_models` - Compute metrics
5. `deploy_models` - Deploy to OCI Model Deployment
6. `update_api` - Reload models in API

### 4. Prediction DAG (`prediction_dag.py`)

**Schedule**: Daily at 6:00 AM UTC

**Tasks**:
1. `load_features` - Load latest features
2. `batch_predict_aquifer` - Predict for all grid points
3. `batch_forecast_recharge` - Forecast recharge
4. `store_predictions` - Store in database
5. `generate_reports` - Generate ISO reports
6. `send_notifications` - Email/Slack notifications

## DAG Configuration

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'aquapredict',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['admin@aquapredict.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_ingestion',
    default_args=default_args,
    description='Fetch geospatial data from GEE',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['ingestion', 'gee'],
)
```

## Task Dependencies

```python
# Linear pipeline
fetch_precip >> preprocess >> compute_features >> train_model >> deploy

# Parallel tasks
[fetch_precip, fetch_temp, fetch_elev] >> validate >> store

# Branching
validate >> [process_success, process_failure]
```

## Monitoring

- **Airflow UI**: http://localhost:8080
- **Task Logs**: View in Airflow UI or logs directory
- **Metrics**: Task duration, success rate, resource usage
- **Alerts**: Email/Slack on failures

## Deployment

### Local Development

```bash
docker-compose up airflow-webserver airflow-scheduler
```

### OCI Deployment

Deploy Airflow on OKE with Helm:

```bash
helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --set executor=CeleryExecutor \
  --set postgresql.enabled=true \
  --set redis.enabled=true
```

## Testing

```bash
# Test DAG
airflow dags test data_ingestion 2024-01-01

# Test task
airflow tasks test data_ingestion fetch_precipitation 2024-01-01
```
