"""Google Earth Engine data fetcher for AquaPredict."""

import ee
import os
import logging
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import json

from .config import IngestionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GEEDataFetcher:
    """Fetches geospatial data from Google Earth Engine."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """
        Initialize GEE Data Fetcher.
        
        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or IngestionConfig()
        self._initialize_gee()
        self.region = self._create_region_geometry()
        
    def _initialize_gee(self):
        """Initialize Google Earth Engine authentication."""
        try:
            if self.config.gee_service_account and self.config.gee_private_key_file:
                # Service account authentication
                if os.path.exists(self.config.gee_private_key_file):
                    credentials = ee.ServiceAccountCredentials(
                        self.config.gee_service_account,
                        self.config.gee_private_key_file
                    )
                    ee.Initialize(credentials)
                    logger.info("GEE initialized with service account")
                else:
                    logger.warning(f"Key file not found: {self.config.gee_private_key_file}")
                    ee.Initialize()
            else:
                # Default authentication
                ee.Initialize()
                logger.info("GEE initialized with default credentials")
        except Exception as e:
            logger.error(f"Failed to initialize GEE: {e}")
            raise
    
    def _create_region_geometry(self) -> ee.Geometry:
        """
        Create GEE geometry from region bounds.
        
        Returns:
            ee.Geometry: Region geometry
        """
        west, south, east, north = self.config.region_bounds
        return ee.Geometry.Rectangle([west, south, east, north])
    
    def fetch_precipitation(
        self,
        start_date: str,
        end_date: str,
        aggregation: str = "monthly"
    ) -> ee.Image:
        """
        Fetch precipitation data from CHIRPS.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            aggregation: Temporal aggregation ('daily', 'monthly', 'yearly')
            
        Returns:
            ee.Image: Precipitation image
        """
        logger.info(f"Fetching CHIRPS precipitation: {start_date} to {end_date}")
        
        collection = ee.ImageCollection(self.config.chirps_dataset) \
            .filterDate(start_date, end_date) \
            .filterBounds(self.region)
        
        if aggregation == "monthly":
            # Monthly aggregation
            months = ee.List.sequence(1, 12)
            
            def monthly_precip(month):
                return collection.filter(ee.Filter.calendarRange(month, month, 'month')) \
                    .sum() \
                    .set('month', month)
            
            monthly_collection = ee.ImageCollection.fromImages(
                months.map(monthly_precip)
            )
            return monthly_collection.toBands().rename(
                [f'precip_month_{i}' for i in range(1, 13)]
            )
        
        elif aggregation == "yearly":
            return collection.sum().rename('precip_total')
        
        else:  # daily
            return collection.toBands()
    
    def fetch_temperature(
        self,
        start_date: str,
        end_date: str,
        variable: str = "temperature_2m"
    ) -> ee.Image:
        """
        Fetch temperature data from ERA5.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            variable: Temperature variable to fetch
            
        Returns:
            ee.Image: Temperature image
        """
        logger.info(f"Fetching ERA5 temperature: {start_date} to {end_date}")
        
        collection = ee.ImageCollection(self.config.era5_dataset) \
            .filterDate(start_date, end_date) \
            .filterBounds(self.region) \
            .select(variable)
        
        # Calculate mean, min, max
        temp_mean = collection.mean().rename('temp_mean')
        temp_min = collection.min().rename('temp_min')
        temp_max = collection.max().rename('temp_max')
        
        return ee.Image.cat([temp_mean, temp_min, temp_max])
    
    def fetch_elevation(self) -> ee.Image:
        """
        Fetch elevation data from SRTM.
        
        Returns:
            ee.Image: Elevation image with derived terrain features
        """
        logger.info("Fetching SRTM elevation data")
        
        dem = ee.Image(self.config.srtm_dataset).clip(self.region)
        
        # Calculate terrain derivatives
        slope = ee.Terrain.slope(dem).rename('slope')
        aspect = ee.Terrain.aspect(dem).rename('aspect')
        
        return ee.Image.cat([
            dem.rename('elevation'),
            slope,
            aspect
        ])
    
    def fetch_land_cover(self, year: int = 2020) -> ee.Image:
        """
        Fetch land cover data from ESA WorldCover.
        
        Args:
            year: Year of land cover data
            
        Returns:
            ee.Image: Land cover image
        """
        logger.info(f"Fetching ESA WorldCover data for {year}")
        
        landcover = ee.ImageCollection(self.config.worldcover_dataset) \
            .filterBounds(self.region) \
            .first() \
            .clip(self.region)
        
        return landcover.rename('landcover')
    
    def calculate_flow_accumulation(self, dem: ee.Image) -> ee.Image:
        """
        Calculate flow accumulation from DEM.
        
        Args:
            dem: Digital Elevation Model
            
        Returns:
            ee.Image: Flow accumulation image
        """
        # Fill sinks
        filled_dem = dem.focal_max(radius=3, kernelType='square', units='pixels')
        
        # Calculate flow direction (D8 algorithm approximation)
        # Note: GEE doesn't have built-in flow accumulation, this is a simplified version
        slope = ee.Terrain.slope(filled_dem)
        
        # Use slope as proxy for flow accumulation (simplified)
        # In production, use more sophisticated hydrological modeling
        flow_accumulation = slope.multiply(100).rename('flow_accumulation')
        
        return flow_accumulation
    
    def export_to_drive(
        self,
        image: ee.Image,
        description: str,
        folder: str = "AquaPredict",
        scale: Optional[float] = None
    ) -> ee.batch.Task:
        """
        Export image to Google Drive.
        
        Args:
            image: Image to export
            description: Export description
            folder: Drive folder name
            scale: Export scale in meters
            
        Returns:
            ee.batch.Task: Export task
        """
        scale = scale or self.config.grid_resolution_m
        
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder=folder,
            region=self.region,
            scale=scale,
            crs=self.config.crs,
            maxPixels=1e13
        )
        
        task.start()
        logger.info(f"Export task started: {description}")
        return task
    
    def export_to_asset(
        self,
        image: ee.Image,
        asset_id: str,
        scale: Optional[float] = None
    ) -> ee.batch.Task:
        """
        Export image to GEE asset.
        
        Args:
            image: Image to export
            asset_id: Asset ID
            scale: Export scale in meters
            
        Returns:
            ee.batch.Task: Export task
        """
        scale = scale or self.config.grid_resolution_m
        
        task = ee.batch.Export.image.toAsset(
            image=image,
            description=asset_id.split('/')[-1],
            assetId=asset_id,
            region=self.region,
            scale=scale,
            crs=self.config.crs,
            maxPixels=1e13
        )
        
        task.start()
        logger.info(f"Export to asset started: {asset_id}")
        return task
    
    def get_image_info(self, image: ee.Image) -> Dict[str, Any]:
        """
        Get information about an image.
        
        Args:
            image: Image to inspect
            
        Returns:
            dict: Image information
        """
        info = image.getInfo()
        return {
            'bands': [band['id'] for band in info.get('bands', [])],
            'properties': info.get('properties', {}),
            'type': info.get('type', 'Unknown')
        }
    
    def sample_points(
        self,
        image: ee.Image,
        num_points: int = 1000,
        scale: Optional[float] = None
    ) -> ee.FeatureCollection:
        """
        Sample random points from an image.
        
        Args:
            image: Image to sample
            num_points: Number of points to sample
            scale: Sampling scale in meters
            
        Returns:
            ee.FeatureCollection: Sampled points
        """
        scale = scale or self.config.grid_resolution_m
        
        samples = image.sample(
            region=self.region,
            scale=scale,
            numPixels=num_points,
            geometries=True
        )
        
        return samples
