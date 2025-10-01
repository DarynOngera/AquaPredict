# AquaPredict Integration Guide

Complete guide for integrating the frontend with the backend service and deploying the full stack.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AquaPredict Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Frontend   │ ◄─────► │   Backend    │                 │
│  │  (Next.js)   │  HTTP   │  (FastAPI)   │                 │
│  │  Port 3000   │         │  Port 8000   │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                          ┌────────┴────────┐                │
│                          │                 │                │
│                   ┌──────▼──────┐   ┌─────▼──────┐         │
│                   │     GEE     │   │   Models   │         │
│                   │  (Optional) │   │ (From Colab)│        │
│                   └─────────────┘   └────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Backend Capabilities
✅ **Aquifer Prediction** - ML-based prediction using GEE data or simulated fallback  
✅ **Recharge Forecasting** - LSTM-based groundwater recharge forecasting  
✅ **Extraction Recommendations** - Sustainable extraction rate calculations  
✅ **Settings Management** - User preferences and configuration  
✅ **Data Export** - CSV, JSON, GeoJSON, PDF export formats  
✅ **Model Management** - Upload and manage Colab-trained models  
✅ **Simulated Fallbacks** - Realistic data when GEE unavailable  

### Frontend Features
✅ **Interactive Map** - Click to select locations for prediction  
✅ **Real-time Predictions** - Instant aquifer presence predictions  
✅ **Forecast Visualization** - Charts for recharge forecasts  
✅ **Settings Panel** - Configure app preferences  
✅ **Export Functionality** - Download predictions and reports  
✅ **History Tracking** - View past predictions  

---

## Quick Start (Full Stack)

### 1. Prerequisites

```bash
# Check requirements
docker --version  # Docker 20.10+
docker-compose --version  # Docker Compose 1.29+
node --version  # Node.js 18+
python3 --version  # Python 3.10+
```

### 2. Clone and Setup

```bash
cd /home/ongera/projects/AquaPredict

# Copy environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

### 3. Add Models (Optional but Recommended)

```bash
# Create models directory
mkdir -p models

# Copy your trained models from Colab
# See BACKEND_DEPLOYMENT_GUIDE.md for training instructions
cp ~/Downloads/aquifer_classifier.pkl models/
cp ~/Downloads/recharge_forecaster.pkl models/
```

### 4. Start Full Stack

```bash
# Start backend and frontend
docker-compose up -d backend frontend

# Or start individually
./scripts/start_backend.sh  # Terminal 1
cd modules/frontend && npm run dev  # Terminal 2
```

### 5. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

---

## Development Setup

### Backend Development

```bash
cd modules/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd modules/frontend

# Install dependencies
npm install

# Set API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

---

## API Integration Examples

### 1. Predict Aquifer Presence

**Frontend (TypeScript)**
```typescript
import { api } from '@/lib/api'

// Make prediction
const prediction = await api.predictAquifer(
  { lat: 0.0236, lon: 37.9062 },
  true  // use real GEE data
)

console.log(`Probability: ${prediction.probability}`)
console.log(`Recommended depth: ${prediction.recommended_drilling_depth}`)
```

**cURL**
```bash
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"lat": 0.0236, "lon": 37.9062},
    "use_real_data": true
  }'
```

**Python**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/predict/aquifer',
    json={
        'location': {'lat': 0.0236, 'lon': 37.9062},
        'use_real_data': True
    }
)

prediction = response.json()
print(f"Probability: {prediction['probability']:.2%}")
```

### 2. Forecast Recharge

**Frontend (TypeScript)**
```typescript
const forecast = await api.forecastRecharge(
  { lat: 0.0236, lon: 37.9062 },
  12,  // 12 months
  true  // use real data
)

console.log(`Sustainability: ${forecast.summary.sustainability_status}`)
```

### 3. Export Data

**Frontend (TypeScript)**
```typescript
// Export prediction as PDF
const blob = await api.exportData(
  'prediction',
  'pdf',
  prediction,
  true  // include metadata
)

// Download file
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = 'prediction_report.pdf'
a.click()
```

### 4. Manage Settings

**Frontend (TypeScript)**
```typescript
// Get settings
const settings = await api.getSettings()

// Update settings
await api.updateSettings({
  theme: 'dark',
  map_zoom: 8,
  confidence_threshold: 0.7
})

// Reset to defaults
await api.resetSettings()
```

---

## Data Flow

### Prediction Flow

```
User clicks map
     ↓
Frontend captures coordinates
     ↓
API call to /api/v1/predict/aquifer
     ↓
Backend checks GEE availability
     ↓
├─ GEE Available → Fetch real data from GEE
└─ GEE Unavailable → Generate simulated data
     ↓
Load ML model (or use heuristics)
     ↓
Make prediction
     ↓
Return result to frontend
     ↓
Display on map and panel
```

### Export Flow

```
User requests export
     ↓
Frontend sends data to /api/v1/export
     ↓
Backend formats data (CSV/JSON/GeoJSON/PDF)
     ↓
Return file as blob
     ↓
Frontend triggers download
```

---

## Configuration

### Backend Configuration

**Environment Variables** (`.env`)
```bash
# Google Earth Engine
GEE_SERVICE_ACCOUNT=your-account@project.iam.gserviceaccount.com
GEE_PRIVATE_KEY_FILE=./credentials/gee_key.json

# API
API_HOST=0.0.0.0
API_PORT=8000
```

**Settings** (`data/settings.json`)
```json
{
  "general": {
    "theme": "system",
    "language": "English",
    "timezone": "Africa/Nairobi"
  },
  "models": {
    "aquifer_model": "XGBoost",
    "recharge_model": "LSTM",
    "confidence_threshold": 0.6
  }
}
```

### Frontend Configuration

**Environment Variables** (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

---

## Testing

### Test Backend

```bash
# Run test suite
./scripts/test_backend.sh

# Test specific endpoint
curl http://localhost:8000/health
```

### Test Frontend

```bash
cd modules/frontend

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

### Integration Testing

```bash
# Start both services
docker-compose up -d backend frontend

# Test full flow
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # Backend

# Test prediction flow
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 0.0236, "lon": 37.9062}, "use_real_data": false}'
```

---

## Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3
```

### Kubernetes

```bash
# Apply configurations
kubectl apply -f infrastructure/k8s/namespace.yaml
kubectl apply -f infrastructure/k8s/deployments/

# Check status
kubectl get pods -n aquapredict
```

### Manual Deployment

**Backend**
```bash
cd modules/backend
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

**Frontend**
```bash
cd modules/frontend
npm run build
npm start
```

---

## Troubleshooting

### Issue: Frontend can't connect to backend

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. CORS is configured correctly in backend
3. API URL is correct in frontend `.env.local`

**Solution:**
```bash
# Backend - check CORS in main.py
# Frontend - verify NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_API_URL
```

### Issue: Predictions are slow

**Solutions:**
1. Use simulated data for testing: `use_real_data: false`
2. Cache predictions in backend
3. Increase backend workers
4. Use CDN for frontend assets

### Issue: Models not loading

**Check:**
1. Models exist: `ls -la models/`
2. Models are valid: Check file size and format
3. Backend logs: `docker-compose logs backend`

**Solution:**
```bash
# Reload models via API
curl -X POST http://localhost:8000/api/v1/models/reload
```

---

## Performance Optimization

### Backend
- Use connection pooling for database
- Enable caching for frequent requests
- Use multiple workers (4-8 for production)
- Optimize GEE queries

### Frontend
- Enable Next.js image optimization
- Use React.memo for expensive components
- Implement virtual scrolling for lists
- Lazy load map components

---

## Security

### Backend
- Enable HTTPS in production
- Use environment variables for secrets
- Implement rate limiting
- Add authentication/authorization

### Frontend
- Sanitize user inputs
- Use HTTPS only
- Implement CSP headers
- Validate API responses

---

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000/api/health
```

### Logs

```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Application logs
tail -f modules/backend/logs/app.log
```

### Metrics

```bash
# Model status
curl http://localhost:8000/api/v1/models

# Data source status
curl http://localhost:8000/api/v1/data/sources
```

---

## Next Steps

1. ✅ Backend and frontend integrated
2. ✅ Models loaded from Colab
3. ✅ GEE integration or fallback working
4. 🔄 Test all features end-to-end
5. 🔄 Configure production settings
6. 🔄 Set up CI/CD pipeline
7. 🔄 Deploy to production

## Resources

- **Backend API Docs**: http://localhost:8000/api/docs
- **Backend README**: `/modules/backend/README.md`
- **Deployment Guide**: `/BACKEND_DEPLOYMENT_GUIDE.md`
- **Frontend README**: `/modules/frontend/README.md`
