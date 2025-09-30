"""
Feature Engineering Module for AquaPredict

Computes geospatial and temporal features for aquifer prediction.
"""

from .feature_engineer import FeatureEngineer
from .config import FeatureConfig

__version__ = "1.0.0"
__all__ = ["FeatureEngineer", "FeatureConfig"]
