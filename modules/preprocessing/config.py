"""Configuration for preprocessing module."""

import os
from dataclasses import dataclass
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()


@dataclass
class PreprocessingConfig:
    """Configuration for data preprocessing."""
    
    # Data paths
    data_dir: str = os.getenv("DATA_DIR", "./data")
    raw_data_dir: str = os.path.join(data_dir, "raw")
    processed_data_dir: str = os.path.join(data_dir, "processed")
    
    # Quality control thresholds
    max_missing_ratio: float = 0.3  # Maximum allowed missing data ratio
    outlier_std_threshold: float = 3.0  # Standard deviations for outlier detection
    
    # Normalization
    normalization_method: str = "minmax"  # 'minmax', 'zscore', 'robust'
    
    # Spatial parameters
    target_crs: str = "EPSG:4326"
    target_resolution_m: float = 1000.0  # 1km
    
    # Temporal parameters
    temporal_resolution: str = "monthly"  # 'daily', 'monthly', 'yearly'
    
    # Missing value handling
    fill_method: str = "interpolate"  # 'interpolate', 'mean', 'median', 'forward', 'backward'
    
    # Masking
    mask_water_bodies: bool = True
    mask_urban_areas: bool = False
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        os.makedirs(self.processed_data_dir, exist_ok=True)
