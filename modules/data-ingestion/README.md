# Data Ingestion Module

This module handles data fetching and extraction from Google Earth Engine (GEE) and other geospatial data sources.

## Features

- Fetch precipitation data (CHIRPS)
- Fetch temperature data (ERA5)
- Fetch elevation data (SRTM)
- Fetch land cover data (ESA WorldCover)
- Fetch soil data (SoilGrids)
- Extract data for specified regions (Kenya pilot: 1km grid)
- Cache downloaded data locally
- Export to GeoTIFF and NetCDF formats

## Data Sources (GEE IDs)

- **CHIRPS Precipitation**: `UCSB-CHG/CHIRPS/DAILY`
- **ERA5 Temperature**: `ECMWF/ERA5/DAILY`
- **SRTM Elevation**: `USGS/SRTMGL1_003`
- **ESA WorldCover**: `ESA/WorldCover/v100`
- **SoilGrids**: Custom integration

## Usage

```python
from data_ingestion import GEEDataFetcher

# Initialize fetcher
fetcher = GEEDataFetcher(
    region_bounds=(33.9, -4.7, 41.9, 5.5),  # Kenya
    resolution_km=1
)

# Fetch precipitation data
precip_data = fetcher.fetch_precipitation(
    start_date='2020-01-01',
    end_date='2023-12-31',
    dataset='CHIRPS'
)

# Export to file
fetcher.export_to_geotiff(precip_data, 'data/raw/kenya_precip.tif')
```

## API Endpoints

- `POST /ingest/precipitation` - Fetch precipitation data
- `POST /ingest/temperature` - Fetch temperature data
- `POST /ingest/elevation` - Fetch elevation data
- `POST /ingest/landcover` - Fetch land cover data
- `POST /ingest/soil` - Fetch soil data
- `GET /ingest/status/{job_id}` - Check ingestion job status

## Testing

```bash
pytest tests/
```
