# Model Integration - Quick Summary

## What I've Created for You

### 1. **Model Service** (`modules/backend/app/services/model_service.py`)
   - Loads and manages your 3 models (Linear Regression, Random Forest, XGBoost)
   - Handles predictions with single models or ensemble
   - Caches models in memory for fast inference

### 2. **API Endpoints** (`modules/backend/app/routers/predictions.py`)
   - `POST /api/predictions/predict` - Single model or ensemble prediction
   - `POST /api/predictions/predict/ensemble` - Get predictions from all models
   - `POST /api/predictions/predict/batch` - Batch predictions
   - `GET /api/predictions/models` - Get model info
   - `GET /api/predictions/features` - Get required features

### 3. **Export Script** (`notebooks/export_models.py`)
   - Helper to export models from your notebook
   - Saves models as `.joblib` files
   - Creates metadata JSON files

### 4. **Complete Guide** (`docs/MODEL_INTEGRATION_GUIDE.md`)
   - Step-by-step instructions
   - Code examples
   - Testing commands

---

## Your Action Items

### ✅ Step 1: Export Models from Notebook (5 minutes)

Add this to the end of your training notebook:

```python
import joblib
import json
from datetime import datetime
from pathlib import Path

# Create directory
Path('/content/models').mkdir(exist_ok=True)

# Export each model
for name, model in [('linear_regression', lr_model), 
                     ('random_forest', rf_model), 
                     ('xgboost', xgb_model)]:
    
    # Save model
    joblib.dump(model, f'/content/models/{name}_precip_v1.joblib')
    
    # Save metadata
    metadata = {
        'model_name': f'{name}_precip',
        'version': 'v1',
        'created_at': datetime.now().isoformat(),
        'metrics': {
            'rmse': 2.5,  # Replace with your actual metrics
            'r2': 0.85,
            'mae': 1.8
        },
        'feature_names': feature_names  # Your feature list
    }
    
    with open(f'/content/models/{name}_precip_v1_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

# Save feature names
with open('/content/models/feature_names.json', 'w') as f:
    json.dump(feature_names, f, indent=2)

# Zip and download
import shutil
shutil.make_archive('/content/aquapredict_models', 'zip', '/content/models')

# In Colab:
from google.colab import files
files.download('/content/aquapredict_models.zip')
```

### ✅ Step 2: Upload to OCI (2 minutes)

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

### ✅ Step 3: Deploy to Backend (3 minutes)

SSH to backend (10.0.1.95):

```bash
# Download models
mkdir -p /opt/AquaPredict/models
cd /opt/AquaPredict/models

oci os object bulk-download \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --prefix models/v1/ \
  --download-dir .

mv models/v1/* . && rmdir -p models/v1

# Install dependencies
cd /opt/AquaPredict
source venv/bin/activate
pip install joblib scikit-learn xgboost numpy

# Restart API
sudo systemctl restart aquapredict-api
```

### ✅ Step 4: Test (1 minute)

```bash
# Test models loaded
curl http://152.70.18.57/api/predictions/models

# Test prediction
curl -X POST http://152.70.18.57/api/predictions/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "precip_lag_1": 5.2,
      "precip_lag_7": 3.8,
      "ndvi_mean": 0.65,
      "elevation": 450.0
    },
    "model_name": "random_forest"
  }'
```

---

## What You'll Get

Once deployed, you'll have:

1. **REST API** for precipitation predictions
2. **3 models** available (Linear, RF, XGBoost)
3. **Ensemble predictions** (average of all 3)
4. **Batch prediction** support
5. **Interactive API docs** at http://152.70.18.57/docs

---

## Example API Usage

### Single Prediction
```python
import requests

response = requests.post(
    'http://152.70.18.57/api/predictions/predict',
    json={
        'features': {
            'precip_lag_1': 5.2,
            'precip_lag_7': 3.8,
            'precip_rolling_mean_7': 4.1,
            'ndvi_mean': 0.65,
            'lst_mean': 298.5,
            'elevation': 450.0,
            'slope': 5.2,
            'month_sin': 0.5,
            'month_cos': 0.866
        },
        'model_name': 'random_forest'
    }
)

print(response.json())
# {'prediction_mm': 4.5, 'model': 'random_forest', 'timestamp': '...'}
```

### Ensemble Prediction
```python
response = requests.post(
    'http://152.70.18.57/api/predictions/predict/ensemble',
    json={
        'features': { ... }  # Same features
    }
)

print(response.json())
# {
#   'predictions': {
#     'linear_regression': 4.2,
#     'random_forest': 4.5,
#     'xgboost': 4.6
#   },
#   'ensemble_mean': 4.43,
#   'models_used': ['linear_regression', 'random_forest', 'xgboost']
# }
```

---

## Files Created

```
AquaPredict/
├── modules/backend/app/
│   ├── services/
│   │   └── model_service.py          ✅ Model loading & inference
│   └── routers/
│       └── predictions.py             ✅ API endpoints
├── notebooks/
│   └── export_models.py               ✅ Export helper script
└── docs/
    ├── MODEL_INTEGRATION_GUIDE.md     ✅ Detailed guide
    └── MODEL_INTEGRATION_PLAN.md      ✅ Technical plan
```

---

## Next Steps After Integration

Once your models are deployed:

1. **Frontend Integration**
   - Add prediction UI to frontend
   - Visualize predictions on map
   - Show model comparison

2. **Advanced Features**
   - Model versioning (v1, v2, etc.)
   - A/B testing between models
   - Prediction confidence intervals
   - Model monitoring & drift detection

3. **Additional Models**
   - Water quality prediction
   - Flood detection
   - Drought forecasting

---

## Need Help?

Just let me know:
- "I've exported the models" → I'll help with upload
- "Models are uploaded" → I'll help with deployment
- "Having issues with X" → I'll troubleshoot

**Ready to export your models?** 🚀
