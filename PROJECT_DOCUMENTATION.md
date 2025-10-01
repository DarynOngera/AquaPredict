# AquaPredict - Official Project Documentation

**Version**: 1.0.0 | **Updated**: October 1, 2025 | **Status**: Production Ready

Enterprise geospatial AI platform for aquifer prediction, groundwater recharge forecasting, and ISO 14046-compliant water sustainability reporting.

---

## Overview

### Problem & Solution
- **Challenge**: Identifying groundwater resources and predicting recharge rates in water-scarce regions
- **Solution**: ML-powered platform using satellite data, Oracle Cloud Infrastructure, and spatial analytics
- **Pilot Region**: Kenya (scalable globally)

### Key Capabilities
- Aquifer presence prediction (XGBoost classifier)
- Groundwater recharge forecasting (LSTM, 12-month horizon)
- Spatial analytics with Oracle Spatial
- ISO 14046 water footprint reports
- Interactive web dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React + Next.js Frontend (OKE/Compute)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend Service (OKE/Compute)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│  Oracle ADB      │  OCI Object      │  OCI Data Science   │
│  (Spatial DB)    │  Storage         │  (ML Training)      │
└──────────────────┴──────────────────┴──────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Google Earth Engine (CHIRPS, ERA5, SRTM, Sentinel-2)      │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
- **Language**: Python 3.10+
- **API**: FastAPI 0.104+
- **ML**: scikit-learn, XGBoost 2.0+, PyTorch 2.0+
- **Geospatial**: Google Earth Engine, GeoPandas, Rasterio
- **Database**: Oracle Autonomous Database 19c (Spatial)
- **Cloud**: OCI Python SDK 2.112+

### Frontend
- **Framework**: Next.js 14, React 18, TypeScript 5.2+
- **Styling**: Tailwind CSS 3.3+, shadcn/ui
- **Maps**: Leaflet 1.9+
- **Charts**: Recharts 2.10+
- **State**: Zustand 4.4+

### Infrastructure
- **Cloud**: Oracle Cloud Infrastructure
- **IaC**: Terraform
- **Containers**: Docker, Kubernetes (OKE)
- **CI/CD**: GitHub Actions
- **Orchestration**: Apache Airflow

---

## System Components

### 1. Data Ingestion (`modules/data-ingestion/`)
Fetch satellite data from Google Earth Engine.

**Data Sources**:
- CHIRPS: Precipitation (0.05°, daily)
- ERA5: Temperature, evapotranspiration (0.25°, daily)
- SRTM: Elevation (30m)
- ESA WorldCover: Land cover (10m)
- Sentinel-2: NDVI (10m)

**Usage**:
```bash
cd modules/data-ingestion
python main.py --dataset chirps --start-date 2023-01-01 --end-date 2023-12-31 \
  --bounds 33.9 -4.7 41.9 5.5 --output-bucket aquapredict-data-raw
```

### 2. Preprocessing (`modules/preprocessing/`)
Clean, validate, and normalize raw data.

**Features**:
- Missing value imputation (interpolation, mean, median)
- Outlier removal (z-score, IQR)
- Normalization (min-max, z-score, robust)
- Spatial/temporal alignment

### 3. Feature Engineering (`modules/feature-engineering/`)
Compute geospatial and temporal features.

**Key Features**:
- **TWI**: `ln((flow_accumulation + 1) / (tan(slope) + 0.001))`
- **TPI**: Topographic Position Index
- **SPI**: Standardized Precipitation Index (1, 3, 6, 12 months)
- **SPEI**: Standardized Precipitation-Evapotranspiration Index
- **PET**: Potential Evapotranspiration (Hargreaves method)

### 4. Modeling (`modules/modeling/`)
Train and evaluate ML models.

**Models**:
- **Aquifer Classifier**: Random Forest, XGBoost (ROC-AUC validation)
- **Recharge Forecaster**: LSTM, TFT (RMSE, MAE, R² metrics)
- Spatial cross-validation
- Hyperparameter tuning (Optuna)

**Training**:
```bash
cd modules/modeling
python main.py --train --model-type xgboost --data-path ../data/features.csv \
  --output-path models/aquifer_v1.pkl
```

### 5. Backend API (`modules/backend/`)
Comprehensive FastAPI service.

**Key Endpoints**:
- `POST /api/v1/predict/aquifer` - Predict aquifer presence
- `POST /api/v1/predict/recharge` - Forecast recharge
- `POST /api/v1/recommendations/extraction` - Extraction recommendations
- `GET /api/v1/settings` - Get/update settings
- `POST /api/v1/export` - Export data (CSV, JSON, GeoJSON, PDF)
- `GET /api/v1/models` - List/reload models

**Run Locally**:
```bash
cd modules/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# API Docs: http://localhost:8000/api/docs
```

### 6. Frontend (`modules/frontend/`)
Interactive web dashboard.

**Features**:
- Interactive Leaflet map
- Click-to-predict functionality
- Real-time prediction display
- Recharge forecast charts
- Settings management
- Data export interface
- Responsive design, dark mode

**Run Locally**:
```bash
cd modules/frontend
npm install
npm run dev
# Frontend: http://localhost:3000
```

### 7. Reporting (`modules/reporting/`)
ISO 14046-compliant water footprint reports (PDF generation with ReportLab).

### 8. Orchestration (`modules/orchestration/`)
Apache Airflow DAGs for automated pipelines.

---

## Data Pipeline

```
1. DATA INGESTION
   Google Earth Engine → Raw Data → OCI Object Storage

2. PREPROCESSING
   Raw Data → Cleaning → Normalization → OCI Object Storage

3. FEATURE ENGINEERING
   Processed Data → TWI, SPI, SPEI → Oracle ADB

4. MODEL TRAINING
   Features → Training → Models → OCI Object Storage

5. PREDICTION
   New Data + Models → Predictions → Oracle ADB

6. VISUALIZATION
   Oracle ADB → API → Frontend → User
```

---

## API Reference

### Base URL
- **Local**: `http://localhost:8000`
- **Production**: `https://api.aquapredict.com`
- **Docs**: `/api/docs` (Swagger UI)

### Example: Predict Aquifer
```bash
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "use_real_data": true
  }'
```

### Example: Forecast Recharge
```bash
curl -X POST "http://localhost:8000/api/v1/predict/recharge" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "horizon": 12,
    "use_real_data": true
  }'
```

---

## Infrastructure (OCI)

### Components
- **Oracle Autonomous Database**: Spatial data store (2 OCPUs, 1TB, auto-scaling)
- **OKE Cluster**: Kubernetes (3 nodes, VM.Standard.E4.Flex)
- **Compute Instances**: Backend API, data processor (2 OCPUs, 16GB RAM each)
- **Object Storage**: 5 buckets (raw, processed, models, reports, backups)
- **Data Science**: Notebooks, model catalog, deployment endpoints
- **Load Balancer**: High availability

### Deployment
```bash
# Configure OCI CLI
oci setup config

# Deploy infrastructure
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Post-deployment
oci ce cluster create-kubeconfig --cluster-id <cluster-ocid> --file ~/.kube/config
kubectl get nodes
```

See `TERRAFORM_DEPLOYMENT_COMMANDS.md` for detailed commands.

---

## Configuration

### Environment Variables (.env)
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
OCI_REGION=us-ashburn-1
COMPARTMENT_ID=ocid1.compartment.oc1..xxx

# Google Earth Engine
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=./credentials/gee_key.json

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Development Workflow

### Local Development
```bash
# Clone repository
git clone https://github.com/yourusername/AquaPredict.git
cd AquaPredict

# Setup environment
cp .env.example .env
# Edit .env with your credentials

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Authenticate GEE
earthengine authenticate

# Start services with Docker Compose
docker-compose up -d

# Access
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# Airflow: http://localhost:8080
```

### Data Pipeline
```bash
# Ingest data
cd modules/data-ingestion
python main.py --dataset chirps --start-date 2023-01-01 --end-date 2023-12-31

# Preprocess
cd ../preprocessing
python main.py --input-bucket aquapredict-data-raw --output-bucket aquapredict-data-processed

# Generate features
cd ../feature-engineering
python main.py --save-to-adb

# Train models
cd ../modeling
python main.py --train --model-type xgboost --save-to-storage
```

---

## Testing

```bash
# All tests
pytest tests/ -v --cov

# Specific module
pytest modules/modeling/tests/ -v

# Integration tests
pytest tests/integration/ -v

# Frontend tests
cd modules/frontend
npm test
```

---

## Security

- **Network**: Private subnets, security lists, NSGs
- **IAM**: Least privilege access policies
- **Secrets**: OCI Vault for sensitive data
- **Encryption**: At-rest and in-transit
- **Audit**: Logging enabled for all resources

---

## Performance

### Targets
- **Prediction Latency**: < 200ms per location
- **Batch Processing**: 1000 locations/minute
- **Model Accuracy**: ROC-AUC > 0.85
- **Forecast RMSE**: < 15% of mean
- **API Uptime**: 99.9%

### Optimization
- Auto-scaling (ADB, OKE)
- Model caching
- Connection pooling
- CDN for static assets

---

## Monitoring & Maintenance

### Health Checks
```bash
# API health
curl http://<load-balancer-ip>/health

# Database connection
sqlplus admin/<password>@aquapredict_high <<< "SELECT 'Connected' FROM dual;"

# Kubernetes pods
kubectl get pods -n aquapredict
```

### Logs
```bash
# API logs
ssh opc@<backend-ip> "sudo journalctl -u aquapredict-api -f"

# Database audit logs
sqlplus admin/<password>@aquapredict_high <<< "SELECT * FROM audit_logs ORDER BY created_at DESC FETCH FIRST 20 ROWS ONLY;"

# Kubernetes logs
kubectl logs -f deployment/backend -n aquapredict
```

### Backups
- **ADB**: Automatic daily backups (60-day retention)
- **Object Storage**: Cross-region replication
- **Kubernetes**: Velero for cluster backups

---

## Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
# Check TNS_ADMIN
echo $TNS_ADMIN
# Verify wallet files
ls -la $TNS_ADMIN
# Test connection
tnsping aquapredict_high
```

**API Not Responding**:
```bash
# Check service status
ssh opc@<backend-ip> "sudo systemctl status aquapredict-api"
# Check Docker
ssh opc@<backend-ip> "sudo docker ps"
# View logs
ssh opc@<backend-ip> "sudo docker logs aquapredict-api"
```

**GEE Authentication Error**:
```bash
# Re-authenticate
earthengine authenticate
# Or use service account
export GEE_SERVICE_ACCOUNT=your-account@project.iam.gserviceaccount.com
export GEE_PRIVATE_KEY_FILE=/path/to/key.json
```

---

## Project Structure

```
AquaPredict/
├── modules/
│   ├── data-ingestion/          # GEE data fetching
│   ├── preprocessing/           # Data cleaning
│   ├── feature-engineering/     # TWI, SPI, SPEI
│   ├── modeling/                # ML models
│   ├── backend/                 # FastAPI service
│   ├── frontend/                # React dashboard
│   ├── reporting/               # ISO reports
│   └── orchestration/           # Airflow DAGs
├── infrastructure/
│   ├── terraform/               # IaC
│   └── k8s/                     # Kubernetes manifests
├── scripts/                     # Automation scripts
├── tests/                       # Test suite
├── docs/                        # Documentation
├── docker-compose.yml           # Local development
├── Makefile                     # Task automation
└── README.md                    # Main documentation
```

---

## Contributing

```bash
# Fork and clone
git clone https://github.com/your-username/AquaPredict.git
cd AquaPredict

# Create branch
git checkout -b feature/your-feature-name

# Make changes and test
pytest tests/ -v

# Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

**Code Style**:
- Python: PEP 8, Black formatting
- TypeScript: ESLint configuration
- Commits: Conventional commits (feat:, fix:, docs:)

---

## Cost Estimation (Monthly)

| Component | Configuration | Cost |
|-----------|--------------|------|
| Compute (2 instances) | 2 OCPUs, 16GB RAM each | $140 |
| Autonomous Database | 2 OCPUs, 1TB storage | $520 |
| Object Storage | 1TB standard | $23 |
| Load Balancer | Flexible, 10-100 Mbps | $20 |
| **Total** | | **~$703/month** |

**Free Tier Option**: Use Always Free tier (2 ADB, 2 compute, 10GB storage) = $0/month

---

## Resources

- **GitHub**: https://github.com/yourusername/AquaPredict
- **API Docs**: http://localhost:8000/api/docs
- **OCI Documentation**: https://docs.oracle.com/iaas
- **Terraform Provider**: https://registry.terraform.io/providers/oracle/oci
- **Google Earth Engine**: https://developers.google.com/earth-engine

---

## License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for sustainable water management**

**Team**: AquaPredict Development Team  
**Contact**: support@aquapredict.com  
**Version**: 1.0.0  
**Last Updated**: October 1, 2025
