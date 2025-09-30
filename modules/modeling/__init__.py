"""
Modeling Module for AquaPredict

Implements ML models for aquifer prediction and recharge forecasting.
"""

from .aquifer_classifier import AquiferClassifier
from .recharge_forecaster import RechargeForecaster
from .config import ModelConfig

__version__ = "1.0.0"
__all__ = ["AquiferClassifier", "RechargeForecaster", "ModelConfig"]
