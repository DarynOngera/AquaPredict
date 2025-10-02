"""
Model Service for Precipitation Prediction
Handles model loading, caching, and inference
"""

import joblib
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PrecipitationModel:
    """Wrapper for precipitation prediction models"""
    
    def __init__(self, model_path: str, metadata_path: str):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path)
        self.model = None
        self.metadata = None
        self.feature_names = None
        self._load()
    
    def _load(self):
        """Load model and metadata"""
        try:
            # Load model
            self.model = joblib.load(self.model_path)
            logger.info(f"Loaded model from {self.model_path}")
            
            # Load metadata
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded metadata from {self.metadata_path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        return self.model.predict(features)
    
    def get_info(self) -> Dict:
        """Get model information"""
        return {
            'model_path': str(self.model_path),
            'metadata': self.metadata,
            'loaded': self.model is not None
        }


class ModelService:
    """Service for managing multiple models"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models: Dict[str, PrecipitationModel] = {}
        self.feature_names: List[str] = []
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all available models"""
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return
        
        # Load feature names
        feature_file = self.models_dir / "feature_names.json"
        if feature_file.exists():
            with open(feature_file, 'r') as f:
                self.feature_names = json.load(f)
        
        # Load each model
        model_types = ['linear_regression', 'random_forest', 'xgboost']
        
        for model_type in model_types:
            model_file = self.models_dir / f"{model_type}_precip_v1.joblib"
            metadata_file = self.models_dir / f"{model_type}_precip_v1_metadata.json"
            
            if model_file.exists() and metadata_file.exists():
                try:
                    self.models[model_type] = PrecipitationModel(
                        str(model_file),
                        str(metadata_file)
                    )
                    logger.info(f"✓ Loaded {model_type} model")
                except Exception as e:
                    logger.error(f"Failed to load {model_type}: {e}")
    
    def predict(
        self,
        model_name: str,
        features: Dict[str, float]
    ) -> Dict:
        """
        Make prediction using specified model
        
        Args:
            model_name: Name of model to use (linear_regression, random_forest, xgboost)
            features: Dictionary of feature values
        
        Returns:
            Dictionary with prediction and metadata
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found. Available: {list(self.models.keys())}")
        
        # Convert features dict to array in correct order
        feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
        feature_array = feature_array.reshape(1, -1)
        
        # Make prediction
        model = self.models[model_name]
        prediction = model.predict(feature_array)[0]
        
        return {
            'model': model_name,
            'prediction_mm': float(prediction),
            'timestamp': datetime.now().isoformat(),
            'model_metadata': model.metadata
        }
    
    def predict_ensemble(self, features: Dict[str, float]) -> Dict:
        """
        Make predictions using all models and return ensemble
        
        Args:
            features: Dictionary of feature values
        
        Returns:
            Dictionary with predictions from all models and ensemble average
        """
        predictions = {}
        
        for model_name in self.models.keys():
            result = self.predict(model_name, features)
            predictions[model_name] = result['prediction_mm']
        
        # Calculate ensemble (simple average)
        ensemble_prediction = np.mean(list(predictions.values()))
        
        return {
            'predictions': predictions,
            'ensemble_mean': float(ensemble_prediction),
            'timestamp': datetime.now().isoformat(),
            'models_used': list(predictions.keys())
        }
    
    def get_models_info(self) -> Dict:
        """Get information about all loaded models"""
        return {
            model_name: model.get_info()
            for model_name, model in self.models.items()
        }
    
    def get_feature_names(self) -> List[str]:
        """Get list of required feature names"""
        return self.feature_names


# Global model service instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create model service singleton"""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
