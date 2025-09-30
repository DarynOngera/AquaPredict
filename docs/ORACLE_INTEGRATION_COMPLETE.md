# 🎯 AquaPredict - Complete Oracle Integration Guide

## **Let's Make This Dream Work with Oracle! 🚀**

This guide will walk you through integrating the full Oracle stack to unlock the **real functional power** of AquaPredict.

---

## 📋 **Prerequisites Checklist**

Before we begin, ensure you have:

- [ ] Oracle Cloud account with credits
- [ ] OCI CLI installed (`brew install oci-cli` or download from Oracle)
- [ ] Python 3.10+ installed
- [ ] Docker installed
- [ ] kubectl installed
- [ ] Terraform installed (optional, for IaC)

---

## 🏗️ **Phase 1: Oracle Autonomous Database (ADB) Setup**

### **Step 1: Create ADB Instance via OCI Console**

1. **Login to OCI Console**: https://cloud.oracle.com
2. **Navigate**: Menu → Oracle Database → Autonomous Database
3. **Click**: "Create Autonomous Database"
4. **Configure**:
   - **Display Name**: `AquaPredict-DB`
   - **Database Name**: `aquapredict`
   - **Workload Type**: Data Warehouse
   - **Deployment Type**: Shared Infrastructure
   - **Database Version**: 19c
   - **OCPU Count**: 2 (auto-scaling enabled)
   - **Storage**: 1 TB (auto-scaling enabled)
   - **Admin Password**: Create a strong password
   - **Network Access**: Secure access from everywhere (for now)
   - **License**: Bring Your Own License (BYOL)

5. **Click**: "Create Autonomous Database"
6. **Wait**: ~5 minutes for provisioning

### **Step 2: Download Wallet**

1. On the ADB details page, click **"DB Connection"**
2. Click **"Download Wallet"**
3. **Wallet Password**: Create a password
4. Save `wallet.zip` to your project

```bash
# Extract wallet
cd /home/ongera/projects/AquaPredict
mkdir -p credentials/wallet
unzip wallet.zip -d credentials/wallet/
```

### **Step 3: Install Oracle Client**

```bash
# For Linux
wget https://download.oracle.com/otn_software/linux/instantclient/instantclient-basic-linux.x64-21.12.0.0.0dbru.zip
unzip instantclient-basic-linux.x64-21.12.0.0.0dbru.zip
sudo mv instantclient_21_12 /opt/oracle/
echo 'export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_12:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# For macOS
brew tap InstantClientTap/instantclient
brew install instantclient-basic
```

### **Step 4: Install Python Oracle Driver**

```bash
pip install oracledb
```

### **Step 5: Create Database Schema**

```bash
# Connect to ADB
sqlplus admin/<your-password>@aquapredict_high

# Run schema creation
@sql/schema.sql
```

Or use the Python script:

```python
import oracledb
import os

# Initialize Oracle client
oracledb.init_oracle_client(config_dir="./credentials/wallet")

# Connect
connection = oracledb.connect(
    user="admin",
    password="<your-password>",
    dsn="aquapredict_high",
    wallet_location="./credentials/wallet",
    wallet_password="<wallet-password>"
)

# Execute schema
with open('sql/schema.sql', 'r') as f:
    schema_sql = f.read()
    
cursor = connection.cursor()
for statement in schema_sql.split(';'):
    if statement.strip():
        cursor.execute(statement)

connection.commit()
print("✅ Schema created successfully!")
```

### **Step 6: Configure Environment Variables**

Create `.env` file:

```bash
# Oracle ADB
WALLET_LOCATION=./credentials/wallet
WALLET_PASSWORD=your_wallet_password
DB_USERNAME=admin
DB_PASSWORD=your_admin_password
DB_DSN=aquapredict_high

# OCI
OCI_CONFIG_FILE=~/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
```

---

## 📦 **Phase 2: OCI Object Storage Setup**

### **Step 1: Create Buckets**

```bash
# Set your compartment OCID
export COMPARTMENT_ID="ocid1.compartment.oc1..xxx"

# Create buckets
oci os bucket create --name aquapredict-data-raw --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-data-processed --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-models --compartment-id $COMPARTMENT_ID
oci os bucket create --name aquapredict-reports --compartment-id $COMPARTMENT_ID

echo "✅ Buckets created!"
```

### **Step 2: Install OCI Python SDK**

```bash
pip install oci
```

### **Step 3: Configure OCI CLI**

```bash
oci setup config

# Follow prompts:
# - Enter your user OCID
# - Enter your tenancy OCID
# - Enter your region (e.g., us-ashburn-1)
# - Generate API key pair (Y)
# - Upload public key to OCI Console (User Settings → API Keys)
```

### **Step 4: Test Object Storage**

```python
from modules.common.oci_storage import OCIStorageClient

# Initialize client
storage = OCIStorageClient()

# Test upload
storage.upload_file(
    bucket_name='aquapredict-data-raw',
    object_name='test/hello.txt',
    file_path='/tmp/test.txt'
)

# Test list
objects = storage.list_objects('aquapredict-data-raw', prefix='test/')
print(f"✅ Found {len(objects)} objects")
```

---

## 🤖 **Phase 3: OCI Data Science & Model Deployment**

### **Step 1: Create Data Science Project**

1. **OCI Console**: Menu → Analytics & AI → Data Science
2. **Click**: "Create Project"
3. **Name**: `AquaPredict ML`
4. **Create**

### **Step 2: Create Notebook Session**

1. **In Project**: Click "Create Notebook Session"
2. **Configure**:
   - **Name**: `aquapredict-training`
   - **Compute Shape**: VM.Standard2.4 (4 OCPUs, 60GB RAM)
   - **Block Storage**: 100 GB
   - **VCN**: Select your VCN
3. **Create** (takes ~5 minutes)

### **Step 3: Upload Training Code**

In the notebook session:

```python
# Install ADS (Accelerated Data Science SDK)
!pip install oracle-ads

# Import
import ads
ads.set_auth(auth='resource_principal')

# Upload your training data to Object Storage
# Then train models in the notebook

# Example: Train aquifer classifier
from modeling import AquiferClassifier
import joblib

# Load data from Object Storage
# ... (your data loading code)

# Train
classifier = AquiferClassifier(model_type='xgboost')
classifier.train(X_train, y_train)

# Save to Object Storage
joblib.dump(classifier, '/tmp/aquifer_classifier.joblib')

# Upload to OCI Object Storage
from oci_storage import DataStorageManager
storage = DataStorageManager()
storage.save_model(
    model_name='aquifer_classifier',
    version='v2.1.0',
    file_path='/tmp/aquifer_classifier.joblib'
)
```

### **Step 4: Deploy Model (Optional - Advanced)**

```python
# In notebook
from ads.model.framework.sklearn_model import SklearnModel

# Prepare model artifact
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

# Deploy
deployment = sklearn_model.deploy(
    display_name="aquapredict-classifier-prod",
    deployment_instance_shape="VM.Standard2.1",
    deployment_instance_count=2
)

print(f"✅ Model deployed! Endpoint: {deployment.url}")
```

---

## 🐳 **Phase 4: OCI Container Registry (OCIR)**

### **Step 1: Login to OCIR**

```bash
# Get your auth token from OCI Console (User Settings → Auth Tokens)
export OCIR_REGION="us-ashburn-1"
export OCIR_TENANCY="your-tenancy-name"
export OCIR_USERNAME="your-tenancy-name/oracleidentitycloudservice/your-email"
export OCIR_TOKEN="your-auth-token"

# Login
docker login ${OCIR_REGION}.ocir.io -u ${OCIR_USERNAME} -p ${OCIR_TOKEN}
```

### **Step 2: Build and Push Images**

```bash
cd /home/ongera/projects/AquaPredict

# Build prediction service
docker build -t ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:latest \
  -f modules/prediction-service/Dockerfile \
  modules/prediction-service/

# Push
docker push ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/prediction-service:latest

# Build frontend
docker build -t ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/frontend:latest \
  -f modules/frontend/Dockerfile \
  modules/frontend/

# Push
docker push ${OCIR_REGION}.ocir.io/${OCIR_TENANCY}/aquapredict/frontend:latest

echo "✅ Images pushed to OCIR!"
```

---

## ☸️ **Phase 5: Oracle Kubernetes Engine (OKE)**

### **Step 1: Create OKE Cluster**

1. **OCI Console**: Menu → Developer Services → Kubernetes Clusters (OKE)
2. **Click**: "Create Cluster"
3. **Choose**: "Quick Create"
4. **Configure**:
   - **Name**: `aquapredict-cluster`
   - **Kubernetes Version**: v1.28.2
   - **Node Pool**: 3 nodes
   - **Shape**: VM.Standard.E4.Flex (2 OCPUs, 16GB RAM each)
   - **Network**: Create new VCN
5. **Create** (takes ~10 minutes)

### **Step 2: Configure kubectl**

```bash
# Get cluster OCID from OCI Console
export CLUSTER_ID="ocid1.cluster.oc1..xxx"

# Generate kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_ID \
  --file ~/.kube/config \
  --region us-ashburn-1 \
  --token-version 2.0.0

# Test
kubectl get nodes
# Should show 3 nodes
```

### **Step 3: Deploy to OKE**

```bash
cd infrastructure/k8s

# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=<your-password> \
  --from-literal=dsn=aquapredict_high \
  --from-file=wallet=../../credentials/wallet \
  -n aquapredict

kubectl create secret docker-registry ocir-secret \
  --docker-server=${OCIR_REGION}.ocir.io \
  --docker-username=${OCIR_USERNAME} \
  --docker-password=${OCIR_TOKEN} \
  -n aquapredict

# Deploy applications
kubectl apply -f deployments/ -n aquapredict
kubectl apply -f services/ -n aquapredict
kubectl apply -f ingress.yaml -n aquapredict

# Check status
kubectl get pods -n aquapredict
kubectl get svc -n aquapredict
```

---

## 📊 **Phase 6: Testing the Complete Integration**

### **Step 1: Test Database Connection**

```python
from modules.prediction-service.oracle_database import OracleADBClient
import asyncio

async def test_db():
    db = OracleADBClient()
    
    # Insert location
    location_id = await db.insert_location(
        lat=-1.2921,
        lon=36.8219,
        region='Nairobi'
    )
    print(f"✅ Created location: {location_id}")
    
    # Insert features
    features = {
        'elevation': 1795,
        'slope': 5.2,
        'twi': 8.5,
        'precip_mean': 800,
        'temp_mean': 22.5
    }
    feature_id = await db.insert_features(location_id, features)
    print(f"✅ Created features: {feature_id}")
    
    # Insert prediction
    pred_id = await db.insert_prediction(
        location_id=location_id,
        prediction='present',
        probability=0.89,
        confidence_lower=0.79,
        confidence_upper=0.95,
        model_type='xgboost',
        model_version='v2.1.0'
    )
    print(f"✅ Created prediction: {pred_id}")

asyncio.run(test_db())
```

### **Step 2: Test Object Storage**

```python
from modules.common.oci_storage import DataStorageManager

storage = DataStorageManager()

# Save test model
storage.save_model(
    model_name='test_model',
    version='v1.0.0',
    file_path='/tmp/test_model.joblib'
)
print("✅ Model saved to Object Storage")

# List models
objects = storage.storage.list_objects('aquapredict-models')
print(f"✅ Found {len(objects)} models")
```

### **Step 3: Test End-to-End**

```bash
# Start prediction service locally
cd modules/prediction-service
uvicorn main:app --reload

# In another terminal, test API
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": -1.2921, "lon": 36.8219},
    "use_cached_features": false,
    "features": {
      "elevation": 1795,
      "slope": 5.2,
      "twi": 8.5,
      "precip_mean": 800,
      "temp_mean": 22.5
    }
  }'

# Should return prediction with data saved to Oracle ADB!
```

---

## 🎯 **Phase 7: Complete Workflow**

### **The Full Pipeline**:

1. **Data Ingestion** → Saves to **OCI Object Storage** (raw bucket)
2. **Preprocessing** → Saves to **OCI Object Storage** (processed bucket)
3. **Feature Engineering** → Saves features to **Oracle ADB**
4. **Model Training** → In **OCI Data Science**, saves models to **OCI Object Storage**
5. **Prediction API** → Loads models from **Object Storage**, saves predictions to **Oracle ADB**
6. **Frontend** → Queries **Oracle ADB** via API, displays results
7. **Reports** → Generated and saved to **OCI Object Storage**

### **Run Complete Workflow**:

```bash
# 1. Ingest data
cd modules/data-ingestion
python main.py --dataset all --start-date 2023-01-01 --end-date 2023-12-31
# Data saved to OCI Object Storage ✅

# 2. Preprocess
cd ../preprocessing
python main.py --input-bucket aquapredict-data-raw --output-bucket aquapredict-data-processed
# Processed data saved to OCI Object Storage ✅

# 3. Generate features
cd ../feature-engineering
python main.py --save-to-adb
# Features saved to Oracle ADB ✅

# 4. Train models
cd ../modeling
python main.py --train --save-to-storage
# Models saved to OCI Object Storage ✅

# 5. Start API
cd ../prediction-service
uvicorn main:app --host 0.0.0.0 --port 8000
# API running, connected to Oracle ADB ✅

# 6. Start Frontend
cd ../frontend
npm run dev
# Frontend running, connected to API ✅

# 7. Test!
# Open http://localhost:3000
# Click on map → Predict → Data flows through Oracle stack! 🎉
```

---

## 📈 **Monitoring with OCI**

### **Enable Logging**:

```bash
# Create log group
oci logging log-group create \
  --compartment-id $COMPARTMENT_ID \
  --display-name "AquaPredict Logs"

# Enable OKE logging
# (Configure in OCI Console → OKE → Logging)
```

### **Enable Monitoring**:

```bash
# Metrics are automatically collected
# View in OCI Console → Monitoring → Metrics Explorer
```

---

## 🎉 **Success Checklist**

- [ ] Oracle ADB created and schema loaded
- [ ] OCI Object Storage buckets created
- [ ] OCI Data Science project created
- [ ] OCIR configured and images pushed
- [ ] OKE cluster created and apps deployed
- [ ] Database connection tested
- [ ] Object Storage tested
- [ ] End-to-end prediction tested
- [ ] Frontend connected and working

---

## 🚀 **You're Ready!**

Your AquaPredict platform is now fully integrated with Oracle's stack:

✅ **Oracle Autonomous Database** - Storing all spatial data  
✅ **OCI Object Storage** - Storing data, models, reports  
✅ **OCI Data Science** - Training ML models  
✅ **OCIR** - Hosting Docker images  
✅ **OKE** - Running containerized services  
✅ **OCI Monitoring** - Tracking performance  
✅ **OCI Logging** - Centralized logs  

**This is the real functional power! Let's make this dream work! 🌊🚀**
