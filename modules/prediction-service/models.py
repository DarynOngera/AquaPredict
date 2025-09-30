"""Model management for prediction service."""

import os
import joblib
import numpy as np
import logging
from typing import Dict, Any, Optional, List, Tuple

from config import ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelManager:
    """Manages ML models for predictions."""
    
    def __init__(self, config: ServiceConfig):
        """
        Initialize Model Manager.
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.aquifer_model = None
        self.recharge_model = None
        self.models_loaded = False
        self.feature_names = []
    
    def load_models(self):
        """Load models from disk."""
        logger.info("Loading models...")
        
        try:
            # Load aquifer classifier
            aquifer_path = os.path.join(
                self.config.model_path,
                self.config.aquifer_model_file
            )
            
            if os.path.exists(aquifer_path):
                model_data = joblib.load(aquifer_path)
                self.aquifer_model = model_data['model']
                self.feature_names = model_data.get('feature_names', [])
                logger.info(f"✓ Loaded aquifer classifier from {aquifer_path}")
            else:
                logger.warning(f"Aquifer model not found at {aquifer_path}")
            
            # Load recharge forecaster
            recharge_path = os.path.join(
                self.config.model_path,
                self.config.recharge_model_file
            )
            
            if os.path.exists(recharge_path):
                self.recharge_model = joblib.load(recharge_path)
                logger.info(f"✓ Loaded recharge forecaster from {recharge_path}")
            else:
                logger.warning(f"Recharge model not found at {recharge_path}")
            
            self.models_loaded = True
            logger.info("✓ All models loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            self.models_loaded = False
            raise
    
    def reload_models(self):
        """Reload models from disk."""
        logger.info("Reloading models...")
        self.models_loaded = False
        self.load_models()
    
    def predict_aquifer(
        self,
        features: np.ndarray
    ) -> Tuple[int, float]:
        """
        Predict aquifer presence.
        
        Args:
            features: Feature array [n_samples, n_features]
            
        Returns:
            Tuple of (prediction, probability)
        """
        if self.aquifer_model is None:
            raise ValueError("Aquifer model not loaded")
        
        # Get prediction
        if isinstance(self.aquifer_model, dict):
            # Ensemble model
            predictions = []
            probabilities = []
            
            for model in self.aquifer_model.values():
                pred = model.predict(features)
                proba = model.predict_proba(features)
                predictions.append(pred[0])
                probabilities.append(proba[0])
            
            # Majority voting for prediction
            prediction = int(np.bincount(predictions).argmax())
            
            # Average probability
            probability = np.mean(probabilities, axis=0)[prediction]
        
        else:
            # Single model
            prediction = int(self.aquifer_model.predict(features)[0])
            probabilities = self.aquifer_model.predict_proba(features)[0]
            probability = float(probabilities[prediction])
        
        return prediction, probability
    
    def forecast_recharge(
        self,
        historical_data: np.ndarray,
        horizon: int = 12
    ) -> np.ndarray:
        """
        Forecast groundwater recharge.
        
        Args:
            historical_data: Historical time series data
            horizon: Forecast horizon
            
        Returns:
            Forecasted values
        """
        if self.recharge_model is None:
            raise ValueError("Recharge model not loaded")
        
        # Ensure 2D array
        if historical_data.ndim == 1:
            historical_data = historical_data.reshape(-1, 1)
        
        # Generate forecast
        forecast = self.recharge_model.forecast(historical_data, horizon)
        
        return forecast
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model information
        """
        models = []
        
        if self.aquifer_model is not None:
            models.append({
                'name': 'aquifer_classifier',
                'type': 'classification',
                'loaded': True,
                'features': len(self.feature_names)
            })
        
        if self.recharge_model is not None:
            models.append({
                'name': 'recharge_forecaster',
                'type': 'time_series',
                'loaded': True
            })
        
        return models
    
    def get_feature_names(self) -> List[str]:
        """Get feature names."""
        return self.feature_names
