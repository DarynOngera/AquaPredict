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
    
    def __init__(self, model_path: str, metadata_path: Optional[str] = None):
        self.model_path = Path(model_path)
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self.model = None
        self.metadata = None
        self.feature_names = None
        self._load()
    
    def _load(self):
        """Load model and metadata"""
        try:
            self.model = joblib.load(self.model_path)
            
            if self.metadata_path and self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            
        except Exception as e:
            raise Exception(f"Failed to load: {e}")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        return self.model.predict(features)
    
    def get_info(self) -> Dict:
        """Get model information"""
        return {
            'model_path': str(self.model_path),
            'loaded': self.model is not None
        }


class ModelService:
    """Service for managing multiple precipitation models"""
    
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            # Look for model_artifacts in project root
            # This file is at: modules/backend/app/services/model_service.py
            # Project root is 4 levels up: ../../../../
            models_dir = Path(__file__).parent.parent.parent.parent.parent / "model_artifacts"
        self.models_dir = Path(models_dir)
        self.models: Dict[str, PrecipitationModel] = {}
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all available models"""
        if not self.models_dir.exists():
            logger.warning(f"Model directory not found: {self.models_dir}")
            return
        
        # Look for model files
        model_files = list(self.models_dir.glob("*.joblib"))
        
        if not model_files:
            logger.warning(f"No models found in {self.models_dir}")
            return
        
        logger.info(f"Loading {len(model_files)} precipitation models...")
        
        for model_file in model_files:
            model_name = model_file.stem.lower()
            metadata_file = model_file.parent / f"{model_file.stem}_metadata.json"
            
            try:
                self.models[model_name] = PrecipitationModel(
                    str(model_file),
                    str(metadata_file) if metadata_file.exists() else None
                )
                logger.info(f"  [OK] {model_name}")
            except Exception as e:
                logger.error(f"  [FAIL] {model_name}: {str(e)[:50]}...")
        
        if self.models:
            logger.info(f"Ready with {len(self.models)} model(s): {', '.join(self.models.keys())}")
        else:
            logger.error("No models loaded successfully")
    
    def get_models_info(self) -> Dict:
        """Get information about all loaded models"""
        return {
            model_name: model.get_info()
            for model_name, model in self.models.items()
        }


# Global model service instance
_model_service: Optional[ModelService] = None


def get_model_service() -> ModelService:
    """Get or create model service singleton"""
    global _model_service
    if _model_service is None:
        _model_service = ModelService()
    return _model_service
