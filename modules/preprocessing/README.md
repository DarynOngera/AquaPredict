# Preprocessing Module

This module handles data cleaning, normalization, and preparation for feature engineering and modeling.

## Features

- Data quality checks and validation
- Missing value imputation
- Outlier detection and handling
- Data normalization and standardization
- Temporal alignment of multi-source datasets
- Spatial resampling and reprojection
- Data masking (e.g., water bodies, urban areas)

## Usage

```python
from preprocessing import DataPreprocessor

# Initialize preprocessor
preprocessor = DataPreprocessor()

# Load and clean data
clean_data = preprocessor.clean_raster('data/raw/kenya_precip.tif')

# Normalize data
normalized = preprocessor.normalize(clean_data, method='minmax')

# Handle missing values
filled = preprocessor.fill_missing(clean_data, method='interpolate')
```

## Processing Steps

1. **Quality Control**: Check for corrupted files, invalid values
2. **Temporal Alignment**: Align time series from different sources
3. **Spatial Alignment**: Resample to common grid
4. **Missing Data**: Interpolate or fill missing values
5. **Outlier Removal**: Detect and handle outliers
6. **Normalization**: Scale features appropriately

## Testing

```bash
pytest tests/
```
