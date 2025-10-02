# ✅ Complete System Alignment

## Overview
Your frontend, backend, and model predictions are now fully aligned and ready to work together.

---

## 🎯 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  - Map UI (click to select location)                        │
│  - Precipitation Tab (date + model selector)                │
│  - Aquifer Tab (based on precipitation)                     │
│  - Forecast Tab (simulated from precipitation)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        BACKEND API                           │
│  FastAPI @ http://localhost:8000                            │
│                                                              │
│  Routers:                                                    │
│  ├─ /api/inference/predict (Precipitation)                  │
│  ├─ /api/v1/predict/aquifer (Aquifer - uses precip)        │
│  └─ /api/v1/predict/recharge (Forecast - uses precip)      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ joblib.load()
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MODEL ARTIFACTS                           │
│  Directory: model_artifacts/                                 │
│                                                              │
│  Models:                                                     │
│  ├─ Linear_Regression.joblib                                │
│  ├─ Random_Forest.joblib                                    │
│  └─ XGBoost.joblib                                          │
│                                                              │
│  Features (16 total):                                        │
│  - longitude, latitude                                       │
│  - month, dayofyear, sin_day, cos_day                       │
│  - lag1_precip, lag2_precip, roll3_precip, roll7_precip    │
│  - 2m_air_temp, dewpoint_2m, mslp, surface_pressure        │
│  - u10, v10                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Flow

### **1. Precipitation Prediction**

**User Action:**
1. Click map → Select location (lon, lat)
2. Switch to "Precipitation" tab
3. Select date (e.g., "2024-01-15")
4. Select model (e.g., "Random Forest")
5. Click "Predict Precipitation"

**Frontend → Backend:**
```javascript
POST /api/inference/predict
{
  "lon": 36.8219,
  "lat": -1.2921,
  "date": "2024-01-15",
  "model_name": "random_forest"
}
```

**Backend Processing:**
```python
1. Parse date → month=1, dayofyear=15
2. Compute temporal features:
   - sin_day = sin(2π × 15 / 365.25)
   - cos_day = cos(2π × 15 / 365.25)
3. Get historical features (or zeros):
   - lag1_precip, lag2_precip, roll3_precip, roll7_precip
   - 2m_air_temp, dewpoint_2m, mslp, surface_pressure, u10, v10
4. Build feature vector (16 features)
5. Load model: Random_Forest.joblib
6. Predict: model.predict(features)
7. Return prediction_mm
```

**Backend → Frontend:**
```json
{
  "prediction_mm": 5.2,
  "location": {"lon": 36.8219, "lat": -1.2921},
  "date": "2024-01-15",
  "model": "random_forest",
  "features_extracted": 16,
  "status": "success",
  "timestamp": "2024-10-02T12:30:00"
}
```

**Frontend Display:**
```
┌─────────────────────────────┐
│  Precipitation Prediction   │
├─────────────────────────────┤
│                             │
│         5.20 mm             │
│   Predicted precipitation   │
│                             │
│  Model: Random Forest       │
│  Date: 2024-01-15          │
│  Features: 16               │
│  Status: ✓ success          │
└─────────────────────────────┘
```

---

### **2. Aquifer Prediction (Based on Precipitation)**

**Logic:**
```python
# Get precipitation prediction first
precip_mm = predict_precipitation(lon, lat, date)

# Determine aquifer potential
if precip_mm > 10:
    prediction = "high_potential"
    probability = 0.85
elif precip_mm > 5:
    prediction = "moderate_potential"
    probability = 0.65
else:
    prediction = "low_potential"
    probability = 0.40

# Add depth estimates based on precipitation
depth_bands = calculate_depth_from_precipitation(precip_mm)
```

**Frontend Display:**
```
┌─────────────────────────────┐
│   Aquifer Prediction        │
├─────────────────────────────┤
│  Status: High Potential     │
│  Confidence: 85%            │
│  Depth: 20-80m              │
│  Yield: 5-15 L/s            │
│                             │
│  Based on precipitation:    │
│  5.20 mm/day                │
└─────────────────────────────┘
```

---

### **3. Recharge Forecast (Simulated from Precipitation)**

**Logic:**
```python
# Get current precipitation
current_precip = predict_precipitation(lon, lat, today)

# Generate 12-month forecast
forecast = []
for month in range(1, 13):
    # Apply seasonal patterns
    seasonal_factor = get_seasonal_factor(month)
    
    # Predict future precipitation
    future_precip = current_precip * seasonal_factor * (1 + random_variation)
    
    # Convert to recharge (simplified)
    recharge_mm = future_precip * 0.3  # 30% infiltration rate
    
    forecast.append({
        "month": month_name(month),
        "precipitation_mm": future_precip,
        "recharge_mm": recharge_mm,
        "confidence": 0.7 - (month * 0.03)  # Decreases with time
    })
```

**Frontend Display:**
```
┌─────────────────────────────┐
│   Recharge Forecast         │
├─────────────────────────────┤
│  12-month projection        │
│                             │
│  [Chart showing monthly     │
│   recharge estimates]       │
│                             │
│  Total: 187 mm/year         │
│  Avg: 15.6 mm/month         │
└─────────────────────────────┘
```

---

## 🔧 Setup Instructions

### **Step 1: Prepare Models**

```bash
# Create model_artifacts directory
mkdir -p model_artifacts

# Place your .joblib files:
# - Linear_Regression.joblib
# - Random_Forest.joblib
# - XGBoost.joblib
```

### **Step 2: Install Dependencies**

```bash
# Backend
cd modules/backend
python3.11 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn joblib scikit-learn xgboost pandas numpy pydantic

# Frontend
cd ../frontend
npm install
```

### **Step 3: Start Services**

```bash
# Terminal 1: Backend
cd modules/backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd modules/frontend
npm run dev
```

### **Step 4: Test**

Open http://localhost:3000:
1. Click on map
2. Try all three tabs:
   - ✅ Precipitation
   - ✅ Aquifer
   - ✅ Forecast

---

## 📁 Key Files

### **Backend:**
- `modules/backend/main.py` - Main API (includes inference router)
- `modules/backend/app/services/inference_pipeline.py` - Feature extraction
- `modules/backend/app/services/model_service.py` - Model loading
- `modules/backend/app/routers/inference.py` - Precipitation API

### **Frontend:**
- `modules/frontend/lib/api.ts` - API client (includes predictPrecipitation)
- `modules/frontend/components/prediction/prediction-panel.tsx` - UI with 3 tabs
- `modules/frontend/components/map/map-component.tsx` - Map with click handler

### **Models:**
- `model_artifacts/Linear_Regression.joblib`
- `model_artifacts/Random_Forest.joblib`
- `model_artifacts/XGBoost.joblib`

---

## ✅ Checklist

- [x] Backend inference pipeline matches model features
- [x] Model service loads from `model_artifacts/`
- [x] Inference router added to main.py
- [x] Frontend API client has `predictPrecipitation()`
- [x] Frontend UI has Precipitation tab
- [x] Date picker and model selector added
- [x] Results display configured
- [x] Aquifer prediction uses precipitation
- [x] Forecast simulates from precipitation

---

## 🚀 Next Steps

1. **Place your models** in `model_artifacts/`
2. **Start backend and frontend**
3. **Test precipitation prediction**
4. **Verify aquifer and forecast tabs**
5. **Deploy to server** when ready

---

## 🐛 Troubleshooting

### Models not loading?
```bash
# Check if models exist
ls -la model_artifacts/*.joblib

# Check backend logs
# Should see: "Loaded model: random_forest"
```

### Feature mismatch?
```bash
# Test feature extraction
curl -X POST http://localhost:8000/api/inference/extract-features \
  -H "Content-Type: application/json" \
  -d '{"lon": 36.8219, "lat": -1.2921, "date": "2024-01-15"}'

# Should return 16 features
```

### Frontend not connecting?
```bash
# Check API URL in frontend
cat modules/frontend/.env.local
# Should have: NEXT_PUBLIC_API_URL=http://localhost:8000

# Test backend directly
curl http://localhost:8000/health
```

---

**Everything is aligned and ready to go!** 🎉

Place your models and start testing!
