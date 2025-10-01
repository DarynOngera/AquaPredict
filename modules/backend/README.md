# AquaPredict Backend Service

Comprehensive backend API for the AquaPredict platform with Google Earth Engine integration, ML model inference, settings management, and data export capabilities.

## Features

- **Aquifer Prediction**: ML-based aquifer presence prediction using GEE data
- **Recharge Forecasting**: LSTM-based groundwater recharge forecasting
- **Extraction Recommendations**: Sustainable extraction rate calculations
- **Settings Management**: User preferences and configuration
- **Data Export**: Export predictions and forecasts in CSV, JSON, GeoJSON, and PDF formats
- **Simulated Fallbacks**: Realistic simulated data when GEE is unavailable
- **Model Management**: Upload and manage trained models from Colab

## Architecture

```
backend/
├── main.py                 # FastAPI application
├── gee_service.py          # Google Earth Engine integration
├── model_service.py        # ML model loading and inference
├── simulated_data.py       # Fallback data generation
├── settings_service.py     # Settings management
├── export_service.py       # Data export (CSV, JSON, GeoJSON, PDF)
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
└── README.md              # This file
```

## Setup

### 1. Environment Variables

Create a `.env` file:

```bash
# Google Earth Engine
GEE_SERVICE_ACCOUNT=your-service-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=./credentials/gee_key.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Your Trained Models

Place your trained models from Colab in the `models/` directory:

```bash
models/
├── aquifer_classifier.pkl    # XGBoost/Random Forest classifier
└── recharge_forecaster.pkl   # LSTM forecaster
```

**Model Format**: Models should be saved using `joblib` or `pickle` and have:
- `predict_proba()` method for aquifer classifier
- `predict()` method for recharge forecaster

### 4. Run the Service

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Docker Deployment

```bash
# Build
docker build -t aquapredict-backend .

# Run
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/credentials:/app/credentials \
  -e GEE_SERVICE_ACCOUNT=your-account@project.iam.gserviceaccount.com \
  aquapredict-backend
```

## API Endpoints

### Health & Status

- `GET /` - API information
- `GET /health` - Health check

### Predictions

- `POST /api/v1/predict/aquifer` - Predict aquifer presence
- `POST /api/v1/predict/recharge` - Forecast groundwater recharge
- `POST /api/v1/recommendations/extraction` - Get extraction recommendations

### Settings

- `GET /api/v1/settings` - Get current settings
- `PUT /api/v1/settings` - Update settings
- `POST /api/v1/settings/reset` - Reset to defaults

### Export

- `POST /api/v1/export` - Export data (CSV, JSON, GeoJSON, PDF)

### Models

- `GET /api/v1/models` - List available models
- `POST /api/v1/models/reload` - Reload models
- `POST /api/v1/models/upload` - Upload new model

### Data Sources

- `GET /api/v1/data/sources` - Get data source status
- `GET /api/v1/data/features` - Get feature information

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Example Usage

### Predict Aquifer Presence

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict/aquifer",
    json={
        "location": {"lat": 0.0236, "lon": 37.9062},
        "use_real_data": True
    }
)

prediction = response.json()
print(f"Probability: {prediction['probability']:.2%}")
print(f"Recommended depth: {prediction['recommended_drilling_depth']}")
```

### Forecast Recharge

```python
response = requests.post(
    "http://localhost:8000/api/v1/predict/recharge",
    json={
        "location": {"lat": 0.0236, "lon": 37.9062},
        "horizon": 12,
        "use_real_data": True
    }
)

forecast = response.json()
print(f"Sustainability: {forecast['summary']['sustainability_status']}")
```

### Export Data

```python
response = requests.post(
    "http://localhost:8000/api/v1/export",
    json={
        "export_type": "prediction",
        "format": "pdf",
        "data": prediction,
        "include_metadata": True
    }
)

with open("prediction_report.pdf", "wb") as f:
    f.write(response.content)
```

## Uploading Models from Colab

After training your models in Google Colab:

```python
# In Colab - Save your model
import joblib

# Save aquifer classifier
joblib.dump(aquifer_model, 'aquifer_classifier.pkl')

# Save recharge forecaster
joblib.dump(recharge_model, 'recharge_forecaster.pkl')

# Download files from Colab
from google.colab import files
files.download('aquifer_classifier.pkl')
files.download('recharge_forecaster.pkl')
```

Then upload to the backend:

```bash
# Copy to models directory
cp aquifer_classifier.pkl models/
cp recharge_forecaster.pkl models/

# Or use the API
curl -X POST "http://localhost:8000/api/v1/models/upload?model_type=aquifer" \
  -F "model_file=@aquifer_classifier.pkl"
```

## Data Sources

### Primary: Google Earth Engine
- **Precipitation**: CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data)
- **Temperature**: ERA5 (ECMWF Reanalysis v5)
- **Elevation**: SRTM (Shuttle Radar Topography Mission)
- **Land Cover**: ESA WorldCover
- **NDVI**: Sentinel-2

### Fallback: Simulated Data
When GEE is unavailable, the service generates realistic simulated data based on:
- Regional hydrogeological characteristics
- Topographic relationships
- Climate patterns for Kenya
- Seasonal variations

## Configuration

Settings are stored in `data/settings.json` and can be managed via the API or directly edited.

## Troubleshooting

### GEE Authentication Issues
```bash
# Initialize GEE authentication
earthengine authenticate

# Or use service account
export GEE_SERVICE_ACCOUNT=your-account@project.iam.gserviceaccount.com
export GEE_PRIVATE_KEY_FILE=/path/to/key.json
```

### Models Not Loading
- Ensure models are in `models/` directory
- Check model format (must be joblib/pickle compatible)
- Verify model has required methods (`predict_proba`, `predict`)

### Port Already in Use
```bash
# Change port
uvicorn main:app --port 8001
```

## Performance

- **Prediction latency**: ~2-5 seconds with GEE, <1 second with simulated data
- **Concurrent requests**: Supports 100+ concurrent requests with 4 workers
- **Model inference**: <100ms per prediction

## License

MIT License - See LICENSE file for details
