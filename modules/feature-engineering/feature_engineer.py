"""Feature engineering for AquaPredict."""

import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage, stats
from scipy.signal import convolve2d
from sklearn.preprocessing import StandardScaler
import logging
from typing import Optional, Dict, Any, Tuple, List
import warnings

from .config import FeatureConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class FeatureEngineer:
    """Computes geospatial and temporal features for aquifer prediction."""
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize Feature Engineer.
        
        Args:
            config: Configuration object
        """
        self.config = config or FeatureConfig()
    
    def compute_twi(
        self,
        dem: np.ndarray,
        flow_accumulation: np.ndarray,
        cell_size: float = 1000.0
    ) -> np.ndarray:
        """
        Compute Topographic Wetness Index (TWI).
        
        Formula: TWI = ln((flow_accumulation + 1) / (tan(slope_rad) + epsilon))
        
        Args:
            dem: Digital Elevation Model
            flow_accumulation: Flow accumulation raster
            cell_size: Cell size in meters
            
        Returns:
            np.ndarray: TWI values
        """
        logger.info("Computing Topographic Wetness Index (TWI)")
        
        # Compute slope in radians
        slope_rad = self._compute_slope_radians(dem, cell_size)
        
        # Compute TWI
        # Add 1 to flow accumulation to avoid log(0)
        # Add epsilon to tan(slope) to avoid division by zero
        twi = np.log(
            (flow_accumulation + 1) / 
            (np.tan(slope_rad) + self.config.twi_epsilon)
        )
        
        # Handle infinite values
        twi = np.where(np.isinf(twi), np.nan, twi)
        
        logger.info(f"TWI range: [{np.nanmin(twi):.2f}, {np.nanmax(twi):.2f}]")
        return twi
    
    def _compute_slope_radians(
        self,
        dem: np.ndarray,
        cell_size: float = 1000.0
    ) -> np.ndarray:
        """
        Compute slope in radians from DEM.
        
        Args:
            dem: Digital Elevation Model
            cell_size: Cell size in meters
            
        Returns:
            np.ndarray: Slope in radians
        """
        # Compute gradients
        dy, dx = np.gradient(dem, cell_size)
        
        # Compute slope in radians
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        
        return slope_rad
    
    def compute_tpi(
        self,
        dem: np.ndarray,
        window_size: int = 3
    ) -> np.ndarray:
        """
        Compute Topographic Position Index (TPI).
        
        TPI = elevation - mean(neighborhood elevation)
        
        Args:
            dem: Digital Elevation Model
            window_size: Neighborhood window size
            
        Returns:
            np.ndarray: TPI values
        """
        logger.info(f"Computing Topographic Position Index (TPI) with window={window_size}")
        
        # Compute mean elevation in neighborhood
        kernel = np.ones((window_size, window_size)) / (window_size ** 2)
        mean_elevation = convolve2d(dem, kernel, mode='same', boundary='symm')
        
        # TPI = elevation - mean neighborhood elevation
        tpi = dem - mean_elevation
        
        logger.info(f"TPI range: [{np.nanmin(tpi):.2f}, {np.nanmax(tpi):.2f}]")
        return tpi
    
    def compute_slope_aspect(
        self,
        dem: np.ndarray,
        cell_size: float = 1000.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute slope and aspect from DEM.
        
        Args:
            dem: Digital Elevation Model
            cell_size: Cell size in meters
            
        Returns:
            Tuple of (slope in degrees, aspect in degrees)
        """
        logger.info("Computing slope and aspect")
        
        # Compute gradients
        dy, dx = np.gradient(dem, cell_size)
        
        # Slope in degrees
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        
        # Aspect in degrees (0-360)
        aspect_rad = np.arctan2(-dy, dx)
        aspect_deg = np.degrees(aspect_rad)
        aspect_deg = (aspect_deg + 360) % 360  # Convert to 0-360
        
        return slope_deg, aspect_deg
    
    def compute_curvature(
        self,
        dem: np.ndarray,
        cell_size: float = 1000.0
    ) -> Dict[str, np.ndarray]:
        """
        Compute surface curvature metrics.
        
        Args:
            dem: Digital Elevation Model
            cell_size: Cell size in meters
            
        Returns:
            Dictionary with 'profile', 'plan', and 'total' curvature
        """
        logger.info("Computing curvature")
        
        # Compute first derivatives
        dy, dx = np.gradient(dem, cell_size)
        
        # Compute second derivatives
        dyy, dyx = np.gradient(dy, cell_size)
        dxy, dxx = np.gradient(dx, cell_size)
        
        # Profile curvature (curvature in direction of slope)
        p = dx**2 + dy**2
        profile_curvature = -(dxx * dx**2 + 2 * dxy * dx * dy + dyy * dy**2) / (p * np.sqrt(p + 1e-10))
        
        # Plan curvature (curvature perpendicular to slope)
        plan_curvature = (dxx * dy**2 - 2 * dxy * dx * dy + dyy * dx**2) / (p**1.5 + 1e-10)
        
        # Total curvature
        total_curvature = dxx + dyy
        
        return {
            'profile': profile_curvature,
            'plan': plan_curvature,
            'total': total_curvature
        }
    
    def compute_spi(
        self,
        precipitation: np.ndarray,
        timescale: int = 3,
        distribution: str = 'gamma'
    ) -> np.ndarray:
        """
        Compute Standardized Precipitation Index (SPI).
        
        Args:
            precipitation: Precipitation time series [time, lat, lon]
            timescale: Timescale in months
            distribution: Distribution to fit ('gamma', 'normal')
            
        Returns:
            np.ndarray: SPI values
        """
        logger.info(f"Computing SPI-{timescale}")
        
        # Ensure 3D array
        if precipitation.ndim == 2:
            precipitation = precipitation[np.newaxis, :, :]
        
        n_times, n_lat, n_lon = precipitation.shape
        spi = np.zeros_like(precipitation)
        
        # Compute rolling sum
        if timescale > 1:
            precip_sum = self._rolling_sum(precipitation, timescale, axis=0)
        else:
            precip_sum = precipitation
        
        # Compute SPI for each pixel
        for i in range(n_lat):
            for j in range(n_lon):
                pixel_data = precip_sum[:, i, j]
                
                # Skip if all NaN
                if np.all(np.isnan(pixel_data)):
                    spi[:, i, j] = np.nan
                    continue
                
                # Remove NaN values for fitting
                valid_data = pixel_data[~np.isnan(pixel_data)]
                
                if len(valid_data) < 10:  # Need sufficient data
                    spi[:, i, j] = np.nan
                    continue
                
                try:
                    if distribution == 'gamma':
                        # Fit gamma distribution
                        shape, loc, scale = stats.gamma.fit(valid_data[valid_data > 0])
                        
                        # Compute CDF
                        cdf = stats.gamma.cdf(pixel_data, shape, loc, scale)
                    else:
                        # Fit normal distribution
                        mean, std = np.mean(valid_data), np.std(valid_data)
                        cdf = stats.norm.cdf(pixel_data, mean, std)
                    
                    # Convert to standard normal (SPI)
                    spi[:, i, j] = stats.norm.ppf(cdf)
                    
                except Exception:
                    spi[:, i, j] = np.nan
        
        # Handle infinite values
        spi = np.where(np.isinf(spi), np.nan, spi)
        
        logger.info(f"SPI-{timescale} computed. Range: [{np.nanmin(spi):.2f}, {np.nanmax(spi):.2f}]")
        return spi
    
    def compute_spei(
        self,
        precipitation: np.ndarray,
        temperature: np.ndarray,
        timescale: int = 3,
        latitude: float = 0.0
    ) -> np.ndarray:
        """
        Compute Standardized Precipitation-Evapotranspiration Index (SPEI).
        
        Args:
            precipitation: Precipitation time series [time, lat, lon]
            temperature: Temperature time series [time, lat, lon]
            timescale: Timescale in months
            latitude: Latitude for ET calculation
            
        Returns:
            np.ndarray: SPEI values
        """
        logger.info(f"Computing SPEI-{timescale}")
        
        # Compute potential evapotranspiration
        pet = self.compute_pet_hargreaves(temperature, latitude)
        
        # Compute water balance (P - PET)
        water_balance = precipitation - pet
        
        # Compute SPEI using same method as SPI but on water balance
        spei = self.compute_spi(water_balance, timescale, distribution='normal')
        
        logger.info(f"SPEI-{timescale} computed. Range: [{np.nanmin(spei):.2f}, {np.nanmax(spei):.2f}]")
        return spei
    
    def compute_pet_hargreaves(
        self,
        temperature: np.ndarray,
        latitude: float = 0.0
    ) -> np.ndarray:
        """
        Compute Potential Evapotranspiration using Hargreaves method.
        
        Simplified formula: PET = 0.0023 * (T_mean + 17.8) * (T_max - T_min)^0.5 * Ra
        
        Args:
            temperature: Temperature array [time, lat, lon] or dict with 'mean', 'min', 'max'
            latitude: Latitude in degrees
            
        Returns:
            np.ndarray: PET values in mm/day
        """
        logger.info("Computing PET using Hargreaves method")
        
        if isinstance(temperature, dict):
            t_mean = temperature['mean']
            t_max = temperature['max']
            t_min = temperature['min']
        else:
            # Assume single temperature array
            t_mean = temperature
            t_max = temperature + 5  # Rough approximation
            t_min = temperature - 5
        
        # Extraterrestrial radiation (Ra) - simplified
        # In production, compute based on day of year and latitude
        ra = 15.0  # MJ/m²/day (approximate average)
        
        # Hargreaves formula
        pet = 0.0023 * (t_mean + 17.8) * np.sqrt(t_max - t_min) * ra
        
        # Ensure non-negative
        pet = np.maximum(pet, 0)
        
        return pet
    
    def compute_distance_to_water(
        self,
        water_mask: np.ndarray,
        cell_size: float = 1000.0
    ) -> np.ndarray:
        """
        Compute distance to nearest water body.
        
        Args:
            water_mask: Binary mask of water bodies (1=water, 0=land)
            cell_size: Cell size in meters
            
        Returns:
            np.ndarray: Distance to water in meters
        """
        logger.info("Computing distance to water")
        
        # Compute Euclidean distance transform
        distance = ndimage.distance_transform_edt(1 - water_mask)
        
        # Convert to meters
        distance_m = distance * cell_size
        
        logger.info(f"Distance to water range: [0, {np.max(distance_m):.0f}] meters")
        return distance_m
    
    def compute_temporal_statistics(
        self,
        data: np.ndarray,
        windows: Optional[List[int]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Compute temporal statistics (mean, std, min, max, trend).
        
        Args:
            data: Time series data [time, lat, lon]
            windows: Rolling window sizes in time steps
            
        Returns:
            Dictionary of statistics
        """
        logger.info("Computing temporal statistics")
        
        windows = windows or self.config.temporal_windows
        
        stats_dict = {
            'mean': np.mean(data, axis=0),
            'std': np.std(data, axis=0),
            'min': np.min(data, axis=0),
            'max': np.max(data, axis=0),
        }
        
        # Compute trend (linear regression slope)
        n_times = data.shape[0]
        time_index = np.arange(n_times)
        
        # Reshape for vectorized regression
        data_2d = data.reshape(n_times, -1)
        
        # Compute slopes
        slopes = np.zeros(data_2d.shape[1])
        for i in range(data_2d.shape[1]):
            valid_mask = ~np.isnan(data_2d[:, i])
            if valid_mask.sum() > 2:
                slope, _ = np.polyfit(time_index[valid_mask], data_2d[valid_mask, i], 1)
                slopes[i] = slope
            else:
                slopes[i] = np.nan
        
        stats_dict['trend'] = slopes.reshape(data.shape[1:])
        
        return stats_dict
    
    def create_lag_features(
        self,
        data: np.ndarray,
        lag_periods: Optional[List[int]] = None
    ) -> Dict[str, np.ndarray]:
        """
        Create lag features for time series.
        
        Args:
            data: Time series data [time, lat, lon]
            lag_periods: List of lag periods
            
        Returns:
            Dictionary of lag features
        """
        logger.info("Creating lag features")
        
        lag_periods = lag_periods or self.config.lag_periods
        
        lag_features = {}
        for lag in lag_periods:
            if lag < data.shape[0]:
                lag_features[f'lag_{lag}'] = np.roll(data, lag, axis=0)
                # Set first 'lag' time steps to NaN
                lag_features[f'lag_{lag}'][:lag] = np.nan
        
        return lag_features
    
    def _rolling_sum(
        self,
        data: np.ndarray,
        window: int,
        axis: int = 0
    ) -> np.ndarray:
        """
        Compute rolling sum along specified axis.
        
        Args:
            data: Input array
            window: Window size
            axis: Axis along which to compute
            
        Returns:
            np.ndarray: Rolling sum
        """
        # Use pandas for efficient rolling computation
        shape = data.shape
        
        if axis == 0:
            # Reshape to 2D for pandas
            data_2d = data.reshape(shape[0], -1)
            df = pd.DataFrame(data_2d)
            rolling_sum = df.rolling(window=window, min_periods=1).sum().values
            return rolling_sum.reshape(shape)
        else:
            raise NotImplementedError("Only axis=0 supported")
    
    def generate_all_features(
        self,
        data_dict: Dict[str, np.ndarray],
        cell_size: float = 1000.0
    ) -> Dict[str, np.ndarray]:
        """
        Generate all features from input data.
        
        Args:
            data_dict: Dictionary of input data arrays
                Required keys: 'dem', 'precipitation', 'temperature'
                Optional: 'flow_accumulation', 'landcover', 'soil'
            cell_size: Cell size in meters
            
        Returns:
            Dictionary of all computed features
        """
        logger.info("=" * 80)
        logger.info("Generating all features")
        logger.info("=" * 80)
        
        features = {}
        
        # Static features
        if 'dem' in data_dict:
            dem = data_dict['dem']
            
            # Slope and aspect
            slope, aspect = self.compute_slope_aspect(dem, cell_size)
            features['slope'] = slope
            features['aspect'] = aspect
            
            # TPI
            features['tpi'] = self.compute_tpi(dem)
            
            # Curvature
            curvature = self.compute_curvature(dem, cell_size)
            features.update({f'curvature_{k}': v for k, v in curvature.items()})
            
            # TWI (if flow accumulation available)
            if 'flow_accumulation' in data_dict:
                features['twi'] = self.compute_twi(
                    dem,
                    data_dict['flow_accumulation'],
                    cell_size
                )
        
        # Temporal features
        if 'precipitation' in data_dict:
            precip = data_dict['precipitation']
            
            # SPI for multiple timescales
            for timescale in self.config.spi_timescales:
                features[f'spi_{timescale}'] = self.compute_spi(precip, timescale)
            
            # Precipitation statistics
            precip_stats = self.compute_temporal_statistics(precip)
            features.update({f'precip_{k}': v for k, v in precip_stats.items()})
        
        if 'temperature' in data_dict and 'precipitation' in data_dict:
            temp = data_dict['temperature']
            precip = data_dict['precipitation']
            
            # SPEI for multiple timescales
            for timescale in self.config.spei_timescales:
                features[f'spei_{timescale}'] = self.compute_spei(
                    precip, temp, timescale
                )
            
            # PET
            features['pet'] = self.compute_pet_hargreaves(temp)
            
            # Water balance
            features['water_balance'] = precip - features['pet']
        
        logger.info(f"Generated {len(features)} features")
        logger.info("=" * 80)
        
        return features
