

# Inference Pipeline Integration Guide

## Overview

This guide shows you how to integrate your trained models and artifacts with the inference pipeline for real-time predictions from the map UI.

---

## Architecture Flow

```
┌─────────────┐
│   Frontend  │
│   Map UI    │
└──────┬──────┘
       │ User clicks point (lon, lat)
       │ Selects date (optional)
       ▼
┌─────────────────────────────────────┐
│  POST /api/inference/predict        │
│  {lon: 36.82, lat: -1.29, date: ...}│
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Inference Pipeline                 │
│  1. Extract CHIRPS features         │
│  2. Extract ERA5 features           │
│  3. Extract SRTM features           │
│  4. Build feature vector            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Trained Model (.joblib)            │
│  - Linear Regression                │
│  - Random Forest                    │
│  - XGBoost                          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Response                           │
│  {prediction_mm: 12.5, ...}         │
└─────────────────────────────────────┘
```

---

## Step 1: Prepare Your Artifacts

### 1.1 Export Models from Notebook

In your training notebook, add this at the end:

```python
import joblib
import json
from datetime import datetime

# Your trained models
models = {
    'linear_regression': lr_model,
    'random_forest': rf_model,
    'xgboost': xgb_model
}

# Your feature names (CRITICAL - must match exactly!)
feature_names = [
    # Precipitation features (CHIRPS)
    'precip_current',
    'precip_lag_1',
    'precip_lag_3',
    'precip_lag_7',
    'precip_lag_14',
    'precip_lag_30',
    'precip_rolling_mean_7',
    'precip_rolling_mean_14',
    'precip_rolling_mean_30',
    'precip_rolling_std_7',
    'precip_rolling_std_14',
    
    # Climate features (ERA5)
    'temp_2m',
    'temp_2m_max',
    'temp_2m_min',
    'dewpoint_2m',
    'surface_pressure',
    'total_precipitation_era5',
    'u_wind_10m',
    'v_wind_10m',
    
    # Topography (SRTM)
    'elevation',
    'slope',
    
    # Temporal features
    'day_of_year',
    'month',
    'month_sin',
    'month_cos',
    'day_of_year_sin',
    'day_of_year_cos',
]

# Export each model
for name, model in models.items():
    # Save model
    joblib.dump(model, f'{name}_precip_v1.joblib')
    
    # Save metadata
    metadata = {
        'model_name': f'{name}_precip',
        'version': 'v1',
        'created_at': datetime.now().isoformat(),
        'metrics': {
            'rmse': model_rmse,  # Replace with your actual metrics
            'r2': model_r2,
            'mae': model_mae
        },
        'feature_names': feature_names,
        'n_features': len(feature_names)
    }
    
    with open(f'{name}_precip_v1_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

# Save feature names separately
with open('feature_names.json', 'w') as f:
    json.dump(feature_names, f, indent=2)

print("✅ Models exported!")
```

### 1.2 Download Artifacts

```python
# In Colab
from google.colab import files
import shutil

# Zip everything
shutil.make_archive('aquapredict_models', 'zip', '.')

# Download
files.download('aquapredict_models.zip')
```

---

## Step 2: Upload Models to Server

### 2.1 Upload to OCI Object Storage

```bash
# Unzip locally
unzip aquapredict_models.zip -d models/

# Upload to OCI
cd models/
for file in *.joblib *.json; do
    oci os object put \
        --bucket-name aquapredict-models \
        --namespace frxiensafavx \
        --file $file \
        --name models/v1/$file \
        --force
done
```

### 2.2 Download to Server

SSH to your server (92.5.94.60):

```bash
# Create models directory
mkdir -p /opt/AquaPredict/models
cd /opt/AquaPredict/models

# Download from OCI
oci os object bulk-download \
    --bucket-name aquapredict-models \
    --namespace frxiensafavx \
    --prefix models/v1/ \
    --download-dir .

# Move files
mv models/v1/* .
rmdir -p models/v1

# Verify
ls -lh
# Should see:
# - linear_regression_precip_v1.joblib
# - random_forest_precip_v1.joblib
# - xgboost_precip_v1.joblib
# - *_metadata.json files
# - feature_names.json
```

---

## Step 3: Install Dependencies

```bash
cd /opt/AquaPredict
source venv/bin/activate

# Install Earth Engine
pip install earthengine-api

# Install ML libraries
pip install scikit-learn xgboost joblib pandas numpy

# Install other dependencies
pip install -r modules/backend/requirements.txt
```

---

## Step 4: Configure GEE Service Account

### 4.1 Upload Service Account JSON

```bash
# Create credentials directory
mkdir -p /opt/AquaPredict/credentials

# Upload your GEE service account JSON
# (Use scp or paste content)
nano /opt/AquaPredict/credentials/gee-service-account.json
# Paste your JSON content

chmod 600 /opt/AquaPredict/credentials/gee-service-account.json
```

### 4.2 Update Environment File

```bash
nano /opt/AquaPredict/.env

# Add this line:
GEE_SERVICE_ACCOUNT_JSON=/opt/AquaPredict/credentials/gee-service-account.json
```

---

## Step 5: Update Backend to Use Inference Pipeline

### 5.1 Update main.py

Edit `/opt/AquaPredict/modules/backend/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import predictions, inference  # Add inference

app = FastAPI(
    title="AquaPredict API",
    description="Geospatial AI for Water Resource Management",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router)
app.include_router(inference.router)  # Add this

@app.get("/")
async def root():
    return {"message": "AquaPredict API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 5.2 Restart Backend

```bash
sudo systemctl restart aquapredict-api
sudo systemctl status aquapredict-api
```

---

## Step 6: Test the Pipeline

### 6.1 Test Feature Extraction

```bash
curl -X POST http://localhost:8000/api/inference/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15"
  }'
```

### 6.2 Test Prediction

```bash
curl -X POST http://localhost:8000/api/inference/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15",
    "model_name": "random_forest"
  }'
```

Expected response:
```json
{
  "prediction_mm": 12.5,
  "location": {"lon": 36.8219, "lat": -1.2921},
  "date": "2024-01-15",
  "model": "random_forest",
  "features_extracted": 27,
  "status": "success",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## Step 7: Frontend Integration

### 7.1 Update Frontend Map Component

In your frontend map component:

```typescript
// When user clicks on map
async function handleMapClick(lon: number, lat: number) {
  const response = await fetch('http://92.5.94.60/api/inference/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      lon,
      lat,
      date: selectedDate || new Date().toISOString().split('T')[0],
      model_name: 'random_forest'
    })
  });
  
  const result = await response.json();
  
  // Display prediction on map
  showPrediction(result.prediction_mm, lon, lat);
}
```

---

## Troubleshooting

### Models Not Loading

```bash
# Check if models exist
ls -lh /opt/AquaPredict/models/

# Check logs
sudo journalctl -u aquapredict-api -n 100

# Test model loading manually
cd /opt/AquaPredict
source venv/bin/activate
python3 << EOF
import joblib
model = joblib.load('models/random_forest_precip_v1.joblib')
print("Model loaded:", type(model))
EOF
```

### Earth Engine Not Initialized

```bash
# Check GEE credentials
cat /opt/AquaPredict/credentials/gee-service-account.json

# Test GEE manually
python3 << EOF
import ee
credentials = ee.ServiceAccountCredentials(
    email=None,
    key_file='/opt/AquaPredict/credentials/gee-service-account.json'
)
ee.Initialize(credentials)
print("✓ Earth Engine initialized")
EOF
```

### Feature Mismatch Error

Make sure your `feature_names` in the training notebook **exactly match** the features in `inference_pipeline.py`.

Check with:
```bash
curl http://localhost:8000/api/inference/features
```

---

## API Documentation

Once deployed, view interactive API docs at:
- **Swagger UI**: http://92.5.94.60/api/docs
- **ReDoc**: http://92.5.94.60/api/redoc

---

## Next Steps

1. ✅ Export models from notebook
2. ✅ Upload to OCI Object Storage
3. ✅ Download to server
4. ✅ Configure GEE credentials
5. ✅ Test inference pipeline
6. ✅ Integrate with frontend map
7. ✅ Deploy and test end-to-end

**You're ready to make real-time predictions from your map!** 🎉
