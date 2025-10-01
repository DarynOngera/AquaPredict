# AquaPredict Quick Reference

## 🚀 Quick Start

```bash
# 1. Start backend
./scripts/start_backend.sh

# 2. Start frontend (new terminal)
cd modules/frontend && npm run dev

# 3. Access apps
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

## 📦 Add Your Colab Models

```bash
# Copy trained models to models/ directory
mkdir -p models
cp ~/Downloads/aquifer_classifier.pkl models/
cp ~/Downloads/recharge_forecaster.pkl models/

# Restart backend or reload via API
curl -X POST http://localhost:8000/api/v1/models/reload
```

## 🧪 Test Backend

```bash
# Run test suite
./scripts/test_backend.sh

# Quick health check
curl http://localhost:8000/health

# Test prediction
curl -X POST http://localhost:8000/api/v1/predict/aquifer \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 0.0236, "lon": 37.9062}, "use_real_data": false}'
```

## 🐳 Docker Deployment

```bash
# Start with Docker Compose
docker-compose up -d backend frontend

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📊 Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/predict/aquifer` | POST | Predict aquifer |
| `/api/v1/predict/recharge` | POST | Forecast recharge |
| `/api/v1/recommendations/extraction` | POST | Get recommendations |
| `/api/v1/settings` | GET/PUT | Manage settings |
| `/api/v1/export` | POST | Export data |
| `/api/v1/models` | GET | List models |
| `/api/v1/models/reload` | POST | Reload models |

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `models/` | Trained ML models |
| `data/settings.json` | User settings |
| `credentials/gee_key.json` | GEE credentials |

## 📚 Documentation

- **Backend Guide**: `BACKEND_DEPLOYMENT_GUIDE.md`
- **Integration Guide**: `INTEGRATION_GUIDE.md`
- **Implementation Summary**: `BACKEND_IMPLEMENTATION_SUMMARY.md`
- **API Docs**: http://localhost:8000/api/docs

## ⚡ Common Commands

```bash
# Backend
cd modules/backend
source venv/bin/activate
uvicorn main:app --reload

# Frontend
cd modules/frontend
npm run dev

# Test
./scripts/test_backend.sh

# Docker
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## 🎯 Features

✅ Aquifer prediction with ML models  
✅ Recharge forecasting  
✅ GEE data integration  
✅ Simulated data fallbacks  
✅ Settings management  
✅ Export (CSV, JSON, GeoJSON, PDF)  
✅ Model management  
✅ Docker deployment  

## 🆘 Troubleshooting

**Backend won't start**
```bash
# Check Python version
python3 --version  # Need 3.10+

# Install dependencies
cd modules/backend
pip install -r requirements.txt
```

**Models not loading**
```bash
# Check models exist
ls -la models/

# Reload models
curl -X POST http://localhost:8000/api/v1/models/reload
```

**GEE not working**
- Backend will automatically use simulated data fallback
- Check `credentials/gee_key.json` exists
- Verify `GEE_SERVICE_ACCOUNT` in `.env`

## 📞 Support

- Check logs: `docker-compose logs backend`
- API docs: http://localhost:8000/api/docs
- Read guides in project root
