"""Data exporter for converting GEE data to local formats."""

import ee
import os
import logging
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import xarray as xr
from typing import Optional, Tuple, Dict, Any
import requests
from tqdm import tqdm

from .config import IngestionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataExporter:
    """Exports GEE data to local file formats."""
    
    def __init__(self, config: Optional[IngestionConfig] = None):
        """
        Initialize Data Exporter.
        
        Args:
            config: Configuration object
        """
        self.config = config or IngestionConfig()
    
    def export_to_geotiff(
        self,
        image: ee.Image,
        output_path: str,
        scale: Optional[float] = None,
        region: Optional[ee.Geometry] = None
    ) -> str:
        """
        Export GEE image to GeoTIFF.
        
        Args:
            image: GEE image to export
            output_path: Output file path
            scale: Export scale in meters
            region: Region to export (defaults to config region)
            
        Returns:
            str: Path to exported file
        """
        scale = scale or self.config.grid_resolution_m
        region = region or ee.Geometry.Rectangle(self.config.region_bounds)
        
        logger.info(f"Exporting to GeoTIFF: {output_path}")
        
        # Get download URL
        url = image.getDownloadURL({
            'scale': scale,
            'crs': self.config.crs,
            'region': region,
            'format': 'GEO_TIFF'
        })
        
        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        total_size = int(response.headers.get('content-length', 0))
        with open(output_path, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=os.path.basename(output_path)
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
        
        logger.info(f"Exported to: {output_path}")
        return output_path
    
    def export_to_netcdf(
        self,
        image: ee.Image,
        output_path: str,
        scale: Optional[float] = None,
        region: Optional[ee.Geometry] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export GEE image to NetCDF.
        
        Args:
            image: GEE image to export
            output_path: Output file path
            scale: Export scale in meters
            region: Region to export
            metadata: Additional metadata
            
        Returns:
            str: Path to exported file
        """
        scale = scale or self.config.grid_resolution_m
        region = region or ee.Geometry.Rectangle(self.config.region_bounds)
        
        logger.info(f"Exporting to NetCDF: {output_path}")
        
        # First export to GeoTIFF
        temp_tif = output_path.replace('.nc', '_temp.tif')
        self.export_to_geotiff(image, temp_tif, scale, region)
        
        # Convert to NetCDF using xarray
        with rasterio.open(temp_tif) as src:
            data = src.read()
            transform = src.transform
            crs = src.crs
            
            # Create coordinates
            height, width = data.shape[1], data.shape[2]
            west, south, east, north = self.config.region_bounds
            
            lons = np.linspace(west, east, width)
            lats = np.linspace(north, south, height)
            
            # Create xarray Dataset
            bands = image.bandNames().getInfo()
            data_vars = {}
            
            for i, band in enumerate(bands):
                data_vars[band] = (['lat', 'lon'], data[i])
            
            ds = xr.Dataset(
                data_vars,
                coords={
                    'lon': lons,
                    'lat': lats
                }
            )
            
            # Add metadata
            ds.attrs['crs'] = str(crs)
            ds.attrs['scale'] = scale
            if metadata:
                ds.attrs.update(metadata)
            
            # Save to NetCDF
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            ds.to_netcdf(output_path)
        
        # Clean up temp file
        if os.path.exists(temp_tif):
            os.remove(temp_tif)
        
        logger.info(f"Exported to: {output_path}")
        return output_path
    
    def export_feature_collection_to_csv(
        self,
        feature_collection: ee.FeatureCollection,
        output_path: str
    ) -> str:
        """
        Export GEE FeatureCollection to CSV.
        
        Args:
            feature_collection: GEE FeatureCollection
            output_path: Output CSV path
            
        Returns:
            str: Path to exported file
        """
        logger.info(f"Exporting FeatureCollection to CSV: {output_path}")
        
        # Get download URL
        url = feature_collection.getDownloadURL('csv')
        
        # Download file
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Exported to: {output_path}")
        return output_path
    
    def export_feature_collection_to_geojson(
        self,
        feature_collection: ee.FeatureCollection,
        output_path: str
    ) -> str:
        """
        Export GEE FeatureCollection to GeoJSON.
        
        Args:
            feature_collection: GEE FeatureCollection
            output_path: Output GeoJSON path
            
        Returns:
            str: Path to exported file
        """
        logger.info(f"Exporting FeatureCollection to GeoJSON: {output_path}")
        
        # Get download URL
        url = feature_collection.getDownloadURL('geojson')
        
        # Download file
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Exported to: {output_path}")
        return output_path
    
    def create_grid(
        self,
        resolution_km: Optional[float] = None
    ) -> ee.FeatureCollection:
        """
        Create a grid of points for the region.
        
        Args:
            resolution_km: Grid resolution in kilometers
            
        Returns:
            ee.FeatureCollection: Grid points
        """
        resolution_km = resolution_km or self.config.grid_resolution_km
        resolution_deg = resolution_km / 111.0  # Approximate conversion
        
        west, south, east, north = self.config.region_bounds
        
        # Create grid points
        lons = ee.List.sequence(west, east, resolution_deg)
        lats = ee.List.sequence(south, north, resolution_deg)
        
        def create_point(lon):
            def create_point_lat(lat):
                return ee.Feature(ee.Geometry.Point([lon, lat]))
            return lats.map(create_point_lat)
        
        points = lons.map(create_point).flatten()
        
        return ee.FeatureCollection(points)
