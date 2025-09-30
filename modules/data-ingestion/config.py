"""Configuration for data ingestion module."""

import os
from dataclasses import dataclass
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()


@dataclass
class IngestionConfig:
    """Configuration for data ingestion."""
    
    # GEE Configuration
    gee_service_account: str = os.getenv("GEE_SERVICE_ACCOUNT", "")
    gee_private_key_file: str = os.getenv("GEE_PRIVATE_KEY_FILE", "")
    
    # Region Configuration (Kenya pilot)
    region_bounds: Tuple[float, float, float, float] = (
        float(os.getenv("KENYA_BOUNDS_WEST", "33.9")),
        float(os.getenv("KENYA_BOUNDS_SOUTH", "-4.7")),
        float(os.getenv("KENYA_BOUNDS_EAST", "41.9")),
        float(os.getenv("KENYA_BOUNDS_NORTH", "5.5"))
    )
    
    # Resolution
    grid_resolution_km: float = float(os.getenv("GRID_RESOLUTION_KM", "1"))
    grid_resolution_m: float = grid_resolution_km * 1000
    
    # Data paths
    data_dir: str = os.getenv("DATA_DIR", "./data")
    raw_data_dir: str = os.path.join(data_dir, "raw")
    cache_dir: str = os.path.join(data_dir, "cache")
    
    # GEE Dataset IDs
    chirps_dataset: str = "UCSB-CHG/CHIRPS/DAILY"
    era5_dataset: str = "ECMWF/ERA5/DAILY"
    srtm_dataset: str = "USGS/SRTMGL1_003"
    worldcover_dataset: str = "ESA/WorldCover/v100"
    
    # Date ranges
    default_start_date: str = "2020-01-01"
    default_end_date: str = "2023-12-31"
    
    # Export settings
    export_format: str = "GeoTIFF"
    crs: str = "EPSG:4326"
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        os.makedirs(self.raw_data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
