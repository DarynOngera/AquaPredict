"""
Google Earth Engine Service
Handles all GEE data fetching and processing.
"""

import ee
import os
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


class GEEService:
    """Service for fetching data from Google Earth Engine."""
    
    def __init__(self):
        self.initialized = False
        self.region_bounds = [33.9, -4.7, 41.9, 5.5]  # Kenya bounds
        
    async def initialize(self):
        """Initialize GEE authentication."""
        try:
            # Try service account authentication first
            service_account = os.getenv('GEE_SERVICE_ACCOUNT')
            key_file = os.getenv('GEE_PRIVATE_KEY_FILE', './credentials/gee_key.json')
            
            if service_account and os.path.exists(key_file):
                credentials = ee.ServiceAccountCredentials(service_account, key_file)
                ee.Initialize(credentials)
                logger.info("GEE initialized with service account")
            else:
                # Fall back to default authentication
                ee.Initialize()
                logger.info("GEE initialized with default credentials")
            
            self.initialized = True
            
        except Exception as e:
            logger.error(f"GEE initialization failed: {e}")
            self.initialized = False
            raise
    
    def is_available(self) -> bool:
        """Check if GEE is available."""
        return self.initialized
    
    async def get_features(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Get all features for a location from GEE.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary of features
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        point = ee.Geometry.Point([lon, lat])
        
        # Fetch all features in parallel
        features = {}
        
        # 1. Elevation and terrain
        dem = ee.Image('USGS/SRTMGL1_003')
        elevation = dem.select('elevation').reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=30
        ).getInfo()
        
        slope = ee.Terrain.slope(dem).reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=30
        ).getInfo()
        
        features['elevation'] = elevation.get('elevation', 1500)
        features['slope'] = slope.get('slope', 5.0)
        
        # 2. Precipitation (CHIRPS - last year)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterBounds(point)
        
        precip = chirps.sum().reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=5000
        ).getInfo()
        
        features['precip_mean'] = precip.get('precipitation', 800)
        
        # 3. Temperature (ERA5 - last year mean)
        era5 = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterBounds(point) \
            .select('mean_2m_air_temperature')
        
        temp = era5.mean().reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=27830
        ).getInfo()
        
        # Convert from Kelvin to Celsius
        temp_k = temp.get('mean_2m_air_temperature', 293)
        features['temp_mean'] = temp_k - 273.15 if temp_k > 200 else 20.0
        
        # 4. NDVI (Sentinel-2 - last 6 months)
        s2_start = end_date - timedelta(days=180)
        s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(s2_start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterBounds(point) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        
        def calculate_ndvi(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi)
        
        s2_ndvi = s2.map(calculate_ndvi).select('NDVI').mean()
        
        ndvi = s2_ndvi.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=10
        ).getInfo()
        
        features['ndvi'] = ndvi.get('NDVI', 0.5)
        
        # 5. Calculate TWI (Topographic Wetness Index)
        # TWI = ln(a / tan(slope))
        # Simplified calculation
        slope_rad = features['slope'] * 3.14159 / 180
        tan_slope = max(0.001, slope_rad)  # Avoid division by zero
        catchment_area = 100  # Simplified
        features['twi'] = float(np.log(catchment_area / tan_slope))
        
        # 6. Land cover
        landcover = ee.ImageCollection('ESA/WorldCover/v100').first()
        lc = landcover.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=10
        ).getInfo()
        
        features['landcover'] = lc.get('Map', 50)
        
        logger.info(f"Fetched features for ({lat}, {lon}): {features}")
        return features
    
    async def get_climate_timeseries(
        self,
        lat: float,
        lon: float,
        months_back: int = 24
    ) -> Dict[str, List[float]]:
        """
        Get climate time series data for forecasting.
        
        Args:
            lat: Latitude
            lon: Longitude
            months_back: Number of months of historical data
            
        Returns:
            Dictionary with precipitation and temperature time series
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        point = ee.Geometry.Point([lon, lat])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        # Get monthly precipitation
        chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterBounds(point)
        
        # Aggregate by month
        months = ee.List.sequence(0, months_back - 1)
        
        def monthly_precip(month_offset):
            month_start = end_date - timedelta(days=(months_back - month_offset) * 30)
            month_end = month_start + timedelta(days=30)
            
            monthly = chirps.filterDate(
                month_start.strftime('%Y-%m-%d'),
                month_end.strftime('%Y-%m-%d')
            ).sum()
            
            return monthly.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=5000
            ).get('precipitation')
        
        precip_list = months.map(monthly_precip).getInfo()
        
        # Get monthly temperature
        era5 = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
            .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) \
            .filterBounds(point) \
            .select('mean_2m_air_temperature')
        
        def monthly_temp(month_offset):
            month_start = end_date - timedelta(days=(months_back - month_offset) * 30)
            month_end = month_start + timedelta(days=30)
            
            monthly = era5.filterDate(
                month_start.strftime('%Y-%m-%d'),
                month_end.strftime('%Y-%m-%d')
            ).mean()
            
            temp_k = monthly.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=27830
            ).get('mean_2m_air_temperature')
            
            # Convert to Celsius
            return ee.Number(temp_k).subtract(273.15)
        
        temp_list = months.map(monthly_temp).getInfo()
        
        return {
            'precipitation': [p if p else 50 for p in precip_list],
            'temperature': [t if t else 20 for t in temp_list],
            'months': months_back
        }
    
    async def get_regional_data(
        self,
        bbox: List[float],
        scale: int = 1000
    ) -> Dict[str, Any]:
        """
        Get regional data for a bounding box.
        
        Args:
            bbox: [west, south, east, north]
            scale: Resolution in meters
            
        Returns:
            Regional data summary
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        region = ee.Geometry.Rectangle(bbox)
        
        # Get elevation statistics
        dem = ee.Image('USGS/SRTMGL1_003')
        elev_stats = dem.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.minMax(),
                sharedInputs=True
            ),
            geometry=region,
            scale=scale,
            maxPixels=1e9
        ).getInfo()
        
        return {
            'elevation': {
                'mean': elev_stats.get('elevation_mean', 1500),
                'min': elev_stats.get('elevation_min', 0),
                'max': elev_stats.get('elevation_max', 3000)
            },
            'bbox': bbox
        }
    
    async def get_tile_url(
        self,
        dataset_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Get GEE tile URL for dataset visualization.
        
        Args:
            dataset_id: Dataset identifier (chirps, era5, srtm, etc.)
            start_date: Start date for temporal datasets
            end_date: End date for temporal datasets
            
        Returns:
            Tile URL template for map display
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        # Dataset configurations
        dataset_configs = {
            'chirps': {
                'collection': 'UCSB-CHG/CHIRPS/DAILY',
                'band': 'precipitation',
                'vis_params': {
                    'min': 1,
                    'max': 17,
                    'palette': ['001137', '0aab1e', 'e7eb05', 'ff4a2d', 'e90000']
                },
                'temporal': True
            },
            'era5': {
                'collection': 'ECMWF/ERA5/MONTHLY',
                'band': 'mean_2m_air_temperature',
                'vis_params': {
                    'min': 250,
                    'max': 320,
                    'palette': ['000080', '0000ff', '00ffff', 'ffff00', 'ff0000', '800000']
                },
                'temporal': True
            },
            'srtm': {
                'collection': 'USGS/SRTMGL1_003',
                'band': 'elevation',
                'vis_params': {
                    'min': 0,
                    'max': 3000,
                    'palette': ['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']
                },
                'temporal': False
            },
            'sentinel2': {
                'collection': 'COPERNICUS/S2_SR',
                'band': 'NDVI',
                'vis_params': {
                    'min': -1,
                    'max': 1,
                    'palette': ['brown', 'yellow', 'green', 'darkgreen']
                },
                'temporal': True,
                'compute_ndvi': True
            },
            'worldcover': {
                'collection': 'ESA/WorldCover/v100',
                'band': 'Map',
                'vis_params': {
                    'min': 10,
                    'max': 100,
                    'palette': ['006400', 'ffbb22', 'ffff4c', 'f096ff', 'fa0000', 
                               'b4b4b4', 'f0f0f0', '0064c8', '0096a0', '00cf75', 'fae6a0']
                },
                'temporal': False
            }
        }
        
        if dataset_id not in dataset_configs:
            raise ValueError(f"Unknown dataset: {dataset_id}")
        
        config = dataset_configs[dataset_id]
        
        # Get image or image collection
        if config['temporal']:
            if not start_date or not end_date:
                # Use default recent dates
                from datetime import datetime, timedelta
                end = datetime.now()
                start = end - timedelta(days=30)
                start_date = start.strftime('%Y-%m-%d')
                end_date = end.strftime('%Y-%m-%d')
            
            collection = ee.ImageCollection(config['collection']) \
                .filterDate(start_date, end_date)
            
            # Special handling for Sentinel-2 NDVI
            if config.get('compute_ndvi'):
                def calculate_ndvi(image):
                    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                    return image.addBands(ndvi)
                
                collection = collection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .map(calculate_ndvi)
            
            # Get mean/median composite
            image = collection.mean() if dataset_id == 'chirps' else collection.median()
        else:
            # Static dataset
            if config['collection'] == 'ESA/WorldCover/v100':
                image = ee.ImageCollection(config['collection']).first()
            else:
                image = ee.Image(config['collection'])
        
        # Select band
        image = image.select(config['band'])
        
        # Get map ID for tiles
        map_id = image.getMapId(config['vis_params'])
        
        return map_id['tile_fetcher'].url_format
