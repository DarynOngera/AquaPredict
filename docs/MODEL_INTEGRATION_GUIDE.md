# Model Integration Guide - Precipitation Prediction

## Overview

You have 3 trained models for spatiotemporal precipitation prediction:
- **Linear Regression** - Baseline model
- **Random Forest Regressor** - Ensemble tree model  
- **XGBoost Regressor** - Gradient boosting model

This guide will help you:
1. Export models from your notebook
2. Upload to OCI Object Storage
3. Integrate with the backend API
4. Create prediction endpoints
5. Test the deployment

---

## Step 1: Export Models from Your Notebook

### 1.1 Add Export Code to Your Notebook

At the end of your training notebook, add this code:

```python
# Install joblib if not already installed
!pip install joblib

import joblib
import json
from datetime import datetime
from pathlib import Path

# Create models directory
Path('/content/models').mkdir(exist_ok=True)

# Export Linear Regression
joblib.dump(lr_model, '/content/models/linear_regression_precip_v1.joblib')
lr_metadata = {
    'model_name': 'linear_regression_precip',
    'model_type': 'LinearRegression',
    'version': 'v1',
    'created_at': datetime.now().isoformat(),
    'metrics': {
        'rmse': lr_rmse,  # Replace with your actual metric
        'r2': lr_r2,
        'mae': lr_mae
    },
    'feature_names': feature_names,  # Your feature names list
    'n_features': len(feature_names)
}
with open('/content/models/linear_regression_precip_v1_metadata.json', 'w') as f:
    json.dump(lr_metadata, f, indent=2)

# Export Random Forest
joblib.dump(rf_model, '/content/models/random_forest_precip_v1.joblib')
rf_metadata = {
    'model_name': 'random_forest_precip',
    'model_type': 'RandomForestRegressor',
    'version': 'v1',
    'created_at': datetime.now().isoformat(),
    'metrics': {
        'rmse': rf_rmse,
        'r2': rf_r2,
        'mae': rf_mae
    },
    'feature_names': feature_names,
    'n_features': len(feature_names)
}
with open('/content/models/random_forest_precip_v1_metadata.json', 'w') as f:
    json.dump(rf_metadata, f, indent=2)

# Export XGBoost
joblib.dump(xgb_model, '/content/models/xgboost_precip_v1.joblib')
xgb_metadata = {
    'model_name': 'xgboost_precip',
    'model_type': 'XGBRegressor',
    'version': 'v1',
    'created_at': datetime.now().isoformat(),
    'metrics': {
        'rmse': xgb_rmse,
        'r2': xgb_r2,
        'mae': xgb_mae
    },
    'feature_names': feature_names,
    'n_features': len(feature_names)
}
with open('/content/models/xgboost_precip_v1_metadata.json', 'w') as f:
    json.dump(xgb_metadata, f, indent=2)

# Save feature names separately
with open('/content/models/feature_names.json', 'w') as f:
    json.dump(feature_names, f, indent=2)

print("✅ All models exported successfully!")
print("\nExported files:")
!ls -lh /content/models/
```

### 1.2 Download Models from Colab/Jupyter

```python
# Zip the models directory
import shutil
shutil.make_archive('/content/aquapredict_models', 'zip', '/content/models')

# Download (in Colab)
from google.colab import files
files.download('/content/aquapredict_models.zip')
```

---

## Step 2: Upload Models to OCI Object Storage

### 2.1 From Your Local Machine

```bash
# Unzip the models
unzip aquapredict_models.zip -d models/

# Upload to OCI Object Storage
cd models/

# Upload each model file
oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file linear_regression_precip_v1.joblib \
  --name models/v1/linear_regression_precip_v1.joblib

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file linear_regression_precip_v1_metadata.json \
  --name models/v1/linear_regression_precip_v1_metadata.json

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file random_forest_precip_v1.joblib \
  --name models/v1/random_forest_precip_v1.joblib

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file random_forest_precip_v1_metadata.json \
  --name models/v1/random_forest_precip_v1_metadata.json

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file xgboost_precip_v1.joblib \
  --name models/v1/xgboost_precip_v1.joblib

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file xgboost_precip_v1_metadata.json \
  --name models/v1/xgboost_precip_v1_metadata.json

oci os object put \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --file feature_names.json \
  --name models/v1/feature_names.json
```

### 2.2 Or Use Bulk Upload Script

```bash
# Create upload script
cat > upload_models.sh << 'EOF'
#!/bin/bash
BUCKET="aquapredict-models"
NAMESPACE="frxiensafavx"
PREFIX="models/v1"

for file in *.joblib *.json; do
    echo "Uploading $file..."
    oci os object put \
        --bucket-name $BUCKET \
        --namespace $NAMESPACE \
        --file $file \
        --name $PREFIX/$file \
        --force
done

echo "✅ All models uploaded!"
EOF

chmod +x upload_models.sh
./upload_models.sh
```

---

## Step 3: Download Models to Backend Instance

SSH into your backend instance (10.0.1.95) and run:

```bash
# Create models directory
mkdir -p /opt/AquaPredict/models
cd /opt/AquaPredict/models

# Download models from OCI Object Storage
oci os object bulk-download \
  --bucket-name aquapredict-models \
  --namespace frxiensafavx \
  --prefix models/v1/ \
  --download-dir .

# Move files to correct location
mv models/v1/* .
rmdir -p models/v1

# Verify files
ls -lh
# Should see:
# - linear_regression_precip_v1.joblib
# - linear_regression_precip_v1_metadata.json
# - random_forest_precip_v1.joblib
# - random_forest_precip_v1_metadata.json
# - xgboost_precip_v1.joblib
# - xgboost_precip_v1_metadata.json
# - feature_names.json
```

---

## Step 4: Update Backend Code

### 4.1 Install Required Dependencies

On the backend instance:

```bash
cd /opt/AquaPredict
source venv/bin/activate

pip install joblib scikit-learn xgboost numpy
```

### 4.2 Update main.py to Include Prediction Router

Edit `/opt/AquaPredict/modules/backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import predictions  # Add this import

app = FastAPI(
    title="AquaPredict API",
    description="Geospatial AI for Water Resource Management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router)  # Add this line

@app.get("/")
async def root():
    return {"message": "AquaPredict API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### 4.3 Restart Backend Service

```bash
sudo systemctl restart aquapredict-api
sudo systemctl status aquapredict-api
```

---

## Step 5: Test the API

### 5.1 Check Models are Loaded

```bash
curl http://localhost:8000/api/predictions/models
```

Should return information about all 3 models.

### 5.2 Get Feature Names

```bash
curl http://localhost:8000/api/predictions/features
```

### 5.3 Make a Test Prediction

```bash
curl -X POST http://localhost:8000/api/predictions/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "precip_lag_1": 5.2,
      "precip_lag_7": 3.8,
      "precip_rolling_mean_7": 4.1,
      "precip_rolling_mean_30": 3.5,
      "ndvi_mean": 0.65,
      "lst_mean": 298.5,
      "elevation": 450.0,
      "slope": 5.2,
      "month_sin": 0.5,
      "month_cos": 0.866
    },
    "model_name": "random_forest"
  }'
```

### 5.4 Test Ensemble Prediction

```bash
curl -X POST http://localhost:8000/api/predictions/predict/ensemble \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "precip_lag_1": 5.2,
      "precip_lag_7": 3.8,
      "precip_rolling_mean_7": 4.1,
      "precip_rolling_mean_30": 3.5,
      "ndvi_mean": 0.65,
      "lst_mean": 298.5,
      "elevation": 450.0,
      "slope": 5.2,
      "month_sin": 0.5,
      "month_cos": 0.866
    }
  }'
```

### 5.5 Test from Load Balancer

```bash
curl http://152.70.18.57/api/predictions/models
```

---

## Step 6: API Documentation

Once deployed, access interactive API docs at:
- **Swagger UI**: http://152.70.18.57/docs
- **ReDoc**: http://152.70.18.57/redoc

---

## Example Feature Dictionary

Based on your training, your features likely include:

```python
features = {
    # Precipitation lags
    "precip_lag_1": 5.2,      # 1-day lag
    "precip_lag_7": 3.8,      # 7-day lag
    "precip_lag_30": 3.2,     # 30-day lag
    
    # Rolling statistics
    "precip_rolling_mean_7": 4.1,
    "precip_rolling_mean_30": 3.5,
    "precip_rolling_std_7": 1.2,
    
    # Satellite indices
    "ndvi_mean": 0.65,        # Vegetation index
    "ndwi_mean": 0.45,        # Water index
    "lst_mean": 298.5,        # Land surface temperature
    
    # Topography
    "elevation": 450.0,       # meters
    "slope": 5.2,             # degrees
    
    # Temporal features
    "month_sin": 0.5,         # Seasonal encoding
    "month_cos": 0.866,
    "day_of_year": 180
}
```

---

## Next Steps

1. **Export your models** from the notebook using the code in Step 1
2. **Upload to OCI** using the commands in Step 2
3. **Download to backend** using Step 3
4. **Test the API** using Step 5

Once this is working, we can:
- Add more sophisticated ensemble methods
- Implement model versioning
- Add model monitoring
- Create inference notebooks
- Build frontend visualization

---

## Troubleshooting

### Models not loading?

```bash
# Check if models exist
ls -lh /opt/AquaPredict/models/

# Check logs
sudo journalctl -u aquapredict-api -f

# Test model loading manually
cd /opt/AquaPredict
source venv/bin/activate
python3 -c "import joblib; model = joblib.load('models/random_forest_precip_v1.joblib'); print('Model loaded!')"
```

### Feature mismatch errors?

Make sure the feature names in your prediction request match exactly what was used during training.

### Import errors?

```bash
# Install missing packages
pip install scikit-learn xgboost joblib numpy
```

---

**Ready to start? Let me know when you've exported your models and I'll help you upload them!** 🚀
