#!/bin/bash
# AquaPredict OCI Data Science Setup Script
# Configures Data Science notebooks and model deployment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get notebook session OCID from Terraform
get_notebook_ocid() {
    log_info "Getting notebook session OCID..."
    
    cd ../terraform
    NOTEBOOK_OCID=$(terraform output -raw data_science_notebook_session_id 2>/dev/null)
    
    if [ -z "$NOTEBOOK_OCID" ]; then
        log_error "Could not retrieve notebook session OCID"
        exit 1
    fi
    
    echo "$NOTEBOOK_OCID"
}

# Create conda environment specification
create_conda_env() {
    log_info "Creating conda environment specification..."
    
    mkdir -p ../data_science/environments
    
    cat > ../data_science/environments/aquapredict_env.yaml <<'EOF'
name: aquapredict_ml
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - numpy=1.24.3
  - pandas=2.0.3
  - scikit-learn=1.3.0
  - xgboost=1.7.6
  - tensorflow=2.13.0
  - keras=2.13.1
  - matplotlib=3.7.2
  - seaborn=0.12.2
  - jupyter=1.0.0
  - ipykernel=6.25.0
  - geopandas=0.13.2
  - shapely=2.0.1
  - rasterio=1.3.8
  - earthengine-api=0.1.363
  - pip:
    - oracle-ads==2.9.1
    - oci==2.112.0
    - cx_Oracle==8.3.0
    - fastapi==0.103.1
    - uvicorn==0.23.2
    - pydantic==2.3.0
    - python-dotenv==1.0.0
    - mlflow==2.7.1
    - optuna==3.3.0
    - shap==0.42.1
EOF

    log_info "Conda environment specification created!"
}

# Create model training notebook
create_training_notebook() {
    log_info "Creating model training notebook..."
    
    mkdir -p ../data_science/notebooks
    
    cat > ../data_science/notebooks/01_aquifer_model_training.py <<'EOF'
"""
AquaPredict - Aquifer Prediction Model Training
Train XGBoost model for aquifer presence prediction
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import xgboost as xgb
import joblib
from datetime import datetime
import json

# OCI imports
import oci
from ads.model.framework.sklearn_model import SklearnModel
from ads.common.model_metadata import UseCaseType

# Configuration
BUCKET_NAME = "aquapredict-models"
MODEL_NAME = "aquifer_prediction_xgboost"
VERSION = datetime.now().strftime("%Y%m%d_%H%M%S")

def load_data_from_adb():
    """Load training data from Oracle ADB"""
    import cx_Oracle
    
    # Connection details from environment
    connection_string = os.getenv("DB_CONNECTION_STRING")
    
    conn = cx_Oracle.connect(connection_string)
    
    query = """
        SELECT 
            f.elevation,
            f.slope,
            f.twi,
            f.precip_mean,
            f.temp_mean,
            f.ndvi,
            f.landcover,
            CASE WHEN p.prediction = 'present' THEN 1 ELSE 0 END as target
        FROM features f
        JOIN predictions p ON f.location_id = p.location_id
        WHERE f.data_source = 'GEE'
        AND p.model_version IS NOT NULL
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def prepare_features(df):
    """Prepare features for training"""
    feature_cols = ['elevation', 'slope', 'twi', 'precip_mean', 
                    'temp_mean', 'ndvi', 'landcover']
    
    X = df[feature_cols]
    y = df['target']
    
    return X, y

def train_model(X_train, y_train):
    """Train XGBoost model"""
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    metrics = {
        'accuracy': float(model.score(X_test, y_test)),
        'roc_auc': float(roc_auc_score(y_test, y_pred_proba)),
        'classification_report': classification_report(y_test, y_pred, output_dict=True),
        'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
    }
    
    return metrics

def save_model_to_oci(model, metrics):
    """Save model to OCI Object Storage and Model Catalog"""
    # Save locally first
    model_path = f"/tmp/{MODEL_NAME}_{VERSION}.pkl"
    joblib.dump(model, model_path)
    
    # Upload to Object Storage
    config = oci.config.from_file()
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data
    
    with open(model_path, 'rb') as f:
        object_storage.put_object(
            namespace,
            BUCKET_NAME,
            f"models/{MODEL_NAME}/{VERSION}/model.pkl",
            f
        )
    
    # Save metadata
    metadata = {
        'model_name': MODEL_NAME,
        'version': VERSION,
        'metrics': metrics,
        'timestamp': datetime.now().isoformat()
    }
    
    object_storage.put_object(
        namespace,
        BUCKET_NAME,
        f"models/{MODEL_NAME}/{VERSION}/metadata.json",
        json.dumps(metadata)
    )
    
    print(f"Model saved to OCI: {BUCKET_NAME}/models/{MODEL_NAME}/{VERSION}/")
    
    return model_path

def main():
    print("Starting AquaPredict Model Training...")
    
    # Load data
    print("Loading data from ADB...")
    df = load_data_from_adb()
    print(f"Loaded {len(df)} samples")
    
    # Prepare features
    X, y = prepare_features(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    print("Training model...")
    model = train_model(X_train, y_train)
    
    # Evaluate
    print("Evaluating model...")
    metrics = evaluate_model(model, X_test, y_test)
    
    print(f"Model Accuracy: {metrics['accuracy']:.4f}")
    print(f"ROC AUC: {metrics['roc_auc']:.4f}")
    
    # Save to OCI
    print("Saving model to OCI...")
    model_path = save_model_to_oci(model, metrics)
    
    print("Training completed successfully!")
    
    return model, metrics

if __name__ == "__main__":
    model, metrics = main()
EOF

    log_info "Training notebook created!"
}

# Create model deployment script
create_deployment_script() {
    log_info "Creating model deployment script..."
    
    cat > ../data_science/scripts/deploy_model.py <<'EOF'
"""
Deploy trained model to OCI Data Science Model Deployment
"""

import oci
import json
from datetime import datetime

def deploy_model(model_ocid, deployment_name):
    """Deploy model to endpoint"""
    config = oci.config.from_file()
    data_science = oci.data_science.DataScienceClient(config)
    
    # Get compartment and project from config
    compartment_id = config['tenancy']
    
    # Create deployment configuration
    deployment_config = oci.data_science.models.CreateModelDeploymentDetails(
        display_name=deployment_name,
        compartment_id=compartment_id,
        model_deployment_configuration_details=oci.data_science.models.SingleModelDeploymentConfigurationDetails(
            deployment_type="SINGLE_MODEL",
            model_configuration_details=oci.data_science.models.ModelConfigurationDetails(
                model_id=model_ocid,
                bandwidth_mbps=10,
                instance_configuration=oci.data_science.models.InstanceConfiguration(
                    instance_shape_name="VM.Standard.E4.Flex",
                    model_deployment_instance_shape_config_details=oci.data_science.models.ModelDeploymentInstanceShapeConfigDetails(
                        ocpus=2,
                        memory_in_gbs=16
                    )
                ),
                scaling_policy=oci.data_science.models.FixedSizeScalingPolicy(
                    policy_type="FIXED_SIZE",
                    instance_count=1
                )
            )
        )
    )
    
    # Create deployment
    response = data_science.create_model_deployment(deployment_config)
    
    print(f"Model deployment created: {response.data.id}")
    print(f"Deployment URL: {response.data.model_deployment_url}")
    
    return response.data

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python deploy_model.py <model_ocid> <deployment_name>")
        sys.exit(1)
    
    model_ocid = sys.argv[1]
    deployment_name = sys.argv[2]
    
    deploy_model(model_ocid, deployment_name)
EOF

    log_info "Deployment script created!"
}

# Create batch prediction script
create_batch_prediction_script() {
    log_info "Creating batch prediction script..."
    
    cat > ../data_science/scripts/batch_predict.py <<'EOF'
"""
Batch prediction script for processing multiple locations
"""

import pandas as pd
import joblib
import oci
from datetime import datetime
import json

def load_model_from_oci(bucket_name, model_path):
    """Load model from OCI Object Storage"""
    config = oci.config.from_file()
    object_storage = oci.object_storage.ObjectStorageClient(config)
    namespace = object_storage.get_namespace().data
    
    response = object_storage.get_object(namespace, bucket_name, model_path)
    
    with open('/tmp/model.pkl', 'wb') as f:
        for chunk in response.data.raw.stream(1024 * 1024, decode_content=False):
            f.write(chunk)
    
    model = joblib.load('/tmp/model.pkl')
    return model

def batch_predict(model, features_df):
    """Make predictions for batch of locations"""
    predictions = model.predict(features_df)
    probabilities = model.predict_proba(features_df)[:, 1]
    
    results = pd.DataFrame({
        'prediction': ['present' if p == 1 else 'absent' for p in predictions],
        'probability': probabilities
    })
    
    return results

def save_results_to_adb(results, location_ids):
    """Save predictions to database"""
    import cx_Oracle
    
    connection_string = os.getenv("DB_CONNECTION_STRING")
    conn = cx_Oracle.connect(connection_string)
    cursor = conn.cursor()
    
    for i, location_id in enumerate(location_ids):
        cursor.execute("""
            INSERT INTO predictions (
                prediction_id, location_id, prediction, probability,
                model_version, data_source, created_at
            ) VALUES (
                :1, :2, :3, :4, :5, :6, CURRENT_TIMESTAMP
            )
        """, (
            f"PRED_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}",
            location_id,
            results.iloc[i]['prediction'],
            float(results.iloc[i]['probability']),
            'v1.0',
            'batch'
        ))
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("Starting batch prediction...")
    
    # Load model
    model = load_model_from_oci("aquapredict-models", "models/aquifer_prediction_xgboost/latest/model.pkl")
    
    # Load features (example)
    features_df = pd.read_csv("/path/to/features.csv")
    location_ids = features_df['location_id'].tolist()
    
    # Make predictions
    results = batch_predict(model, features_df.drop('location_id', axis=1))
    
    # Save to database
    save_results_to_adb(results, location_ids)
    
    print(f"Processed {len(results)} predictions")
EOF

    log_info "Batch prediction script created!"
}

# Create README for Data Science setup
create_readme() {
    log_info "Creating Data Science README..."
    
    cat > ../data_science/README.md <<'EOF'
# AquaPredict OCI Data Science Setup

This directory contains notebooks, scripts, and configurations for ML model training and deployment on OCI Data Science.

## Directory Structure

```
data_science/
├── environments/          # Conda environment specifications
├── notebooks/            # Jupyter notebooks for training
├── scripts/              # Python scripts for deployment
└── README.md            # This file
```

## Setup Instructions

### 1. Access Notebook Session

Get the notebook URL from Terraform:
```bash
cd ../terraform
terraform output data_science_notebook_url
```

### 2. Install Conda Environment

In the notebook session terminal:
```bash
conda env create -f environments/aquapredict_env.yaml
conda activate aquapredict_ml
python -m ipykernel install --user --name aquapredict_ml --display-name "AquaPredict ML"
```

### 3. Configure Environment Variables

Create `.env` file in notebook session:
```bash
export DB_CONNECTION_STRING="user/pass@service_high"
export OCI_REGION="us-ashburn-1"
export BUCKET_NAME="aquapredict-models"
```

### 4. Train Models

Run the training notebook:
```bash
python notebooks/01_aquifer_model_training.py
```

### 5. Deploy Model

```bash
python scripts/deploy_model.py <model_ocid> aquifer-prediction-v1
```

## Model Training Workflow

1. **Data Loading**: Load features and labels from Oracle ADB
2. **Feature Engineering**: Prepare features for training
3. **Model Training**: Train XGBoost/LSTM models
4. **Evaluation**: Assess model performance
5. **Model Registry**: Save to OCI Object Storage and Model Catalog
6. **Deployment**: Deploy to OCI Data Science endpoints

## Batch Prediction

Process multiple locations:
```bash
python scripts/batch_predict.py
```

## Model Monitoring

Monitor deployed models:
- Access logs in OCI Logging
- Track metrics in Model Catalog
- Set up alerts for performance degradation

## Best Practices

1. **Version Control**: Tag all model versions
2. **Experiment Tracking**: Use MLflow for experiments
3. **Model Validation**: Always validate on holdout set
4. **Documentation**: Document model architecture and hyperparameters
5. **Monitoring**: Set up continuous monitoring

## Resources

- [OCI Data Science Documentation](https://docs.oracle.com/en-us/iaas/data-science/using/data-science.htm)
- [Oracle ADS SDK](https://accelerated-data-science.readthedocs.io/)
- [Model Deployment Guide](https://docs.oracle.com/en-us/iaas/data-science/using/model-dep-about.htm)
EOF

    log_info "README created!"
}

# Display notebook URL
display_notebook_info() {
    log_info "========================================="
    log_info "OCI Data Science Setup Complete"
    log_info "========================================="
    echo ""
    
    cd ../terraform
    NOTEBOOK_URL=$(terraform output -raw data_science_notebook_url 2>/dev/null)
    
    if [ -n "$NOTEBOOK_URL" ]; then
        log_info "Notebook Session URL: $NOTEBOOK_URL"
    else
        log_warn "Could not retrieve notebook URL. Check Terraform outputs."
    fi
    
    echo ""
    log_info "Next Steps:"
    log_info "1. Access the notebook session using the URL above"
    log_info "2. Install conda environment: conda env create -f environments/aquapredict_env.yaml"
    log_info "3. Run training notebook: python notebooks/01_aquifer_model_training.py"
    log_info "4. Deploy model: python scripts/deploy_model.py <model_ocid> <name>"
    log_info "========================================="
}

# Main function
main() {
    log_info "Setting up OCI Data Science for AquaPredict..."
    echo ""
    
    create_conda_env
    create_training_notebook
    create_deployment_script
    create_batch_prediction_script
    create_readme
    display_notebook_info
    
    log_info "Data Science setup completed successfully!"
}

main "$@"
