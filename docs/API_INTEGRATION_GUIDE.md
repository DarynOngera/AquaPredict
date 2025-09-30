# AquaPredict - Complete API Integration Guide

## 🎯 Mission: Real Functional Power with Oracle Stack

This guide will help you integrate all components to create a **production-ready, Oracle-powered** geospatial AI platform.

---

## 🏗️ **Oracle Cloud Infrastructure (OCI) - Our Foundation**

### **Required Oracle Services**

1. **Oracle Autonomous Database (ADB)** - Spatial data storage ⭐
2. **OCI Object Storage** - Raw data, models, reports
3. **OCI Data Science** - Model training notebooks
4. **OCI Model Deployment** - Scalable ML inference
5. **OCI Container Registry (OCIR)** - Docker images
6. **Oracle Kubernetes Engine (OKE)** - Container orchestration
7. **OCI Logging** - Centralized logging
8. **OCI Monitoring** - Metrics and alerts
9. **OCI Vault** - Secrets management
10. **OCI API Gateway** - API management (optional)

---

## 📊 **Phase 1: Oracle Autonomous Database Setup**

### **Why ADB?**
- Built-in **Oracle Spatial** for geospatial queries
- Auto-scaling compute and storage
- Automatic backups and patching
- High availability
- **Perfect for our geospatial data!**

### **Step 1: Create ADB Instance**

```bash
# Using OCI CLI
oci db autonomous-database create \
  --compartment-id $COMPARTMENT_ID \
  --db-name aquapredict \
  --display-name "AquaPredict Spatial DB" \
  --admin-password "YourSecurePassword123!" \
  --cpu-core-count 2 \
  --data-storage-size-in-tbs 1 \
  --db-workload DW \
  --is-auto-scaling-enabled true
```

### **Step 2: Download Wallet**

```bash
# Download connection wallet
oci db autonomous-database generate-wallet \
  --autonomous-database-id $ADB_OCID \
  --file wallet.zip \
  --password "WalletPassword123!"

# Extract wallet
unzip wallet.zip -d wallet/
```

### **Step 3: Create Database Schema**

Create `sql/schema.sql`:

```sql
-- ============================================
-- AquaPredict Database Schema
-- Oracle Autonomous Database with Spatial
-- ============================================

-- Enable Spatial
ALTER SESSION SET CURRENT_SCHEMA = ADMIN;

-- ============================================
-- 1. LOCATIONS TABLE (Spatial)
-- ============================================
CREATE TABLE locations (
    location_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    latitude NUMBER(10, 6) NOT NULL,
    longitude NUMBER(10, 6) NOT NULL,
    region VARCHAR2(100),
    country VARCHAR2(100) DEFAULT 'Kenya',
    geom SDO_GEOMETRY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_lat CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_lon CHECK (longitude BETWEEN -180 AND 180)
);

-- Spatial index
INSERT INTO user_sdo_geom_metadata VALUES (
    'LOCATIONS',
    'GEOM',
    SDO_DIM_ARRAY(
        SDO_DIM_ELEMENT('X', -180, 180, 0.005),
        SDO_DIM_ELEMENT('Y', -90, 90, 0.005)
    ),
    4326  -- WGS84
);

CREATE INDEX locations_spatial_idx ON locations(geom)
    INDEXTYPE IS MDSYS.SPATIAL_INDEX;

-- ============================================
-- 2. FEATURES TABLE
-- ============================================
CREATE TABLE features (
    feature_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id NUMBER NOT NULL,
    
    -- Static features
    elevation NUMBER,
    slope NUMBER,
    aspect NUMBER,
    twi NUMBER,  -- Topographic Wetness Index
    tpi NUMBER,  -- Topographic Position Index
    
    -- Soil features
    soil_type VARCHAR2(50),
    soil_moisture NUMBER,
    
    -- Temporal features (monthly aggregates)
    precip_mean NUMBER,
    precip_std NUMBER,
    temp_mean NUMBER,
    temp_std NUMBER,
    
    -- Drought indices
    spi_1 NUMBER,   -- 1-month SPI
    spi_3 NUMBER,   -- 3-month SPI
    spi_6 NUMBER,   -- 6-month SPI
    spi_12 NUMBER,  -- 12-month SPI
    spei_3 NUMBER,  -- 3-month SPEI
    spei_6 NUMBER,  -- 6-month SPEI
    spei_12 NUMBER, -- 12-month SPEI
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_quality_score NUMBER(3, 2),
    
    CONSTRAINT fk_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX idx_features_location ON features(location_id);

-- ============================================
-- 3. PREDICTIONS TABLE
-- ============================================
CREATE TABLE predictions (
    prediction_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id NUMBER NOT NULL,
    
    -- Prediction results
    model_version VARCHAR2(20),
    prediction VARCHAR2(20),  -- 'present', 'absent'
    probability NUMBER(5, 4),
    confidence_lower NUMBER(5, 4),
    confidence_upper NUMBER(5, 4),
    
    -- Model details
    model_type VARCHAR2(50),  -- 'xgboost', 'random_forest', 'ensemble'
    feature_importance CLOB,  -- JSON
    
    -- Metadata
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prediction_time_ms NUMBER,
    
    CONSTRAINT fk_pred_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX idx_predictions_location ON predictions(location_id);
CREATE INDEX idx_predictions_date ON predictions(predicted_at);

-- ============================================
-- 4. FORECASTS TABLE
-- ============================================
CREATE TABLE forecasts (
    forecast_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id NUMBER NOT NULL,
    
    -- Forecast results
    model_version VARCHAR2(20),
    horizon_months NUMBER,
    forecast_values CLOB,  -- JSON array
    confidence_intervals CLOB,  -- JSON array
    
    -- Statistics
    avg_recharge NUMBER,
    max_recharge NUMBER,
    min_recharge NUMBER,
    
    -- Model details
    model_type VARCHAR2(50),  -- 'lstm', 'tft'
    rmse NUMBER,
    mae NUMBER,
    r2_score NUMBER,
    
    -- Metadata
    forecasted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    forecast_time_ms NUMBER,
    
    CONSTRAINT fk_forecast_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX idx_forecasts_location ON forecasts(location_id);
CREATE INDEX idx_forecasts_date ON forecasts(forecasted_at);

-- ============================================
-- 5. TIME_SERIES_DATA TABLE
-- ============================================
CREATE TABLE time_series_data (
    ts_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id NUMBER NOT NULL,
    
    -- Time
    date_value DATE NOT NULL,
    year NUMBER,
    month NUMBER,
    
    -- Measurements
    precipitation NUMBER,
    temperature NUMBER,
    evapotranspiration NUMBER,
    recharge NUMBER,
    
    -- Source
    data_source VARCHAR2(50),  -- 'CHIRPS', 'ERA5', 'computed'
    
    CONSTRAINT fk_ts_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX idx_ts_location_date ON time_series_data(location_id, date_value);

-- ============================================
-- 6. MODELS TABLE
-- ============================================
CREATE TABLE models (
    model_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Model info
    model_name VARCHAR2(100) NOT NULL,
    model_type VARCHAR2(50),  -- 'classifier', 'forecaster'
    version VARCHAR2(20),
    
    -- Storage
    storage_path VARCHAR2(500),  -- OCI Object Storage path
    
    -- Performance metrics
    metrics CLOB,  -- JSON
    
    -- Status
    status VARCHAR2(20),  -- 'active', 'deprecated', 'testing'
    is_default NUMBER(1) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR2(100)
);

CREATE INDEX idx_models_status ON models(status);

-- ============================================
-- 7. REPORTS TABLE
-- ============================================
CREATE TABLE reports (
    report_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Report info
    title VARCHAR2(200) NOT NULL,
    report_type VARCHAR2(50),  -- 'ISO14046', 'technical', 'forecast'
    region VARCHAR2(100),
    
    -- Content
    storage_path VARCHAR2(500),  -- OCI Object Storage path
    file_size_mb NUMBER,
    
    -- Statistics
    total_predictions NUMBER,
    aquifers_found NUMBER,
    
    -- Status
    status VARCHAR2(20),  -- 'completed', 'processing', 'failed'
    
    -- Metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR2(100)
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_date ON reports(generated_at);

-- ============================================
-- 8. AUDIT_LOG TABLE
-- ============================================
CREATE TABLE audit_log (
    log_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Event
    event_type VARCHAR2(50),  -- 'prediction', 'forecast', 'report', 'model_update'
    event_action VARCHAR2(50),
    
    -- Details
    user_id VARCHAR2(100),
    ip_address VARCHAR2(50),
    details CLOB,  -- JSON
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_type ON audit_log(event_type);
CREATE INDEX idx_audit_date ON audit_log(created_at);

-- ============================================
-- VIEWS
-- ============================================

-- Recent predictions with location
CREATE OR REPLACE VIEW v_recent_predictions AS
SELECT 
    p.prediction_id,
    l.latitude,
    l.longitude,
    l.region,
    p.prediction,
    p.probability,
    p.model_type,
    p.predicted_at
FROM predictions p
JOIN locations l ON p.location_id = l.location_id
ORDER BY p.predicted_at DESC;

-- Model performance summary
CREATE OR REPLACE VIEW v_model_performance AS
SELECT 
    model_name,
    version,
    model_type,
    status,
    JSON_VALUE(metrics, '$.roc_auc') as roc_auc,
    JSON_VALUE(metrics, '$.rmse') as rmse,
    created_at
FROM models
WHERE status = 'active';

-- ============================================
-- SPATIAL FUNCTIONS
-- ============================================

-- Function to find nearest locations
CREATE OR REPLACE FUNCTION find_nearest_locations(
    p_lat NUMBER,
    p_lon NUMBER,
    p_limit NUMBER DEFAULT 10
)
RETURN SYS_REFCURSOR
IS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT 
            location_id,
            latitude,
            longitude,
            region,
            SDO_GEOM.SDO_DISTANCE(
                geom,
                SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(p_lon, p_lat, NULL), NULL, NULL),
                0.005
            ) as distance_km
        FROM locations
        ORDER BY distance_km
        FETCH FIRST p_limit ROWS ONLY;
    
    RETURN v_cursor;
END;
/

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert sample Kenya regions
INSERT INTO locations (latitude, longitude, region, geom) VALUES
    (-1.2921, 36.8219, 'Nairobi', SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(36.8219, -1.2921, NULL), NULL, NULL)),
    (-0.0917, 34.7680, 'Kisumu', SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(34.7680, -0.0917, NULL), NULL, NULL)),
    (0.5143, 35.2698, 'Eldoret', SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(35.2698, 0.5143, NULL), NULL, NULL)),
    (-4.0435, 39.6682, 'Mombasa', SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(39.6682, -4.0435, NULL), NULL, NULL)),
    (-0.2827, 36.0800, 'Nakuru', SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(36.0800, -0.2827, NULL), NULL, NULL));

COMMIT;

-- Grant permissions (if needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON locations TO aquapredict_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON features TO aquapredict_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON predictions TO aquapredict_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON forecasts TO aquapredict_user;

SELECT 'Schema created successfully!' FROM DUAL;
```

### **Step 4: Connect from Python**

Update `modules/prediction-service/database.py`:

```python
import oracledb
import os
from contextlib import asynccontextmanager

class OracleADBConnection:
    def __init__(self):
        self.wallet_location = os.getenv("WALLET_LOCATION", "./wallet")
        self.wallet_password = os.getenv("WALLET_PASSWORD")
        self.username = os.getenv("DB_USERNAME", "admin")
        self.password = os.getenv("DB_PASSWORD")
        self.dsn = os.getenv("DB_DSN", "aquapredict_high")
        
    async def get_connection(self):
        """Get Oracle ADB connection with wallet."""
        oracledb.init_oracle_client(
            config_dir=self.wallet_location
        )
        
        connection = await oracledb.connect_async(
            user=self.username,
            password=self.password,
            dsn=self.dsn,
            wallet_location=self.wallet_location,
            wallet_password=self.wallet_password
        )
        
        return connection
```

---

## 🗄️ **Phase 2: OCI Object Storage Integration**

### **Why Object Storage?**
- Store raw GEE data (GeoTIFFs, NetCDFs)
- Store trained ML models
- Store generated reports (PDFs)
- Cheap, scalable, durable

### **Step 1: Create Buckets**

```bash
# Create buckets
oci os bucket create --name aquapredict-data-raw --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-data-processed --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-models --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-reports --compartment-id $COMPARTMENT_ID
```

### **Step 2: Python Integration**

Create `modules/common/oci_storage.py`:

```python
import oci
import os
from typing import BinaryIO

class OCIStorageClient:
    def __init__(self):
        config = oci.config.from_file()
        self.object_storage = oci.object_storage.ObjectStorageClient(config)
        self.namespace = self.object_storage.get_namespace().data
        
    def upload_file(self, bucket_name: str, object_name: str, file_path: str):
        """Upload file to OCI Object Storage."""
        with open(file_path, 'rb') as file:
            self.object_storage.put_object(
                namespace_name=self.namespace,
                bucket_name=bucket_name,
                object_name=object_name,
                put_object_body=file
            )
    
    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """Download file from OCI Object Storage."""
        response = self.object_storage.get_object(
            namespace_name=self.namespace,
            bucket_name=bucket_name,
            object_name=object_name
        )
        
        with open(file_path, 'wb') as file:
            for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
                file.write(chunk)
    
    def list_objects(self, bucket_name: str, prefix: str = None):
        """List objects in bucket."""
        return self.object_storage.list_objects(
            namespace_name=self.namespace,
            bucket_name=bucket_name,
            prefix=prefix
        ).data.objects
```

---

## 🤖 **Phase 3: OCI Data Science & Model Deployment**

### **Step 1: Train Models in OCI Data Science**

Create notebook session and run:

```python
# In OCI Data Science Notebook
import ads
from ads.model.framework.sklearn_model import SklearnModel

# Authenticate
ads.set_auth(auth='resource_principal')

# Train your model
from modeling import AquiferClassifier

classifier = AquiferClassifier(model_type='xgboost')
classifier.train(X_train, y_train)

# Save to Model Catalog
sklearn_model = SklearnModel(
    estimator=classifier.model,
    artifact_dir="./model_artifact"
)

sklearn_model.prepare(
    inference_conda_env="oci://bucket@namespace/conda_env.tar.gz",
    force_overwrite=True
)

# Save to Model Catalog
model_id = sklearn_model.save(
    display_name="AquaPredict Aquifer Classifier v2.1",
    description="XGBoost classifier for aquifer prediction"
)
```

### **Step 2: Deploy Model**

```python
# Deploy to Model Deployment
sklearn_model.deploy(
    display_name="aquapredict-classifier-prod",
    deployment_instance_shape="VM.Standard2.1",
    deployment_instance_count=2,
    deployment_bandwidth_mbps=10
)
```

### **Step 3: Call Deployed Model**

```python
# In prediction service
import ads
from ads.model.deployment import ModelDeployment

ads.set_auth(auth='api_key', config='~/.oci/config')

deployment = ModelDeployment.from_id("<deployment_ocid>")

# Make prediction
prediction = deployment.predict(features)
```

---

## 📡 **Phase 4: Complete API Integration**

Let me create the complete, production-ready API integration files...
