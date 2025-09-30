# AquaPredict Quick Start Guide

Get AquaPredict up and running in 15 minutes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Google Earth Engine account
- 8GB RAM minimum
- 20GB free disk space

## Step 1: Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd AquaPredict

# Run setup script
make setup

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required variables:**
```env
# Google Earth Engine (for data ingestion)
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=./credentials/gee_key.json

# Database (optional for local dev)
DATABASE_URL=sqlite:///./aquapredict.db

# Mapbox (for frontend maps)
MAPBOX_TOKEN=pk.your_mapbox_token
```

## Step 3: Authenticate with Google Earth Engine

```bash
# Interactive authentication
earthengine authenticate

# Or use service account
# Place your GEE service account key in credentials/gee_key.json
```

## Step 4: Start Services

### Option A: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services will be available at:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Airflow: http://localhost:8080 (admin/admin)

### Option B: Manual Start (Development)

**Terminal 1 - API:**
```bash
cd modules/prediction-service
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd modules/frontend
npm run dev
```

## Step 5: Ingest Sample Data

```bash
# Fetch data for Kenya (this may take 10-30 minutes)
make ingest-data

# Or manually:
cd modules/data-ingestion
python main.py --dataset precipitation --start-date 2023-01-01 --end-date 2023-12-31
```

## Step 6: Process Data and Train Models

```bash
# Preprocess data
make preprocess-data

# Generate features
make generate-features

# Train models
make train-models
```

## Step 7: Make Your First Prediction

### Via API (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0, "lon": 36.0},
    "use_cached_features": false,
    "features": {
      "elevation": 1500,
      "slope": 5.2,
      "twi": 8.5,
      "precip_mean": 800,
      "temp_mean": 22.5
    }
  }'
```

### Via Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict/aquifer",
    json={
        "location": {"lat": 0.0, "lon": 36.0},
        "use_cached_features": True
    }
)

print(response.json())
```

### Via Frontend

1. Open http://localhost:3000
2. Click on the map to select a location
3. Click "Predict Aquifer"
4. View results in the sidebar

## Common Tasks

### View API Documentation

```bash
# Open in browser
open http://localhost:8000/docs
```

### Check Service Health

```bash
curl http://localhost:8000/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f prediction-service
```

### Stop Services

```bash
docker-compose down
```

### Clean Up

```bash
# Remove containers and volumes
docker-compose down -v

# Clean Python cache
make clean
```

## Troubleshooting

### GEE Authentication Failed

```bash
# Re-authenticate
earthengine authenticate

# Check credentials
ls -la ~/.config/earthengine/
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

### Docker Out of Memory

```bash
# Increase Docker memory limit to 8GB
# Docker Desktop > Settings > Resources > Memory

# Or reduce service replicas in docker-compose.yml
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.10+
```

### Database Connection Failed

```bash
# For local development, use SQLite (no setup needed)
DATABASE_URL=sqlite:///./aquapredict.db

# Or start PostgreSQL
docker-compose up -d postgres
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Customize Models**: Edit `modules/modeling/config.py`
3. **Add More Data**: Modify `modules/data-ingestion/config.py`
4. **Deploy to Production**: See `infrastructure/README.md`
5. **Read Full Documentation**: See `docs/IMPLEMENTATION_GUIDE.md`

## Sample Workflow

```bash
# Complete data pipeline
make ingest-data          # Fetch from GEE
make preprocess-data      # Clean and normalize
make generate-features    # Compute TWI, SPI, SPEI
make train-models         # Train ML models

# Start services
make deploy-local

# Make predictions via API
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 0.0, "lon": 36.0}}'
```

## Getting Help

- **Documentation**: `docs/` directory
- **Issues**: GitHub Issues
- **API Docs**: http://localhost:8000/docs
- **Logs**: `docker-compose logs -f`

## Development Tips

1. **Use virtual environment**: Always activate venv before working
2. **Run tests**: `make test` before committing
3. **Check logs**: Monitor logs for errors
4. **Use API docs**: Interactive testing at `/docs`
5. **Hot reload**: API and frontend support hot reload in dev mode

## Production Deployment

For production deployment to OCI, see:
- `infrastructure/README.md` - Full deployment guide
- `scripts/deploy_oci.sh` - Automated deployment script
- `docs/IMPLEMENTATION_GUIDE.md` - Architecture details

```bash
# Deploy to OCI (requires OCI account)
make deploy-oci
```

---

**You're all set!** 🎉

Visit http://localhost:3000 to start predicting aquifers.
