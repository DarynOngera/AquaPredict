# Model Artifacts Integration Guide

## Overview

Your trained models (.joblib files) are ready for inference. They expect **precomputed features** including longitude, latitude, temporal features, and meteorological variables.

---

## Model Artifacts Structure

### **What You Have:**

```
models/
├── linear_regression_precip_v1.joblib
├── random_forest_precip_v1.joblib
├── xgboost_precip_v1.joblib
├── linear_regression_precip_v1_metadata.json
├── random_forest_precip_v1_metadata.json
└── xgboost_precip_v1_metadata.json
```

### **Model Features (in order):**

1. **longitude** - Location longitude
2. **latitude** - Location latitude
3. **sin_day** - Cyclical day of year (sin)
4. **cos_day** - Cyclical day of year (cos)
5. **lag1_precip** - Precipitation 1 day ago
6. **lag3_precip** - Precipitation 3 days ago
7. **lag7_precip** - Precipitation 7 days ago
8. **roll3_precip** - 3-day rolling mean precipitation
9. **roll7_precip** - 7-day rolling mean precipitation
10. **temperature_2m** - ERA5 2m temperature
11. **dewpoint_temperature_2m** - ERA5 dewpoint
12. **surface_pressure** - ERA5 surface pressure
13. **u_wind_10m** - ERA5 U wind component
14. **v_wind_10m** - ERA5 V wind component
15. **total_precipitation** - ERA5 total precipitation

---

## Deployment Steps

### **Step 1: Upload Models to Server**

```bash
# From your local machine
cd ~/Downloads  # or wherever your models are

# Upload to OCI Object Storage
for file in *.joblib *.json; do
    oci os object put \
        --bucket-name aquapredict-models \
        --namespace frxiensafavx \
        --file $file \
        --name models/v1/$file \
        --force
done
```

### **Step 2: Download to Server**

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

# Move files to correct location
mv models/v1/* .
rmdir -p models/v1 2>/dev/null || true

# Verify
ls -lh
```

Expected output:
```
-rw-r--r-- 1 opc opc  2.1M Oct  2 12:00 linear_regression_precip_v1.joblib
-rw-r--r-- 1 opc opc  1.2K Oct  2 12:00 linear_regression_precip_v1_metadata.json
-rw-r--r-- 1 opc opc   15M Oct  2 12:00 random_forest_precip_v1.joblib
-rw-r--r-- 1 opc opc  1.2K Oct  2 12:00 random_forest_precip_v1_metadata.json
-rw-r--r-- 1 opc opc   12M Oct  2 12:00 xgboost_precip_v1.joblib
-rw-r--r-- 1 opc opc  1.2K Oct  2 12:00 xgboost_precip_v1_metadata.json
```

### **Step 3: Install Dependencies**

```bash
cd /opt/AquaPredict
source venv/bin/activate

# Install ML libraries
pip install scikit-learn xgboost joblib pandas numpy

# Verify installation
python3 << EOF
import joblib
import sklearn
import xgboost
print("✓ All libraries installed")
EOF
```

### **Step 4: Test Model Loading**

```bash
cd /opt/AquaPredict
source venv/bin/activate

python3 << 'EOF'
import joblib
import numpy as np
import pandas as pd

# Load model
model = joblib.load('models/random_forest_precip_v1.joblib')
print(f"✓ Model loaded: {type(model)}")

# Create test feature vector
features = pd.DataFrame([{
    'longitude': 36.8219,
    'latitude': -1.2921,
    'sin_day': 0.5,
    'cos_day': 0.866,
    'lag1_precip': 0.0,
    'lag3_precip': 0.0,
    'lag7_precip': 0.0,
    'roll3_precip': 0.0,
    'roll7_precip': 0.0,
    'temperature_2m': 0.0,
    'dewpoint_temperature_2m': 0.0,
    'surface_pressure': 0.0,
    'u_wind_10m': 0.0,
    'v_wind_10m': 0.0,
    'total_precipitation': 0.0,
}])

# Make prediction
prediction = model.predict(features)[0]
print(f"✓ Test prediction: {prediction:.2f} mm")
EOF
```

### **Step 5: Update Backend Code**

The inference pipeline is already configured to work with your artifacts!

Edit `/opt/AquaPredict/modules/backend/main.py` to include the inference router:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inference  # Add this

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

# Include inference router
app.include_router(inference.router)

@app.get("/")
async def root():
    return {"message": "AquaPredict API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### **Step 6: Restart Backend**

```bash
sudo systemctl restart aquapredict-api
sudo systemctl status aquapredict-api

# Check logs
sudo journalctl -u aquapredict-api -n 50
```

---

## Testing the API

### **Test 1: Single Point Prediction**

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
  "prediction_mm": 5.2,
  "location": {"lon": 36.8219, "lat": -1.2921},
  "date": "2024-01-15",
  "model": "random_forest",
  "features_extracted": 15,
  "status": "success",
  "timestamp": "2024-10-02T12:30:00"
}
```

### **Test 2: Batch Predictions**

```bash
curl -X POST http://localhost:8000/api/inference/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {"lon": 36.8219, "lat": -1.2921, "date": "2024-01-15"},
      {"lon": 36.8500, "lat": -1.3000, "date": "2024-01-15"},
      {"lon": 36.8700, "lat": -1.3200, "date": "2024-01-15"}
    ],
    "model_name": "xgboost"
  }'
```

### **Test 3: Extract Features Only**

```bash
curl -X POST http://localhost:8000/api/inference/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15"
  }'
```

### **Test 4: Get Feature Info**

```bash
curl http://localhost:8000/api/inference/features
```

---

## How It Works

### **For Known Locations (with historical data):**

1. User clicks map → sends `{lon, lat, date}`
2. Pipeline checks if location exists in historical data
3. Uses precomputed features (lag_precip, ERA5 vars, etc.)
4. Runs model prediction
5. Returns result

### **For Unknown Locations (new coordinates):**

1. User clicks map → sends `{lon, lat, date}`
2. Pipeline doesn't find location in historical data
3. Uses **default values (zeros)** for meteorological features
4. Still uses lon, lat, and temporal features (sin_day, cos_day)
5. Runs model prediction
6. Returns result

> **Note**: Predictions for unseen locations will be less accurate since meteorological features default to zero. To improve this, you can:
> - Add more historical data
> - Implement spatial interpolation
> - Query Earth Engine in real-time (future enhancement)

---

## Optional: Load Historical Data

If you have a CSV with historical features, you can load it:

```python
# In your backend startup
import pandas as pd
from app.services.inference_pipeline import get_inference_pipeline

# Load historical data
historical_data = pd.read_csv('/opt/AquaPredict/data/historical_features.csv')

# Initialize pipeline with historical data
pipeline = get_inference_pipeline(historical_data)
```

---

## Frontend Integration

### **Map Click Handler**

```typescript
async function handleMapClick(lng: number, lat: number) {
  const selectedDate = dateInput.value || new Date().toISOString().split('T')[0];
  
  try {
    const response = await fetch('/api/inference/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        lon: lng,
        lat: lat,
        date: selectedDate,
        model_name: 'random_forest'  // or let user select
      })
    });
    
    const result = await response.json();
    
    // Display prediction on map
    showPredictionMarker({
      coordinates: [lng, lat],
      prediction: result.prediction_mm,
      date: result.date,
      model: result.model
    });
    
    // Show popup
    showPopup(`
      <h3>Precipitation Prediction</h3>
      <p><strong>${result.prediction_mm.toFixed(2)} mm</strong></p>
      <p>Location: ${lat.toFixed(4)}, ${lng.toFixed(4)}</p>
      <p>Date: ${result.date}</p>
      <p>Model: ${result.model}</p>
    `);
    
  } catch (error) {
    console.error('Prediction failed:', error);
    showError('Failed to get prediction');
  }
}
```

---

## Model Selection

You have 3 models available. Choose based on your metrics:

```bash
# Check model metrics
cat /opt/AquaPredict/models/random_forest_precip_v1_metadata.json
```

**Typical characteristics:**
- **Linear Regression**: Fast, interpretable, baseline
- **Random Forest**: Good accuracy, robust, slower
- **XGBoost**: Best accuracy, handles complex patterns, slowest

---

## Troubleshooting

### Models Not Loading

```bash
# Check if models exist
ls -lh /opt/AquaPredict/models/*.joblib

# Test loading manually
cd /opt/AquaPredict
source venv/bin/activate
python3 -c "import joblib; m = joblib.load('models/random_forest_precip_v1.joblib'); print('OK')"
```

### Feature Mismatch Error

```bash
# Check feature names in your model
python3 << 'EOF'
import joblib
model = joblib.load('models/random_forest_precip_v1.joblib')
print("Expected features:", model.feature_names_in_)
EOF

# Compare with pipeline features
curl http://localhost:8000/api/inference/features
```

### Prediction Returns NaN

- Check if model file is corrupted
- Verify all features are numeric
- Check for infinity values in features

---

## API Documentation

View interactive API docs:
- **Swagger UI**: http://92.5.94.60/api/docs
- **ReDoc**: http://92.5.94.60/api/redoc

---

## Next Steps

1. ✅ Upload models to server
2. ✅ Test predictions via API
3. ✅ Integrate with frontend map
4. ⏳ Add historical data (optional, for better accuracy)
5. ⏳ Monitor prediction performance
6. ⏳ Add model versioning

**Your models are ready to serve predictions!** 🎉
