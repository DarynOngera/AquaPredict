"""Configuration for feature engineering module."""

import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class FeatureConfig:
    """Configuration for feature engineering."""
    
    # Data paths
    data_dir: str = os.getenv("DATA_DIR", "./data")
    processed_data_dir: str = os.path.join(data_dir, "processed")
    features_dir: str = os.path.join(data_dir, "features")
    
    # Static features to compute
    static_features: List[str] = None
    
    # Temporal features to compute
    temporal_features: List[str] = None
    
    # TWI parameters
    twi_epsilon: float = 0.001  # Small value to avoid division by zero
    
    # SPI/SPEI parameters
    spi_timescales: List[int] = None  # months
    spei_timescales: List[int] = None  # months
    distribution: str = "gamma"  # Distribution for SPI/SPEI fitting
    
    # Evapotranspiration parameters
    et_method: str = "hargreaves"  # 'hargreaves', 'penman-monteith'
    
    # Temporal aggregation
    temporal_windows: List[int] = None  # days for rolling statistics
    
    # Lag features
    lag_periods: List[int] = None  # time steps for lag features
    
    def __post_init__(self):
        """Initialize default values and create directories."""
        if self.static_features is None:
            self.static_features = [
                'twi', 'tpi', 'slope', 'aspect', 'curvature',
                'distance_to_water', 'soil_texture', 'soil_porosity'
            ]
        
        if self.temporal_features is None:
            self.temporal_features = [
                'spi', 'spei', 'precip_mean', 'precip_std',
                'temp_mean', 'temp_min', 'temp_max', 'et', 'water_balance'
            ]
        
        if self.spi_timescales is None:
            self.spi_timescales = [1, 3, 6, 12]  # 1, 3, 6, 12 months
        
        if self.spei_timescales is None:
            self.spei_timescales = [1, 3, 6, 12]
        
        if self.temporal_windows is None:
            self.temporal_windows = [7, 30, 90, 365]  # days
        
        if self.lag_periods is None:
            self.lag_periods = [1, 3, 6, 12]  # months
        
        os.makedirs(self.features_dir, exist_ok=True)
