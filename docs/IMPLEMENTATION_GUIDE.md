# AquaPredict Implementation Guide

## Overview

This guide provides detailed instructions for implementing and deploying the AquaPredict platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│              Leaflet Maps + Recharts + shadcn/ui                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Prediction Service (FastAPI)                   │
│                    REST API + Model Serving                      │
└────────┬──────────────────────────────────────────┬─────────────┘
         │                                           │
         ▼                                           ▼
┌────────────────────┐                    ┌──────────────────────┐
│  Oracle ADB        │                    │  OCI Model Deploy    │
│  (Spatial Data)    │                    │  (ML Inference)      │
└────────────────────┘                    └──────────────────────┘
         ▲
         │
┌────────┴───────────────────────────────────────────────────────┐
│                    Airflow Orchestration                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Ingestion│→ │Preprocess│→ │ Features │→ │ Modeling │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Module Implementation Status

### ✅ Completed Modules

1. **Data Ingestion** - GEE integration, CHIRPS/ERA5/SRTM fetching
2. **Preprocessing** - Data cleaning, normalization, resampling
3. **Feature Engineering** - TWI, SPI, SPEI, terrain features
4. **Modeling** - RF/XGBoost classifiers, LSTM forecaster
5. **Prediction Service** - FastAPI REST API with model serving

### 🔨 To Be Implemented

6. **Frontend** - React dashboard (scaffold provided below)
7. **Reporting** - ISO PDF generation (scaffold provided below)
8. **Orchestration** - Airflow DAGs (scaffold provided below)
9. **OCI Deployment** - Infrastructure as Code (scaffold provided below)

## Data Pipeline

### 1. Data Ingestion (GEE)

```bash
cd modules/data-ingestion
python main.py --dataset all --start-date 2020-01-01 --end-date 2023-12-31
```

**Datasets fetched:**
- CHIRPS precipitation (monthly aggregation)
- ERA5 temperature (mean, min, max)
- SRTM elevation (with slope, aspect)
- ESA WorldCover land cover

### 2. Preprocessing

```bash
cd modules/preprocessing
python main.py --input-dir data/raw --output-dir data/processed \
  --clean --fill-missing --remove-outliers --normalize
```

### 3. Feature Engineering

```python
from feature_engineering import FeatureEngineer

engineer = FeatureEngineer()

# Compute TWI
twi = engineer.compute_twi(dem, flow_accumulation)

# Compute SPI (1, 3, 6, 12 month scales)
spi_3 = engineer.compute_spi(precipitation, timescale=3)

# Compute SPEI
spei_6 = engineer.compute_spei(precipitation, temperature, timescale=6)

# Generate all features
features = engineer.generate_all_features({
    'dem': dem,
    'precipitation': precip,
    'temperature': temp,
    'flow_accumulation': flow_acc
})
```

### 4. Model Training

```python
from modeling import AquiferClassifier, RechargeForecaster

# Train aquifer classifier
classifier = AquiferClassifier(model_type='xgboost')
metrics = classifier.train(X_train, y_train, feature_names=feature_names)
classifier.save('models/trained/aquifer_classifier.joblib')

# Train recharge forecaster
forecaster = RechargeForecaster(model_type='lstm')
forecaster.train(time_series_data)
forecaster.save('models/trained/recharge_forecaster.joblib')
```

### 5. Prediction Service

```bash
cd modules/prediction-service
uvicorn main:app --host 0.0.0.0 --port 8000
```

**API endpoints:**
- `POST /api/v1/predict/aquifer` - Aquifer prediction
- `POST /api/v1/predict/recharge` - Recharge forecast
- `GET /docs` - Swagger documentation

## Feature Formulas

### Topographic Wetness Index (TWI)

```
TWI = ln((flow_accumulation + 1) / (tan(slope_rad) + 0.001))
```

### Standardized Precipitation Index (SPI)

1. Aggregate precipitation over timescale (1, 3, 6, 12 months)
2. Fit gamma distribution to aggregated data
3. Transform to standard normal distribution

### Standardized Precipitation-Evapotranspiration Index (SPEI)

1. Compute water balance: WB = P - PET
2. Aggregate over timescale
3. Fit normal distribution and transform to standard normal

### Potential Evapotranspiration (Hargreaves)

```
PET = 0.0023 * (T_mean + 17.8) * sqrt(T_max - T_min) * Ra
```

## Model Specifications

### Aquifer Classifier (XGBoost)

- **Task**: Binary/multi-class classification
- **Features**: Static (TWI, TPI, slope, soil) + Temporal (SPI, SPEI, precip stats)
- **Validation**: 5-fold spatial cross-validation
- **Metrics**: ROC-AUC, Precision, Recall, F1-Score

### Recharge Forecaster (LSTM)

- **Task**: Time-series forecasting
- **Architecture**: 2-layer LSTM (64 hidden units)
- **Input**: 12-month lookback window
- **Output**: 1-12 month forecast horizon
- **Metrics**: RMSE, MAE, R², MAPE

## Kenya Pilot Configuration

```python
# Region bounds
KENYA_BOUNDS = {
    'west': 33.9,
    'south': -4.7,
    'east': 41.9,
    'north': 5.5
}

# Grid resolution
GRID_RESOLUTION_KM = 1  # 1km grid

# Time period
START_DATE = '2020-01-01'
END_DATE = '2023-12-31'
```

## Next Steps

1. **Implement Frontend** (see `docs/FRONTEND_GUIDE.md`)
2. **Implement Reporting** (see `docs/REPORTING_GUIDE.md`)
3. **Setup Orchestration** (see `docs/ORCHESTRATION_GUIDE.md`)
4. **Deploy to OCI** (see `infrastructure/README.md`)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run module-specific tests
pytest modules/data-ingestion/tests/ -v
pytest modules/modeling/tests/ -v

# Run integration tests
pytest tests/integration/ -v
```

## Troubleshooting

### GEE Authentication Issues

```bash
earthengine authenticate
# Follow browser prompts
```

### Memory Issues with Large Rasters

- Use chunked processing with xarray/dask
- Reduce spatial resolution temporarily
- Process by tiles/regions

### Model Training Performance

- Use GPU for LSTM training: `accelerator='gpu'`
- Enable Optuna hyperparameter tuning
- Use spatial CV for better generalization

## References

- [Google Earth Engine](https://earthengine.google.com/)
- [CHIRPS Dataset](https://www.chc.ucsb.edu/data/chirps)
- [Oracle Spatial](https://www.oracle.com/database/spatial/)
- [ISO 14046](https://www.iso.org/standard/43263.html)
