# AquaPredict Backend Deployment Guide

Complete guide for deploying the AquaPredict backend service with GEE integration and trained models.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Model Setup (Colab Integration)](#model-setup-colab-integration)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Options](#deployment-options)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Python 3.10+
- Docker & Docker Compose (for containerized deployment)
- Google Earth Engine account (optional, fallback to simulated data)

### Optional
- Trained ML models from Google Colab
- Oracle Cloud Infrastructure account (for production)
- SSL certificates (for HTTPS)

---

## Quick Start

### 1. Clone and Navigate

```bash
cd /home/ongera/projects/AquaPredict
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 3. Add Your Trained Models

If you have models trained in Google Colab:

```bash
# Create models directory
mkdir -p models

# Copy your models (from Colab downloads)
cp ~/Downloads/aquifer_classifier.pkl models/
cp ~/Downloads/recharge_forecaster.pkl models/
```

### 4. Start Services

```bash
# Using Docker Compose (recommended)
docker-compose up -d backend frontend

# Or run backend directly
cd modules/backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 0.0236, "lon": 37.9062}, "use_real_data": true}'
```

---

## Model Setup (Colab Integration)

### Training Models in Google Colab

#### 1. Aquifer Classifier (XGBoost/Random Forest)

```python
# In Google Colab notebook
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib

# Load your training data
# data = pd.read_csv('your_training_data.csv')

# Features: elevation, slope, twi, precip_mean, temp_mean, ndvi, landcover
X = data[['elevation', 'slope', 'twi', 'precip_mean', 'temp_mean', 'ndvi', 'landcover']]
y = data['aquifer_present']  # Binary: 1 = present, 0 = absent

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
from sklearn.metrics import roc_auc_score, classification_report
y_pred_proba = model.predict_proba(X_test)[:, 1]
print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.3f}")

# Save model
joblib.dump(model, 'aquifer_classifier.pkl')

# Download
from google.colab import files
files.download('aquifer_classifier.pkl')
```

#### 2. Recharge Forecaster (LSTM)

```python
# In Google Colab notebook
import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import MinMaxScaler
import joblib

# Prepare time series data
# climate_data = your historical precipitation and temperature data

# Create sequences for LSTM
def create_sequences(data, seq_length=12):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

# Scale data
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(climate_data)

# Create sequences
X, y = create_sequences(scaled_data, seq_length=12)

# Build LSTM model
model = keras.Sequential([
    keras.layers.LSTM(64, return_sequences=True, input_shape=(12, X.shape[2])),
    keras.layers.Dropout(0.2),
    keras.layers.LSTM(32),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(16, activation='relu'),
    keras.layers.Dense(1)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])
model.fit(X, y, epochs=50, batch_size=32, validation_split=0.2)

# Save model and scaler
model.save('recharge_forecaster.h5')
joblib.dump(scaler, 'recharge_scaler.pkl')

# For compatibility, wrap in a class
class RechargeForecastModel:
    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler
    
    def predict(self, X):
        X_scaled = self.scaler.transform(X)
        return self.scaler.inverse_transform(self.model.predict(X_scaled))

# Save wrapped model
wrapped_model = RechargeForecastModel(model, scaler)
joblib.dump(wrapped_model, 'recharge_forecaster.pkl')

# Download
files.download('recharge_forecaster.pkl')
```

### 3. Upload Models to Backend

**Option A: Manual Copy**
```bash
# Copy downloaded models to backend
cp ~/Downloads/aquifer_classifier.pkl /home/ongera/projects/AquaPredict/models/
cp ~/Downloads/recharge_forecaster.pkl /home/ongera/projects/AquaPredict/models/
```

**Option B: API Upload**
```bash
# Upload via API
curl -X POST "http://localhost:8000/api/v1/models/upload?model_type=aquifer" \
  -F "model_file=@aquifer_classifier.pkl"

curl -X POST "http://localhost:8000/api/v1/models/upload?model_type=recharge" \
  -F "model_file=@recharge_forecaster.pkl"
```

**Option C: From Colab Directly**
```python
# In Colab - Upload directly to your server
import requests

with open('aquifer_classifier.pkl', 'rb') as f:
    files = {'model_file': f}
    response = requests.post(
        'http://your-server:8000/api/v1/models/upload?model_type=aquifer',
        files=files
    )
    print(response.json())
```

---

## Environment Configuration

### Required Environment Variables

```bash
# .env file

# Google Earth Engine (Optional - falls back to simulated data)
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=./credentials/gee_key.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Google Earth Engine Setup

1. **Create Service Account**
   ```bash
   # Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
   # Create service account with Earth Engine permissions
   ```

2. **Download Key**
   ```bash
   # Download JSON key file
   mkdir -p credentials
   mv ~/Downloads/gee-key-*.json credentials/gee_key.json
   ```

3. **Register with Earth Engine**
   ```bash
   # Visit: https://signup.earthengine.google.com/
   # Register your service account
   ```

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Option 2: Standalone Docker

```bash
# Build image
docker build -t aquapredict-backend ./modules/backend

# Run container
docker run -d \
  --name aquapredict-backend \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/credentials:/app/credentials \
  -e GEE_SERVICE_ACCOUNT=${GEE_SERVICE_ACCOUNT} \
  aquapredict-backend
```

### Option 3: Local Development

```bash
cd modules/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 4: Production (Gunicorn)

```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
```

---

## Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-01T02:33:29Z",
  "services": {
    "gee": true,
    "models": true,
    "settings": true,
    "export": true
  }
}
```

### 2. Test Prediction (with GEE)

```bash
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "use_real_data": true
  }'
```

### 3. Test Prediction (simulated fallback)

```bash
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "use_real_data": false
  }'
```

### 4. Test Forecast

```bash
curl -X POST http://localhost:8000/api/v1/predict/recharge \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "horizon": 12,
    "use_real_data": true
  }'
```

### 5. Test Export

```bash
# Export as PDF
curl -X POST http://localhost:8000/api/v1/export \
  -H "Content-Type: application/json" \
  -d '{
    "export_type": "prediction",
    "format": "pdf",
    "data": {...prediction_data...},
    "include_metadata": true
  }' \
  --output prediction_report.pdf
```

---

## Troubleshooting

### Issue: GEE Authentication Failed

**Symptoms:**
```
GEE initialization failed: Invalid service account credentials
```

**Solutions:**
1. Verify service account email in `.env`
2. Check key file path and permissions
3. Ensure service account is registered with Earth Engine
4. Test authentication:
   ```bash
   earthengine authenticate --service-account your-account@project.iam.gserviceaccount.com --key-file credentials/gee_key.json
   ```

### Issue: Models Not Loading

**Symptoms:**
```
Model loading failed: No such file or directory
```

**Solutions:**
1. Check models directory exists: `mkdir -p models`
2. Verify model files are present: `ls -la models/`
3. Check file permissions: `chmod 644 models/*.pkl`
4. Reload models via API:
   ```bash
   curl -X POST http://localhost:8000/api/v1/models/reload
   ```

### Issue: Port Already in Use

**Symptoms:**
```
Error: Address already in use
```

**Solutions:**
1. Find process using port:
   ```bash
   lsof -i :8000
   ```
2. Kill process or use different port:
   ```bash
   uvicorn main:app --port 8001
   ```

### Issue: Slow Predictions

**Symptoms:**
- Predictions taking >10 seconds

**Solutions:**
1. Use simulated data for testing: `"use_real_data": false`
2. Increase GEE timeout in `gee_service.py`
3. Cache features in database
4. Use multiple workers: `--workers 4`

### Issue: Export PDF Fails

**Symptoms:**
```
Error: reportlab module not found
```

**Solutions:**
1. Install reportlab:
   ```bash
   pip install reportlab
   ```
2. Rebuild Docker image:
   ```bash
   docker-compose build backend
   ```

---

## Performance Optimization

### 1. Enable Caching

```python
# Add to main.py
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_prediction(lat, lon):
    # Cache predictions for frequently requested locations
    pass
```

### 2. Use Multiple Workers

```bash
# Production deployment
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

### 3. Database Connection Pooling

```python
# Add connection pooling for Oracle ADB
# See oracle_database.py for implementation
```

---

## Monitoring

### Health Checks

```bash
# Add to crontab for monitoring
*/5 * * * * curl -f http://localhost:8000/health || echo "Backend down!"
```

### Logs

```bash
# Docker logs
docker-compose logs -f backend

# Application logs
tail -f logs/backend.log
```

### Metrics

```bash
# Check model status
curl http://localhost:8000/api/v1/models

# Check data sources
curl http://localhost:8000/api/v1/data/sources
```

---

## Next Steps

1. ✅ Backend deployed and running
2. ✅ Models loaded from Colab
3. ✅ GEE integration working (or fallback enabled)
4. 🔄 Test all endpoints
5. 🔄 Configure production settings
6. 🔄 Set up monitoring and alerts
7. 🔄 Deploy to cloud (OCI/AWS/GCP)

## Support

- **Documentation**: `/modules/backend/README.md`
- **API Docs**: `http://localhost:8000/api/docs`
- **Issues**: Check logs and troubleshooting section above
