# Feature Engineering Module

This module computes geospatial and temporal features for aquifer prediction and groundwater analysis.

## Features

### Static Features
- **TWI (Topographic Wetness Index)**: `TWI = ln((flow_accumulation + 1) / (tan(slope_rad) + 0.001))`
- **TPI (Topographic Position Index)**: Elevation relative to surroundings
- **Slope and Aspect**: Terrain derivatives
- **Curvature**: Surface curvature metrics
- **Distance to Water**: Proximity to water bodies
- **Soil Properties**: Texture, porosity, hydraulic conductivity

### Temporal Features
- **SPI (Standardized Precipitation Index)**: Precipitation anomalies
- **SPEI (Standardized Precipitation-Evapotranspiration Index)**: Water balance anomalies
- **Precipitation Statistics**: Mean, variance, trends
- **Temperature Statistics**: Mean, min, max, trends
- **NDVI**: Vegetation index from satellite imagery
- **Evapotranspiration**: Estimated from temperature and radiation

### Derived Features
- **Water Balance**: Precipitation - Evapotranspiration
- **Recharge Potential**: Based on soil, slope, land cover
- **Seasonal Patterns**: Monthly/seasonal aggregations
- **Lag Features**: Temporal lags for time-series modeling

## Usage

```python
from feature_engineering import FeatureEngineer

# Initialize
engineer = FeatureEngineer()

# Compute TWI
twi = engineer.compute_twi(dem, flow_accumulation)

# Compute SPI
spi = engineer.compute_spi(precipitation, timescale=3)

# Compute SPEI
spei = engineer.compute_spei(precipitation, temperature, timescale=3)

# Generate all features
features = engineer.generate_all_features(data_dict)
```

## Testing

```bash
pytest tests/
```
