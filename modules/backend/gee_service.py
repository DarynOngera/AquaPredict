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
        self.region_bounds = [33.9, -4.7, 41.9, 5.5]  # Kenya bounds
        
    async def initialize(self):
        """Initialize GEE authentication."""
        try:
            # Try default authentication first (personal account)
            try:
                project = os.getenv('GEE_PROJECT', 'aquapredict-473718')
                ee.Initialize(project=project)
                logger.info(f"GEE initialized with default credentials (project: {project})")
                self.initialized = True
                return
            except Exception as e:
                logger.warning(f"Default auth with project failed: {e}")
                
                # Try without project
                try:
                    ee.Initialize()
                    logger.info("GEE initialized with default credentials (no project)")
                    self.initialized = True
                    return
                except Exception as e2:
                    logger.warning(f"Default auth without project failed: {e2}")
            
            # Fall back to service account if default fails
            service_account = os.getenv('GEE_SERVICE_ACCOUNT')
            key_file = os.getenv('GEE_PRIVATE_KEY_FILE', './credentials/key.json')
            
            if service_account and os.path.exists(key_file):
                credentials = ee.ServiceAccountCredentials(service_account, key_file)
                ee.Initialize(credentials)
                logger.info("GEE initialized with service account")
                self.initialized = True
                return
            
            # All methods failed
            raise Exception("All GEE authentication methods failed")
            
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
                .filterDate(start_date, end_date) \
                .select(config['band'])
            
            # Special handling for Sentinel-2 NDVI
            if config.get('compute_ndvi'):
                def calculate_ndvi(img):
                    ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                    return ndvi
                
                collection = ee.ImageCollection(config['collection']) \
                    .filterDate(start_date, end_date) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
                    .map(calculate_ndvi)
            
            # Check if collection has images
            count = collection.size().getInfo()
            if count == 0:
                raise ValueError(f"No images found for {dataset_id} in the specified date range")
            
            # Get most recent image (avoids band naming issues with mean/median)
            image = collection.sort('system:time_start', False).first()
        else:
            # Static dataset
            if config['collection'] == 'ESA/WorldCover/v100':
                image = ee.ImageCollection(config['collection']).first().select(config['band'])
            else:
                image = ee.Image(config['collection']).select(config['band'])
        
        # Verify image is not null
        if image is None:
            raise ValueError(f"Failed to create image for {dataset_id}")
        
        # Get map ID for tiles
        map_id = image.getMapId(config['vis_params'])
        
        return map_id['tile_fetcher'].url_format
    
    async def get_dataset_stats(
        self,
        dataset_id: str,
        location: Dict[str, float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a dataset at a location.
        
        Args:
            dataset_id: Dataset identifier
            location: Dict with 'lat' and 'lon'
            start_date: Start date for temporal datasets
            end_date: End date for temporal datasets
            
        Returns:
            Statistics dictionary with min, max, mean, time series, etc.
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        point = ee.Geometry.Point([location['lon'], location['lat']])
        
        # Dataset-specific statistics
        if dataset_id == 'chirps':
            return await self._get_chirps_stats(point, start_date, end_date)
        elif dataset_id == 'era5':
            return await self._get_era5_stats(point, start_date, end_date)
        elif dataset_id == 'srtm':
            return await self._get_srtm_stats(point)
        elif dataset_id == 'sentinel2':
            return await self._get_sentinel2_stats(point, start_date, end_date)
        elif dataset_id == 'worldcover':
            return await self._get_worldcover_stats(point)
        else:
            raise ValueError(f"Unknown dataset: {dataset_id}")
    
    async def _get_chirps_stats(self, point, start_date, end_date):
        """Get CHIRPS precipitation statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=90)  # Last 90 days
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate(start_date, end_date) \
            .filterBounds(point) \
            .select('precipitation')
        
        # Check if collection has images
        count = collection.size().getInfo()
        if count == 0:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'std': 0,
                'unit': 'mm/day',
                'time_series': {'dates': [], 'values': []},
                'total_images': 0,
                'date_range': [start_date, end_date],
                'error': 'No images found for date range'
            }
        
        # Calculate statistics at the point
        def get_stats(img):
            return img.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=5000
            )
        
        # Get all values
        all_values = collection.map(get_stats).aggregate_array('precipitation').getInfo()
        all_values = [v for v in all_values if v is not None]
        
        if len(all_values) == 0:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'std': 0,
                'unit': 'mm/day',
                'time_series': {'dates': [], 'values': []},
                'total_images': count,
                'date_range': [start_date, end_date],
                'error': 'No valid data at location'
            }
        
        import numpy as np
        stats = {
            'precipitation_min': float(np.min(all_values)),
            'precipitation_max': float(np.max(all_values)),
            'precipitation_mean': float(np.mean(all_values)),
            'precipitation_stdDev': float(np.std(all_values))
        }
        
        # Get time series (limit to last 30 days for performance)
        recent_collection = collection.limit(30, 'system:time_start', False)
        
        def extract_value(image):
            value = image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=5000
            ).get('precipitation')
            return ee.Feature(None, {
                'date': image.date().format('YYYY-MM-dd'),
                'value': value
            })
        
        time_series = recent_collection.map(extract_value).getInfo()
        
        # Extract time series data
        dates = []
        values = []
        for feature in time_series['features']:
            props = feature['properties']
            if props.get('value') is not None:
                dates.append(props['date'])
                values.append(float(props['value']))
        
        return {
            'min': stats.get('precipitation_min', 0),
            'max': stats.get('precipitation_max', 0),
            'mean': stats.get('precipitation_mean', 0),
            'std': stats.get('precipitation_stdDev', 0),
            'unit': 'mm/day',
            'time_series': {
                'dates': dates,
                'values': values
            },
            'total_images': count,
            'date_range': [start_date, end_date]
        }
    
    async def _get_era5_stats(self, point, start_date, end_date):
        """Get ERA5 temperature statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=365)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        collection = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
            .filterDate(start_date, end_date) \
            .filterBounds(point) \
            .select('mean_2m_air_temperature')
        
        count = collection.size().getInfo()
        if count == 0:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'unit': '°C',
                'total_images': 0,
                'date_range': [start_date, end_date],
                'error': 'No images found'
            }
        
        # Get temperature values at point
        def get_temp(img):
            return img.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=27830
            )
        
        temp_values = collection.map(get_temp).aggregate_array('mean_2m_air_temperature').getInfo()
        temp_values = [v for v in temp_values if v is not None]
        
        if len(temp_values) == 0:
            return {
                'min': 0,
                'max': 0,
                'mean': 0,
                'unit': '°C',
                'total_images': count,
                'date_range': [start_date, end_date],
                'error': 'No valid data at location'
            }
        
        import numpy as np
        # Convert Kelvin to Celsius
        return {
            'min': float(np.min(temp_values)) - 273.15,
            'max': float(np.max(temp_values)) - 273.15,
            'mean': float(np.mean(temp_values)) - 273.15,
            'unit': '°C',
            'total_images': count,
            'date_range': [start_date, end_date]
        }
    
    async def _get_srtm_stats(self, point):
        """Get SRTM elevation statistics."""
        dem = ee.Image('USGS/SRTMGL1_003')
        
        # Get elevation at point
        elevation = dem.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=30
        ).getInfo()
        
        # Get slope
        slope = ee.Terrain.slope(dem).reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=30
        ).getInfo()
        
        # Get regional statistics (10km buffer)
        buffer = point.buffer(10000)
        regional_stats = dem.reduceRegion(
            reducer=ee.Reducer.minMax().combine(
                ee.Reducer.mean(), sharedInputs=True
            ),
            geometry=buffer,
            scale=90
        ).getInfo()
        
        return {
            'elevation': elevation.get('elevation', 0),
            'slope': slope.get('slope', 0),
            'regional_min': regional_stats.get('elevation_min', 0),
            'regional_max': regional_stats.get('elevation_max', 0),
            'regional_mean': regional_stats.get('elevation_mean', 0),
            'unit': 'meters',
            'resolution': '30m'
        }
    
    async def _get_sentinel2_stats(self, point, start_date, end_date):
        """Get Sentinel-2 NDVI statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=180)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        def calculate_ndvi(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi)
        
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(start_date, end_date) \
            .filterBounds(point) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .map(calculate_ndvi) \
            .select('NDVI')
        
        count = collection.size().getInfo()
        if count == 0:
            return {
                'min': -1,
                'max': 1,
                'mean': 0,
                'std': 0,
                'unit': 'index (-1 to 1)',
                'total_images': 0,
                'date_range': [start_date, end_date],
                'interpretation': 'No data available',
                'error': 'No cloud-free images found'
            }
        
        # Get NDVI values at point
        def get_ndvi(img):
            return img.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=10
            )
        
        ndvi_values = collection.map(get_ndvi).aggregate_array('NDVI').getInfo()
        ndvi_values = [v for v in ndvi_values if v is not None]
        
        if len(ndvi_values) == 0:
            return {
                'min': -1,
                'max': 1,
                'mean': 0,
                'std': 0,
                'unit': 'index (-1 to 1)',
                'total_images': count,
                'date_range': [start_date, end_date],
                'interpretation': 'No valid data at location',
                'error': 'No valid data at location'
            }
        
        import numpy as np
        mean_ndvi = float(np.mean(ndvi_values))
        
        return {
            'min': float(np.min(ndvi_values)),
            'max': float(np.max(ndvi_values)),
            'mean': mean_ndvi,
            'std': float(np.std(ndvi_values)),
            'unit': 'index (-1 to 1)',
            'total_images': count,
            'date_range': [start_date, end_date],
            'interpretation': self._interpret_ndvi(mean_ndvi)
        }
    
    async def _get_worldcover_stats(self, point):
        """Get ESA WorldCover land cover statistics."""
        worldcover = ee.ImageCollection('ESA/WorldCover/v100').first()
        
        # Get land cover class at point
        lc_class = worldcover.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=10
        ).getInfo()
        
        # Land cover classes
        lc_names = {
            10: 'Tree cover',
            20: 'Shrubland',
            30: 'Grassland',
            40: 'Cropland',
            50: 'Built-up',
            60: 'Bare / sparse vegetation',
            70: 'Snow and ice',
            80: 'Permanent water bodies',
            90: 'Herbaceous wetland',
            95: 'Mangroves',
            100: 'Moss and lichen'
        }
        
        class_value = int(lc_class.get('Map', 0))
        
        return {
            'class_value': class_value,
            'class_name': lc_names.get(class_value, 'Unknown'),
            'unit': 'class',
            'resolution': '10m',
            'year': '2020'
        }
    
    def _interpret_ndvi(self, ndvi_value):
        """Interpret NDVI value."""
        if ndvi_value < 0:
            return 'Water or snow'
        elif ndvi_value < 0.2:
            return 'Bare soil or rock'
        elif ndvi_value < 0.4:
            return 'Sparse vegetation'
        elif ndvi_value < 0.6:
            return 'Moderate vegetation'
        else:
            return 'Dense vegetation'
    
    async def get_regional_stats(
        self,
        dataset_id: str,
        bbox: List[float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get regional statistics over a bounding box and date range.
        
        Args:
            dataset_id: Dataset identifier
            bbox: [west, south, east, north]
            start_date: Start date
            end_date: End date
            
        Returns:
            Regional statistics with time series
        """
        if not self.initialized:
            raise RuntimeError("GEE not initialized")
        
        region = ee.Geometry.Rectangle(bbox)
        
        # Dataset-specific regional stats
        if dataset_id == 'chirps':
            return await self._get_chirps_regional(region, start_date, end_date)
        elif dataset_id == 'era5':
            return await self._get_era5_regional(region, start_date, end_date)
        elif dataset_id == 'srtm':
            return await self._get_srtm_regional(region)
        elif dataset_id == 'sentinel2':
            return await self._get_sentinel2_regional(region, start_date, end_date)
        elif dataset_id == 'worldcover':
            return await self._get_worldcover_regional(region)
        else:
            raise ValueError(f"Unknown dataset: {dataset_id}")
    
    async def _get_chirps_regional(self, region, start_date, end_date):
        """Get regional CHIRPS statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=30)  # Reduced to 30 days for speed
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate(start_date, end_date) \
            .filterBounds(region) \
            .select('precipitation')
        
        count = collection.size().getInfo()
        if count == 0:
            return {'error': 'No data', 'date_range': [start_date, end_date]}
        
        # Get overall statistics using server-side reduction (much faster)
        mean_image = collection.mean()
        stats = mean_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=5000,
            maxPixels=1e9
        ).getInfo()
        
        # Get min/max from collection
        min_max = collection.reduce(ee.Reducer.minMax()).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=5000,
            maxPixels=1e9
        ).getInfo()
        
        # Get simplified time series (weekly averages for speed)
        # Sample only 10 images evenly distributed
        sample_size = min(10, count)
        step = max(1, count // sample_size)
        
        dates = []
        values = []
        
        for i in range(sample_size):
            idx = i * step
            img = ee.Image(collection.toList(1, idx).get(0))
            date = img.date().format('YYYY-MM-dd').getInfo()
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=5000,
                maxPixels=1e9
            ).getInfo()
            
            if val.get('precipitation') is not None:
                dates.append(date)
                values.append(float(val['precipitation']))
        
        return {
            'min': min_max.get('precipitation_min', 0),
            'max': min_max.get('precipitation_max', 0),
            'mean': stats.get('precipitation', 0),
            'std': 0,  # Skip std calculation for speed
            'unit': 'mm/day',
            'time_series': {'dates': dates, 'values': values},
            'total_images': count,
            'date_range': [start_date, end_date],
            'region_area_km2': region.area().divide(1e6).getInfo()
        }
    
    async def _get_era5_regional(self, region, start_date, end_date):
        """Get regional ERA5 statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=180)  # Reduced to 6 months for speed
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        collection = ee.ImageCollection('ECMWF/ERA5/MONTHLY') \
            .filterDate(start_date, end_date) \
            .filterBounds(region) \
            .select('mean_2m_air_temperature')
        
        count = collection.size().getInfo()
        if count == 0:
            return {'error': 'No data', 'date_range': [start_date, end_date]}
        
        # Get overall statistics using server-side operations
        mean_temp = collection.mean().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=27830,
            maxPixels=1e9
        ).getInfo()
        
        min_max = collection.reduce(ee.Reducer.minMax()).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=27830,
            maxPixels=1e9
        ).getInfo()
        
        # Get simplified time series (sample up to 12 months)
        sample_size = min(12, count)
        dates = []
        values = []
        
        img_list = collection.toList(sample_size, 0)
        for i in range(sample_size):
            img = ee.Image(img_list.get(i))
            date = img.date().format('YYYY-MM').getInfo()
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=27830,
                maxPixels=1e9
            ).getInfo()
            
            if val.get('mean_2m_air_temperature') is not None:
                dates.append(date)
                values.append(float(val['mean_2m_air_temperature']) - 273.15)
        
        return {
            'min': min_max.get('mean_2m_air_temperature_min', 273) - 273.15,
            'max': min_max.get('mean_2m_air_temperature_max', 273) - 273.15,
            'mean': mean_temp.get('mean_2m_air_temperature', 273) - 273.15,
            'unit': '°C',
            'time_series': {'dates': dates, 'values': values},
            'total_images': count,
            'date_range': [start_date, end_date],
            'region_area_km2': region.area().divide(1e6).getInfo()
        }
    
    async def _get_srtm_regional(self, region):
        """Get regional SRTM statistics."""
        dem = ee.Image('USGS/SRTMGL1_003')
        
        stats = dem.reduceRegion(
            reducer=ee.Reducer.minMax().combine(
                ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
                sharedInputs=True
            ),
            geometry=region,
            scale=90,
            maxPixels=1e9
        ).getInfo()
        
        return {
            'min': stats.get('elevation_min', 0),
            'max': stats.get('elevation_max', 0),
            'mean': stats.get('elevation_mean', 0),
            'std': stats.get('elevation_stdDev', 0),
            'unit': 'meters',
            'region_area_km2': region.area().divide(1e6).getInfo()
        }
    
    async def _get_sentinel2_regional(self, region, start_date, end_date):
        """Get regional Sentinel-2 NDVI statistics."""
        if not start_date or not end_date:
            end = datetime.now()
            start = end - timedelta(days=90)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')
        
        def calculate_ndvi(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi)
        
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterDate(start_date, end_date) \
            .filterBounds(region) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
            .map(calculate_ndvi) \
            .select('NDVI')
        
        count = collection.size().getInfo()
        if count == 0:
            return {'error': 'No cloud-free images', 'date_range': [start_date, end_date]}
        
        # Get mean NDVI
        mean_ndvi = collection.mean()
        stats = mean_ndvi.reduceRegion(
            reducer=ee.Reducer.minMax().combine(
                ee.Reducer.mean(), sharedInputs=True
            ),
            geometry=region,
            scale=100,
            maxPixels=1e9
        ).getInfo()
        
        mean_val = stats.get('NDVI_mean', 0)
        
        return {
            'min': stats.get('NDVI_min', -1),
            'max': stats.get('NDVI_max', 1),
            'mean': mean_val,
            'unit': 'index (-1 to 1)',
            'interpretation': self._interpret_ndvi(mean_val),
            'total_images': count,
            'date_range': [start_date, end_date],
            'region_area_km2': region.area().divide(1e6).getInfo()
        }
    
    async def _get_worldcover_regional(self, region):
        """Get regional WorldCover statistics."""
        worldcover = ee.ImageCollection('ESA/WorldCover/v100').first()
        
        # Get histogram of land cover classes
        histogram = worldcover.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=region,
            scale=100,
            maxPixels=1e9
        ).getInfo()
        
        lc_names = {
            '10': 'Tree cover', '20': 'Shrubland', '30': 'Grassland',
            '40': 'Cropland', '50': 'Built-up', '60': 'Bare/sparse vegetation',
            '70': 'Snow and ice', '80': 'Water bodies', '90': 'Herbaceous wetland',
            '95': 'Mangroves', '100': 'Moss and lichen'
        }
        
        class_distribution = {}
        if 'Map' in histogram:
            for class_val, count in histogram['Map'].items():
                class_name = lc_names.get(class_val, f'Class {class_val}')
                class_distribution[class_name] = int(count)
        
        # Get dominant class
        dominant_class = max(class_distribution, key=class_distribution.get) if class_distribution else 'Unknown'
        
        return {
            'dominant_class': dominant_class,
            'class_distribution': class_distribution,
            'unit': 'pixel count',
            'year': '2020',
            'region_area_km2': region.area().divide(1e6).getInfo()
        }
