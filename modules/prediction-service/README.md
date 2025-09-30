# Prediction Service

FastAPI-based REST API for aquifer prediction and groundwater recharge forecasting.

## Features

- RESTful API endpoints for predictions
- Model serving with caching
- Batch prediction support
- Geospatial query support
- Real-time inference
- Swagger/OpenAPI documentation
- CORS support for frontend integration
- Oracle ADB integration for data persistence

## API Endpoints

### Prediction Endpoints
- `POST /api/v1/predict/aquifer` - Predict aquifer presence
- `POST /api/v1/predict/depth` - Predict aquifer depth
- `POST /api/v1/predict/recharge` - Forecast groundwater recharge
- `POST /api/v1/predict/batch` - Batch predictions

### Data Endpoints
- `GET /api/v1/data/features` - Get available features
- `GET /api/v1/data/region/{region_id}` - Get region data
- `POST /api/v1/data/query` - Query spatial data

### Model Endpoints
- `GET /api/v1/models` - List available models
- `GET /api/v1/models/{model_id}` - Get model info
- `POST /api/v1/models/reload` - Reload models

### Health Endpoints
- `GET /health` - Health check
- `GET /ready` - Readiness check

## Usage

```bash
# Start service
uvicorn main:app --host 0.0.0.0 --port 8000

# Access API docs
http://localhost:8000/docs

# Example prediction
curl -X POST "http://localhost:8000/api/v1/predict/aquifer" \
  -H "Content-Type: application/json" \
  -d '{"features": {...}, "location": {"lat": 0.0, "lon": 36.0}}'
```

## Testing

```bash
pytest tests/
```
