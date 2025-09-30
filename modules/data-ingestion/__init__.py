"""
Data Ingestion Module for AquaPredict

Handles fetching and extraction of geospatial data from Google Earth Engine
and other sources for aquifer prediction and groundwater analysis.
"""

from .gee_fetcher import GEEDataFetcher
from .data_exporter import DataExporter
from .config import IngestionConfig

__version__ = "1.0.0"
__all__ = ["GEEDataFetcher", "DataExporter", "IngestionConfig"]
