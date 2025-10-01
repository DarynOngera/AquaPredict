# 🌍 AquaPredict - Real Data Setup Guide

## **Moving from Simulation to Real Data**

This guide will help you transition from simulated data to real satellite and geospatial data for Kenya.

---

## 📋 **Prerequisites**

### **1. Google Earth Engine Access**
- [ ] Google Earth Engine account created
- [ ] Service account created in GCP
- [ ] Service account key downloaded
- [ ] Earth Engine API enabled

### **2. Required Credentials**
- [ ] GEE service account email
- [ ] GEE private key JSON file
- [ ] Oracle Cloud credentials configured
- [ ] OCI Object Storage buckets created

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Setup Google Earth Engine**

#### **Create Service Account**

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Create Project** (if needed): "AquaPredict"
3. **Enable Earth Engine API**:
   - Navigate to: APIs & Services → Library
   - Search: "Earth Engine API"
   - Click: Enable

4. **Create Service Account**:
   - Navigate to: IAM & Admin → Service Accounts
   - Click: "Create Service Account"
   - Name: `aquapredict-gee`
   - Role: `Earth Engine Resource Admin`
   - Click: "Create Key" → JSON
   - Save as: `gee-service-account.json`

5. **Register Service Account with Earth Engine**:
   ```bash
   # Install Earth Engine CLI
   pip install earthengine-api
   
   # Authenticate
   earthengine authenticate
   
   # Register service account
   earthengine set_project your-gcp-project-id
   ```

#### **Configure Credentials**

```bash
# Create credentials directory
mkdir -p credentials

# Copy service account key
cp ~/Downloads/gee-service-account.json credentials/gee_key.json

# Set permissions
chmod 600 credentials/gee_key.json
```

#### **Update Environment Variables**

Add to `.env`:
```bash
# Google Earth Engine
GEE_SERVICE_ACCOUNT=aquapredict-gee@your-project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_PATH=./credentials/gee_key.json
GEE_PROJECT_ID=your-gcp-project-id
```

---

### **Step 2: Fetch Real Data from GEE**

#### **Test GEE Connection**

```python
# test_gee_connection.py
import ee
import json

# Load service account credentials
with open('credentials/gee_key.json') as f:
    credentials = json.load(f)

# Initialize Earth Engine
credentials_obj = ee.ServiceAccountCredentials(
    credentials['client_email'],
    'credentials/gee_key.json'
)
ee.Initialize(credentials_obj)

# Test: Get CHIRPS precipitation
chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
print("✅ Connected to Google Earth Engine!")
print(f"CHIRPS collection size: {chirps.size().getInfo()}")
```

Run test:
```bash
python test_gee_connection.py
```

#### **Fetch Kenya Data**

**Option A: Quick Sample (1 month)**
```bash
cd modules/data-ingestion

python main.py \
  --dataset all \
  --start-date 2023-01-01 \
  --end-date 2023-01-31 \
  --output-dir ../../data/raw \
  --format geotiff
```

**Option B: Full Dataset (4 years)**
```bash
python main.py \
  --dataset all \
  --start-date 2020-01-01 \
  --end-date 2023-12-31 \
  --output-dir ../../data/raw \
  --format geotiff
```

**Expected Output**:
```
data/raw/
├── kenya_precipitation.tif    # CHIRPS daily precipitation
├── kenya_temperature.tif      # ERA5 temperature
├── kenya_elevation.tif        # SRTM elevation
└── kenya_landcover.tif        # ESA WorldCover
```

---

### **Step 3: Upload to OCI Object Storage**

```bash
# Upload raw data to OCI
python << 'EOF'
import sys
sys.path.append('modules/common')
from oci_storage import DataStorageManager
import os

storage = DataStorageManager()

# Upload each file
files = [
    'data/raw/kenya_precipitation.tif',
    'data/raw/kenya_temperature.tif',
    'data/raw/kenya_elevation.tif',
    'data/raw/kenya_landcover.tif'
]

for file_path in files:
    if os.path.exists(file_path):
        dataset_name = os.path.basename(file_path).replace('kenya_', '').replace('.tif', '')
        url = storage.save_raw_data(
            dataset_name=dataset_name,
            date='2023-01-01',
            file_path=file_path
        )
        print(f"✅ Uploaded: {file_path} → {url}")
    else:
        print(f"⚠️  File not found: {file_path}")
EOF
```

---

### **Step 4: Preprocess Real Data**

```bash
cd modules/preprocessing

# Preprocess precipitation
python main.py \
  --input-file ../../data/raw/kenya_precipitation.tif \
  --output-file ../../data/processed/kenya_precipitation_processed.tif \
  --operations clean,normalize,resample

# Preprocess temperature
python main.py \
  --input-file ../../data/raw/kenya_temperature.tif \
  --output-file ../../data/processed/kenya_temperature_processed.tif \
  --operations clean,normalize,resample

# Preprocess elevation
python main.py \
  --input-file ../../data/raw/kenya_elevation.tif \
  --output-file ../../data/processed/kenya_elevation_processed.tif \
  --operations clean,normalize
```

---

### **Step 5: Generate Real Features**

```bash
cd modules/feature-engineering

# Generate all features
python main.py \
  --dem-file ../../data/processed/kenya_elevation_processed.tif \
  --precip-file ../../data/processed/kenya_precipitation_processed.tif \
  --temp-file ../../data/processed/kenya_temperature_processed.tif \
  --output-dir ../../data/features \
  --save-to-adb
```

**Features Generated**:
- ✅ TWI (Topographic Wetness Index)
- ✅ TPI (Topographic Position Index)
- ✅ Slope, Aspect, Curvature
- ✅ SPI (1, 3, 6, 12 months)
- ✅ SPEI (3, 6, 12 months)
- ✅ PET (Potential Evapotranspiration)

---

### **Step 6: Prepare Training Data**

#### **Create Training Dataset from Real Data**

```python
# create_training_dataset.py
import sys
sys.path.append('modules/prediction-service')
from oracle_database import OracleADBClient
import asyncio
import pandas as pd
import numpy as np

async def create_training_data():
    db = OracleADBClient()
    
    # Query features from Oracle ADB
    async with db.get_connection() as conn:
        async with conn.cursor() as cursor:
            sql = """
            SELECT 
                l.latitude,
                l.longitude,
                f.elevation,
                f.slope,
                f.aspect,
                f.twi,
                f.tpi,
                f.precip_mean,
                f.precip_std,
                f.temp_mean,
                f.temp_std,
                f.spi_1,
                f.spi_3,
                f.spi_6,
                f.spi_12,
                f.spei_3,
                f.spei_6,
                f.spei_12
            FROM features f
            JOIN locations l ON f.location_id = l.location_id
            WHERE f.data_quality_score > 0.7
            """
            
            await cursor.execute(sql)
            rows = await cursor.fetchall()
            
            # Create DataFrame
            columns = [
                'latitude', 'longitude', 'elevation', 'slope', 'aspect',
                'twi', 'tpi', 'precip_mean', 'precip_std', 'temp_mean',
                'temp_std', 'spi_1', 'spi_3', 'spi_6', 'spi_12',
                'spei_3', 'spei_6', 'spei_12'
            ]
            
            df = pd.DataFrame(rows, columns=columns)
            
            # Save to CSV
            df.to_csv('data/training/kenya_features.csv', index=False)
            print(f"✅ Created training dataset: {len(df)} samples")
            print(f"   Saved to: data/training/kenya_features.csv")
            
            return df

# Run
asyncio.run(create_training_data())
```

#### **Add Ground Truth Labels**

You'll need actual well data or aquifer presence data. Options:

**Option 1: Use Existing Well Data**
```python
# Add well data from CSV
import pandas as pd

# Load your well data
wells = pd.read_csv('data/ground_truth/kenya_wells.csv')
# Expected columns: latitude, longitude, aquifer_present (0/1), depth_m

# Merge with features
features = pd.read_csv('data/training/kenya_features.csv')
training_data = features.merge(
    wells,
    on=['latitude', 'longitude'],
    how='inner'
)

training_data.to_csv('data/training/kenya_training_data.csv', index=False)
print(f"✅ Training data with labels: {len(training_data)} samples")
```

**Option 2: Use Proxy Labels (Hydrogeological Maps)**
```python
# Use geological/hydrogeological maps as proxy
# Areas with sedimentary rocks → likely aquifers
# Areas with crystalline rocks → unlikely aquifers
```

**Option 3: Use GRACE Data (NASA)**
```python
# Use GRACE groundwater storage anomalies as proxy
# Positive anomalies → aquifer recharge
# Negative anomalies → aquifer depletion
```

---

### **Step 7: Train Models on Real Data**

```bash
cd modules/modeling

# Train aquifer classifier on real data
python main.py \
  --train \
  --data-file ../../data/training/kenya_training_data.csv \
  --model-type xgboost \
  --target aquifer_present \
  --cv-folds 5 \
  --save-to-storage

# Train recharge forecaster on real data
python main.py \
  --train \
  --data-file ../../data/training/kenya_time_series.csv \
  --model-type lstm \
  --task forecast \
  --horizon 12 \
  --save-to-storage
```

---

### **Step 8: Validate with Real Data**

#### **Spatial Cross-Validation**

```python
# validate_model.py
from modeling.spatial_cv import SpatialCrossValidator
import pandas as pd

# Load data
data = pd.read_csv('data/training/kenya_training_data.csv')

X = data[['elevation', 'slope', 'twi', 'tpi', 'spi_3', 'spei_6']]
y = data['aquifer_present']
coords = data[['latitude', 'longitude']].values

# Spatial CV
cv = SpatialCrossValidator(n_splits=5, buffer_radius_km=50)

from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)

scores = cv.cross_validate(model, X, y, coords)

print(f"✅ Spatial CV Results:")
print(f"   Mean ROC-AUC: {scores['roc_auc'].mean():.3f} ± {scores['roc_auc'].std():.3f}")
print(f"   Mean Accuracy: {scores['accuracy'].mean():.3f} ± {scores['accuracy'].std():.3f}")
```

---

### **Step 9: Deploy with Real Data**

#### **Update API to Use Real Models**

```bash
# Copy trained models to prediction service
cp data/models/aquifer_classifier_v2.1.0.joblib \
   modules/prediction-service/models/

cp data/models/recharge_forecaster_v1.8.2.pt \
   modules/prediction-service/models/
```

#### **Start API with Real Data**

```bash
cd modules/prediction-service

# Update config to use real models
export MODEL_PATH=./models/aquifer_classifier_v2.1.0.joblib
export FORECASTER_PATH=./models/recharge_forecaster_v1.8.2.pt

# Start API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **Test Real Predictions**

```bash
# Test with real Kenya location
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": -1.2921, "lon": 36.8219},
    "use_cached_features": true
  }'

# Should return real prediction based on actual data!
```

---

## 📊 **Real Data Sources**

### **Primary Sources (Included)**

1. **CHIRPS (Precipitation)**
   - Dataset: `UCSB-CHG/CHIRPS/DAILY`
   - Resolution: 5.5 km
   - Coverage: 1981-present
   - Update: Daily

2. **ERA5 (Temperature)**
   - Dataset: `ECMWF/ERA5/DAILY`
   - Resolution: 27 km
   - Coverage: 1979-present
   - Update: Daily

3. **SRTM (Elevation)**
   - Dataset: `USGS/SRTMGL1_003`
   - Resolution: 30 m
   - Coverage: Global
   - Static

4. **ESA WorldCover (Land Cover)**
   - Dataset: `ESA/WorldCover/v100`
   - Resolution: 10 m
   - Coverage: Global
   - Year: 2020

### **Additional Sources (Optional)**

5. **GRACE (Groundwater Storage)**
   - Dataset: `NASA/GRACE/MASS_GRIDS/MASCON`
   - Use for: Groundwater trends
   
6. **MODIS (Vegetation)**
   - Dataset: `MODIS/006/MOD13A2`
   - Use for: NDVI, land health

7. **Soil Grids (Soil Properties)**
   - Dataset: `OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M`
   - Use for: Soil characteristics

---

## 🎯 **Data Quality Checklist**

### **Before Training**
- [ ] Data downloaded successfully from GEE
- [ ] No missing values in critical features
- [ ] Data covers entire Kenya region
- [ ] Temporal coverage is adequate (3+ years)
- [ ] Spatial resolution is consistent
- [ ] Features are properly normalized
- [ ] Ground truth labels are available
- [ ] Train/test split is spatially separated

### **After Training**
- [ ] Model performance is acceptable (ROC-AUC > 0.75)
- [ ] Spatial cross-validation shows no overfitting
- [ ] Predictions make geographical sense
- [ ] Feature importance aligns with domain knowledge
- [ ] Model generalizes to unseen regions

---

## 🔍 **Validation Strategies**

### **1. Spatial Validation**
```python
# Use spatial cross-validation
# Ensure test locations are >50km from training locations
```

### **2. Temporal Validation**
```python
# Train on 2020-2022, test on 2023
# Ensures model works on future data
```

### **3. Expert Validation**
```python
# Show predictions to hydrogeologists
# Validate against known aquifer locations
```

### **4. Field Validation**
```python
# Drill wells at high-confidence predictions
# Measure actual aquifer presence/depth
```

---

## 📈 **Expected Results with Real Data**

### **Model Performance**
- **Aquifer Classifier**:
  - ROC-AUC: 0.80-0.90
  - Precision: 0.75-0.85
  - Recall: 0.70-0.85

- **Recharge Forecaster**:
  - RMSE: 10-20 mm
  - MAE: 8-15 mm
  - R²: 0.70-0.85

### **Spatial Coverage**
- **Kenya**: ~580,000 km²
- **Grid Points**: ~580,000 (1km resolution)
- **Predictions**: All grid points
- **Processing Time**: 2-4 hours (full country)

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: GEE Quota Exceeded**
```bash
# Solution: Use batch processing
# Process data in smaller chunks (monthly instead of yearly)
```

### **Issue 2: Missing Data**
```bash
# Solution: Use interpolation
# Fill gaps with spatial/temporal interpolation
```

### **Issue 3: Large File Sizes**
```bash
# Solution: Use compression
# Export as Cloud Optimized GeoTIFF (COG)
```

### **Issue 4: Slow Processing**
```bash
# Solution: Use OCI Data Science
# Process in parallel on larger compute instances
```

---

## 📝 **Next Steps**

1. **✅ Setup GEE credentials**
2. **✅ Fetch real data for Kenya**
3. **✅ Upload to OCI Object Storage**
4. **✅ Preprocess and generate features**
5. **✅ Obtain ground truth labels**
6. **✅ Train models on real data**
7. **✅ Validate spatially and temporally**
8. **✅ Deploy to production**
9. **✅ Monitor performance**
10. **✅ Iterate and improve**

---

## 🎓 **Resources**

- **GEE Datasets**: https://developers.google.com/earth-engine/datasets
- **CHIRPS**: https://www.chc.ucsb.edu/data/chirps
- **ERA5**: https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5
- **SRTM**: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-srtm
- **Kenya Water Data**: http://www.wra.go.ke/

---

**You're now ready to work with real data! 🌍🚀**

Run the commands in sequence and you'll have a fully functional system using actual satellite and geospatial data for Kenya.
