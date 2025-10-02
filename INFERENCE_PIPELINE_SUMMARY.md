# 🎯 Inference Pipeline - Ready to Integrate!

## What I've Built for You

### **Complete End-to-End Inference Pipeline**

```
User clicks map → Extract features from Earth Engine → Run model → Return prediction
```

---

## 📁 Files Created

### 1. **Inference Pipeline** (`modules/backend/app/services/inference_pipeline.py`)
   - Extracts CHIRPS precipitation features (current + lags + rolling stats)
   - Extracts ERA5 climate features (temp, pressure, wind)
   - Extracts SRTM topography (elevation, slope)
   - Builds feature vector matching your training format
   - Makes predictions using your trained models

### 2. **API Endpoints** (`modules/backend/app/routers/inference.py`)
   - `POST /api/inference/predict` - Single point prediction
   - `POST /api/inference/predict/batch` - Multiple points
   - `POST /api/inference/extract-features` - Feature extraction only
   - `GET /api/inference/features` - Feature information

### 3. **Integration Guide** (`docs/INFERENCE_PIPELINE_GUIDE.md`)
   - Complete step-by-step setup instructions
   - Model export code for your notebook
   - Deployment procedures
   - Frontend integration examples
   - Troubleshooting guide

---

## 🚀 How It Works

### **User Flow**

1. **User clicks on map** → Frontend sends `{lon, lat, date}` to API
2. **Backend receives request** → Inference pipeline activates
3. **Earth Engine queries**:
   - CHIRPS: Gets precipitation for selected date + past 30 days
   - ERA5: Gets climate variables for that date
   - SRTM: Gets elevation and slope for that location
4. **Feature engineering**:
   - Calculates lag features (1, 3, 7, 14, 30 days)
   - Calculates rolling means and std (7, 14, 30 days)
   - Adds temporal features (month, day of year with sin/cos encoding)
5. **Model prediction**:
   - Loads your trained model (.joblib)
   - Runs prediction on feature vector
6. **Returns result** → Frontend displays prediction on map

---

## 📋 Your Action Items

### **Step 1: Export Models from Notebook** (15 minutes)

Add this to your training notebook:

```python
import joblib
import json
from datetime import datetime

# Export models
for name, model in [('linear_regression', lr_model), 
                     ('random_forest', rf_model), 
                     ('xgboost', xgb_model)]:
    
    joblib.dump(model, f'{name}_precip_v1.joblib')
    
    metadata = {
        'model_name': f'{name}_precip',
        'version': 'v1',
        'created_at': datetime.now().isoformat(),
        'metrics': {'rmse': your_rmse, 'r2': your_r2, 'mae': your_mae},
        'feature_names': feature_names  # Your feature list
    }
    
    with open(f'{name}_precip_v1_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

# Save feature names
with open('feature_names.json', 'w') as f:
    json.dump(feature_names, f, indent=2)

# Download from Colab
from google.colab import files
import shutil
shutil.make_archive('models', 'zip', '.')
files.download('models.zip')
```

### **Step 2: Upload Models to Server** (5 minutes)

```bash
# Upload to OCI Object Storage
cd models/
for file in *.joblib *.json; do
    oci os object put \
        --bucket-name aquapredict-models \
        --namespace frxiensafavx \
        --file $file \
        --name models/v1/$file
done

# Download to server
ssh opc@92.5.94.60
mkdir -p /opt/AquaPredict/models
cd /opt/AquaPredict/models
oci os object bulk-download \
    --bucket-name aquapredict-models \
    --namespace frxiensafavx \
    --prefix models/v1/ \
    --download-dir .
```

### **Step 3: Install Dependencies** (5 minutes)

```bash
cd /opt/AquaPredict
source venv/bin/activate
pip install earthengine-api scikit-learn xgboost joblib pandas numpy
```

### **Step 4: Configure GEE Credentials** (2 minutes)

```bash
mkdir -p /opt/AquaPredict/credentials
nano /opt/AquaPredict/credentials/gee-service-account.json
# Paste your GEE service account JSON

# Add to .env
echo "GEE_SERVICE_ACCOUNT_JSON=/opt/AquaPredict/credentials/gee-service-account.json" >> /opt/AquaPredict/.env
```

### **Step 5: Update Backend** (2 minutes)

Edit `/opt/AquaPredict/modules/backend/main.py`:

```python
from app.routers import predictions, inference  # Add inference

app.include_router(inference.router)  # Add this line
```

Restart:
```bash
sudo systemctl restart aquapredict-api
```

### **Step 6: Test** (5 minutes)

```bash
# Test prediction
curl -X POST http://92.5.94.60/api/inference/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15",
    "model_name": "random_forest"
  }'
```

---

## 🎨 Frontend Integration

### **Map Click Handler**

```typescript
// In your map component
async function handleMapClick(event: MapClickEvent) {
  const {lng, lat} = event.lngLat;
  
  try {
    const response = await fetch('/api/inference/predict', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        lon: lng,
        lat: lat,
        date: selectedDate || new Date().toISOString().split('T')[0],
        model_name: 'random_forest'
      })
    });
    
    const result = await response.json();
    
    // Display prediction
    showPredictionPopup({
      location: {lng, lat},
      prediction: result.prediction_mm,
      date: result.date,
      model: result.model
    });
    
  } catch (error) {
    console.error('Prediction failed:', error);
  }
}
```

---

## 📊 Features Extracted

The pipeline extracts **27 features** for each prediction:

### **CHIRPS Precipitation** (11 features)
- Current day precipitation
- Lag features: 1, 3, 7, 14, 30 days
- Rolling means: 7, 14, 30 days
- Rolling std: 7, 14 days

### **ERA5 Climate** (8 features)
- Temperature (mean, max, min)
- Dewpoint temperature
- Surface pressure
- Total precipitation
- Wind components (U, V)

### **SRTM Topography** (2 features)
- Elevation
- Slope

### **Temporal** (6 features)
- Day of year
- Month
- Cyclical encodings (sin/cos)

---

## 🔍 API Examples

### **Single Point Prediction**

```bash
curl -X POST http://92.5.94.60/api/inference/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15",
    "model_name": "random_forest"
  }'
```

Response:
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

### **Batch Predictions**

```bash
curl -X POST http://92.5.94.60/api/inference/predict/batch \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {"lon": 36.8219, "lat": -1.2921, "date": "2024-01-15"},
      {"lon": 36.8500, "lat": -1.3000, "date": "2024-01-15"}
    ],
    "model_name": "xgboost"
  }'
```

### **Extract Features Only**

```bash
curl -X POST http://92.5.94.60/api/inference/extract-features \
  -H "Content-Type: application/json" \
  -d '{
    "lon": 36.8219,
    "lat": -1.2921,
    "date": "2024-01-15"
  }'
```

---

## ✅ What's Ready

- ✅ Complete inference pipeline code
- ✅ Earth Engine integration
- ✅ Feature extraction (CHIRPS, ERA5, SRTM)
- ✅ Model loading and prediction
- ✅ REST API endpoints
- ✅ Batch prediction support
- ✅ Error handling and logging
- ✅ API documentation
- ✅ Integration guide

---

## ⏳ What You Need to Provide

1. **Trained models** (.joblib files)
2. **Model metadata** (metrics, feature names)
3. **Feature names list** (exact order from training)
4. **GEE service account** (you already have this)

---

## 📚 Documentation

- **Full Guide**: `docs/INFERENCE_PIPELINE_GUIDE.md`
- **API Docs**: http://92.5.94.60/api/docs (after deployment)
- **Model Integration**: `MODEL_INTEGRATION_SUMMARY.md`

---

## 🎯 Next Steps

1. **Export models** from your training notebook
2. **Upload to OCI** Object Storage
3. **Download to server** and configure
4. **Test predictions** via API
5. **Integrate with frontend** map component
6. **Deploy and enjoy** real-time predictions! 🎉

---

## 💡 Key Points

- **Real-time**: Features extracted on-demand from Earth Engine
- **Scalable**: Supports batch predictions for multiple points
- **Flexible**: Works with any sklearn/xgboost model
- **Production-ready**: Error handling, logging, API docs included
- **Easy to test**: Interactive API docs at `/api/docs`

---

**Ready to integrate your models? Follow the guide in `docs/INFERENCE_PIPELINE_GUIDE.md`!** 🚀
