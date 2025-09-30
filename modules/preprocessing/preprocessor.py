"""Data preprocessor for AquaPredict."""

import numpy as np
import pandas as pd
import xarray as xr
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_bounds
from scipy import interpolate
from scipy.stats import zscore
from sklearn.preprocessing import MinMaxScaler, RobustScaler
import logging
from typing import Optional, Union, Tuple, Dict, Any
import os

from .config import PreprocessingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Preprocesses geospatial data for AquaPredict."""
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        """
        Initialize Data Preprocessor.
        
        Args:
            config: Configuration object
        """
        self.config = config or PreprocessingConfig()
    
    def clean_raster(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        nodata_value: Optional[float] = None
    ) -> np.ndarray:
        """
        Clean raster data by handling invalid values.
        
        Args:
            input_path: Path to input raster
            output_path: Path to save cleaned raster (optional)
            nodata_value: NoData value to use
            
        Returns:
            np.ndarray: Cleaned data array
        """
        logger.info(f"Cleaning raster: {input_path}")
        
        with rasterio.open(input_path) as src:
            data = src.read()
            profile = src.profile
            
            # Handle NoData values
            if nodata_value is None:
                nodata_value = src.nodata or -9999
            
            # Replace NoData with NaN
            data = np.where(data == nodata_value, np.nan, data)
            
            # Remove infinite values
            data = np.where(np.isinf(data), np.nan, data)
            
            # Check data quality
            missing_ratio = np.isnan(data).sum() / data.size
            logger.info(f"Missing data ratio: {missing_ratio:.2%}")
            
            if missing_ratio > self.config.max_missing_ratio:
                logger.warning(
                    f"High missing data ratio ({missing_ratio:.2%}) exceeds threshold "
                    f"({self.config.max_missing_ratio:.2%})"
                )
            
            # Save if output path provided
            if output_path:
                profile.update(nodata=nodata_value)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(data)
                
                logger.info(f"Cleaned raster saved to: {output_path}")
            
            return data
    
    def fill_missing(
        self,
        data: np.ndarray,
        method: Optional[str] = None
    ) -> np.ndarray:
        """
        Fill missing values in array.
        
        Args:
            data: Input data array
            method: Fill method ('interpolate', 'mean', 'median', 'forward', 'backward')
            
        Returns:
            np.ndarray: Data with filled values
        """
        method = method or self.config.fill_method
        logger.info(f"Filling missing values using method: {method}")
        
        if data.ndim == 2:
            # 2D spatial interpolation
            if method == 'interpolate':
                return self._interpolate_2d(data)
            elif method == 'mean':
                fill_value = np.nanmean(data)
                return np.where(np.isnan(data), fill_value, data)
            elif method == 'median':
                fill_value = np.nanmedian(data)
                return np.where(np.isnan(data), fill_value, data)
            else:
                logger.warning(f"Method {method} not supported for 2D, using mean")
                fill_value = np.nanmean(data)
                return np.where(np.isnan(data), fill_value, data)
        
        elif data.ndim == 3:
            # 3D temporal-spatial interpolation
            filled = np.zeros_like(data)
            for i in range(data.shape[0]):
                filled[i] = self.fill_missing(data[i], method)
            return filled
        
        else:
            raise ValueError(f"Unsupported data dimensions: {data.ndim}")
    
    def _interpolate_2d(self, data: np.ndarray) -> np.ndarray:
        """
        Interpolate 2D spatial data.
        
        Args:
            data: 2D data array
            
        Returns:
            np.ndarray: Interpolated data
        """
        # Get valid data points
        valid_mask = ~np.isnan(data)
        
        if not valid_mask.any():
            logger.warning("No valid data points for interpolation")
            return data
        
        # Create coordinate grids
        rows, cols = np.indices(data.shape)
        valid_points = np.column_stack([rows[valid_mask], cols[valid_mask]])
        valid_values = data[valid_mask]
        
        # Interpolate missing points
        missing_points = np.column_stack([rows[~valid_mask], cols[~valid_mask]])
        
        if len(missing_points) == 0:
            return data
        
        # Use nearest neighbor interpolation for robustness
        interpolated_values = interpolate.griddata(
            valid_points,
            valid_values,
            missing_points,
            method='nearest'
        )
        
        # Fill missing values
        filled_data = data.copy()
        filled_data[~valid_mask] = interpolated_values
        
        return filled_data
    
    def detect_outliers(
        self,
        data: np.ndarray,
        threshold: Optional[float] = None
    ) -> np.ndarray:
        """
        Detect outliers using z-score method.
        
        Args:
            data: Input data array
            threshold: Z-score threshold
            
        Returns:
            np.ndarray: Boolean mask of outliers
        """
        threshold = threshold or self.config.outlier_std_threshold
        
        # Flatten and remove NaN
        flat_data = data.flatten()
        valid_data = flat_data[~np.isnan(flat_data)]
        
        if len(valid_data) == 0:
            return np.zeros_like(data, dtype=bool)
        
        # Calculate z-scores
        z_scores = np.abs(zscore(valid_data))
        
        # Create outlier mask
        outlier_mask = np.zeros_like(flat_data, dtype=bool)
        outlier_mask[~np.isnan(flat_data)] = z_scores > threshold
        
        return outlier_mask.reshape(data.shape)
    
    def remove_outliers(
        self,
        data: np.ndarray,
        threshold: Optional[float] = None,
        replace_with: str = 'nan'
    ) -> np.ndarray:
        """
        Remove or replace outliers.
        
        Args:
            data: Input data array
            threshold: Z-score threshold
            replace_with: Replacement method ('nan', 'median', 'mean')
            
        Returns:
            np.ndarray: Data with outliers handled
        """
        outlier_mask = self.detect_outliers(data, threshold)
        
        outlier_count = outlier_mask.sum()
        outlier_ratio = outlier_count / data.size
        logger.info(f"Detected {outlier_count} outliers ({outlier_ratio:.2%})")
        
        cleaned_data = data.copy()
        
        if replace_with == 'nan':
            cleaned_data[outlier_mask] = np.nan
        elif replace_with == 'median':
            fill_value = np.nanmedian(data[~outlier_mask])
            cleaned_data[outlier_mask] = fill_value
        elif replace_with == 'mean':
            fill_value = np.nanmean(data[~outlier_mask])
            cleaned_data[outlier_mask] = fill_value
        
        return cleaned_data
    
    def normalize(
        self,
        data: np.ndarray,
        method: Optional[str] = None,
        feature_range: Tuple[float, float] = (0, 1)
    ) -> np.ndarray:
        """
        Normalize data.
        
        Args:
            data: Input data array
            method: Normalization method ('minmax', 'zscore', 'robust')
            feature_range: Target range for minmax scaling
            
        Returns:
            np.ndarray: Normalized data
        """
        method = method or self.config.normalization_method
        logger.info(f"Normalizing data using method: {method}")
        
        # Flatten and remove NaN
        original_shape = data.shape
        flat_data = data.flatten().reshape(-1, 1)
        valid_mask = ~np.isnan(flat_data.flatten())
        
        if not valid_mask.any():
            logger.warning("No valid data for normalization")
            return data
        
        normalized = flat_data.copy()
        
        if method == 'minmax':
            scaler = MinMaxScaler(feature_range=feature_range)
            normalized[valid_mask] = scaler.fit_transform(
                flat_data[valid_mask].reshape(-1, 1)
            ).flatten()
        
        elif method == 'zscore':
            valid_data = flat_data[valid_mask]
            mean = np.mean(valid_data)
            std = np.std(valid_data)
            normalized[valid_mask] = ((flat_data[valid_mask] - mean) / std).flatten()
        
        elif method == 'robust':
            scaler = RobustScaler()
            normalized[valid_mask] = scaler.fit_transform(
                flat_data[valid_mask].reshape(-1, 1)
            ).flatten()
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized.reshape(original_shape)
    
    def resample_raster(
        self,
        input_path: str,
        output_path: str,
        target_resolution: Optional[float] = None,
        resampling_method: Resampling = Resampling.bilinear
    ) -> str:
        """
        Resample raster to target resolution.
        
        Args:
            input_path: Path to input raster
            output_path: Path to output raster
            target_resolution: Target resolution in meters
            resampling_method: Resampling method
            
        Returns:
            str: Path to resampled raster
        """
        target_resolution = target_resolution or self.config.target_resolution_m
        logger.info(f"Resampling raster to {target_resolution}m resolution")
        
        with rasterio.open(input_path) as src:
            # Calculate new dimensions
            scale_factor = src.res[0] / target_resolution
            new_width = int(src.width * scale_factor)
            new_height = int(src.height * scale_factor)
            
            # Create new transform
            new_transform = from_bounds(
                *src.bounds,
                new_width,
                new_height
            )
            
            # Prepare output array
            resampled_data = np.empty(
                (src.count, new_height, new_width),
                dtype=src.dtypes[0]
            )
            
            # Resample each band
            for i in range(src.count):
                reproject(
                    source=rasterio.band(src, i + 1),
                    destination=resampled_data[i],
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=new_transform,
                    dst_crs=src.crs,
                    resampling=resampling_method
                )
            
            # Update profile
            profile = src.profile.copy()
            profile.update({
                'height': new_height,
                'width': new_width,
                'transform': new_transform
            })
            
            # Write output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(resampled_data)
        
        logger.info(f"Resampled raster saved to: {output_path}")
        return output_path
    
    def align_temporal_data(
        self,
        datasets: Dict[str, xr.Dataset],
        time_resolution: Optional[str] = None
    ) -> xr.Dataset:
        """
        Align multiple temporal datasets to common time grid.
        
        Args:
            datasets: Dictionary of named xarray Datasets
            time_resolution: Target time resolution
            
        Returns:
            xr.Dataset: Aligned dataset
        """
        time_resolution = time_resolution or self.config.temporal_resolution
        logger.info(f"Aligning temporal data to {time_resolution} resolution")
        
        # Find common time range
        time_ranges = [ds.time.values for ds in datasets.values()]
        common_start = max(tr.min() for tr in time_ranges)
        common_end = min(tr.max() for tr in time_ranges)
        
        # Create common time grid
        if time_resolution == 'monthly':
            time_grid = pd.date_range(common_start, common_end, freq='MS')
        elif time_resolution == 'daily':
            time_grid = pd.date_range(common_start, common_end, freq='D')
        elif time_resolution == 'yearly':
            time_grid = pd.date_range(common_start, common_end, freq='YS')
        else:
            raise ValueError(f"Unknown time resolution: {time_resolution}")
        
        # Resample and merge datasets
        aligned_datasets = {}
        for name, ds in datasets.items():
            aligned_datasets[name] = ds.resample(time=time_resolution).mean()
        
        # Merge into single dataset
        merged = xr.merge(aligned_datasets.values())
        
        return merged
