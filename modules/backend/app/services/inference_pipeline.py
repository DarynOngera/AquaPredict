"""
Inference Pipeline for Point-based Predictions
Uses precomputed features from training data or defaults for new locations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InferencePipeline:
    """
    Inference pipeline for precipitation predictions
    
    Flow:
    1. User selects point (lon, lat) and date on map
    2. Build feature vector with lon, lat, temporal features
    3. Use precomputed meteorological features or defaults
    4. Run model prediction
    5. Return result
    
    Note: Models expect precomputed features (sin_day, cos_day, lag1_precip, 
    roll3_precip, ERA5 variables). For unseen coordinates, defaults to zeros.
    """
    
    def __init__(self, historical_data: Optional[pd.DataFrame] = None):
        """
        Initialize inference pipeline
        
        Args:
            historical_data: Optional DataFrame with historical features for known locations
        """
        self.historical_data = historical_data
        self.feature_names = self._get_feature_names()
    
    
    def _get_feature_names(self) -> List[str]:
        """
        Get feature names in the exact order used during training
        
        Returns:
            List of feature names matching your trained models
        """
        return [
            # Spatial features
            'longitude',
            'latitude',
            
            # Temporal features
            'month',
            'dayofyear',
            'sin_day',
            'cos_day',
            
            # Precipitation history
            'lag1_precip',
            'lag2_precip',
            'roll3_precip',
            'roll7_precip',
            
            # Meteorological features
            '2m_air_temp',
            'dewpoint_2m',
            'mslp',
            'surface_pressure',
            'u10',
            'v10',
        ]
    
    def get_temporal_features(self, date: datetime) -> Dict[str, float]:
        """
        Extract temporal features from date (cyclical encoding)
        
        Args:
            date: Target date
        
        Returns:
            Dictionary with month, dayofyear, sin_day, cos_day
        """
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # Cyclical encoding of day of year
        sin_day = np.sin(2 * np.pi * day_of_year / 365.25)
        cos_day = np.cos(2 * np.pi * day_of_year / 365.25)
        
        return {
            'month': month,
            'dayofyear': day_of_year,
            'sin_day': sin_day,
            'cos_day': cos_day
        }
    
    def get_historical_features(
        self,
        lon: float,
        lat: float,
        date: datetime
    ) -> Dict[str, float]:
        """
        Get precomputed features for a location from historical data
        
        Args:
            lon: Longitude
            lat: Latitude
            date: Target date
        
        Returns:
            Dictionary of meteorological features (or zeros for unseen locations)
        """
        # If we have historical data, try to find matching location
        if self.historical_data is not None:
            # Find closest point in historical data (within tolerance)
            tolerance = 0.01  # ~1km
            mask = (
                (np.abs(self.historical_data['longitude'] - lon) < tolerance) &
                (np.abs(self.historical_data['latitude'] - lat) < tolerance)
            )
            
            if mask.any():
                # Get most recent data for this location
                location_data = self.historical_data[mask].iloc[-1]
                
                return {
                    'lag1_precip': location_data.get('lag1_precip', 0.0),
                    'lag2_precip': location_data.get('lag2_precip', 0.0),
                    'roll3_precip': location_data.get('roll3_precip', 0.0),
                    'roll7_precip': location_data.get('roll7_precip', 0.0),
                    '2m_air_temp': location_data.get('2m_air_temp', 0.0),
                    'dewpoint_2m': location_data.get('dewpoint_2m', 0.0),
                    'mslp': location_data.get('mslp', 0.0),
                    'surface_pressure': location_data.get('surface_pressure', 0.0),
                    'u10': location_data.get('u10', 0.0),
                    'v10': location_data.get('v10', 0.0),
                }
        
        # Default to reasonable average values for unseen coordinates
        logger.debug(f"Using regional averages for ({lon:.4f}, {lat:.4f})")
        return {
            # Precipitation lags (mm) - typical daily values
            'lag1_precip': 2.5,
            'lag2_precip': 2.5,
            'roll3_precip': 2.5,
            'roll7_precip': 2.5,
            
            # Meteorological features - typical East Africa values
            '2m_air_temp': 22.0,      # °C - typical temperature
            'dewpoint_2m': 15.0,       # °C - typical dewpoint
            'mslp': 1013.25,           # hPa - sea level pressure
            'surface_pressure': 950.0, # hPa - adjusted for elevation
            'u10': 2.0,                # m/s - typical zonal wind
            'v10': 1.5,                # m/s - typical meridional wind
        }
    
    
    def build_feature_vector(
        self,
        lon: float,
        lat: float,
        date: datetime
    ) -> pd.DataFrame:
        """
        Build complete feature vector for a point
        
        Args:
            lon: Longitude
            lat: Latitude
            date: Target date
        
        Returns:
            DataFrame with features in correct order matching trained models
        """
        # Get temporal features
        temporal_features = self.get_temporal_features(date)
        
        # Get historical/meteorological features (or defaults)
        historical_features = self.get_historical_features(lon, lat, date)
        
        # Combine all features
        all_features = {
            'longitude': lon,
            'latitude': lat,
            **temporal_features,
            **historical_features
        }
        
        # Create DataFrame with features in correct order
        feature_vector = pd.DataFrame([all_features])
        feature_vector = feature_vector[self.feature_names]
        
        return feature_vector
    
    def predict(
        self,
        lon: float,
        lat: float,
        date: datetime,
        model
    ) -> Dict:
        """
        Make prediction for a point
        
        Args:
            lon: Longitude
            lat: Latitude
            date: Target date
            model: Trained model (sklearn/xgboost)
        
        Returns:
            Dictionary with prediction and metadata
        """
        try:
            # Build feature vector
            features = self.build_feature_vector(lon, lat, date)
            
            # Make prediction
            prediction = model.predict(features)[0]
            
            return {
                'prediction': float(prediction),
                'location': {'lon': lon, 'lat': lat},
                'date': date.isoformat(),
                'features_used': len(self.feature_names),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'prediction': None,
                'location': {'lon': lon, 'lat': lat},
                'date': date.isoformat(),
                'error': str(e),
                'status': 'failed'
            }


# Global pipeline instance
_pipeline: Optional[InferencePipeline] = None


def get_inference_pipeline(historical_data: Optional[pd.DataFrame] = None) -> InferencePipeline:
    """Get or create inference pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = InferencePipeline(historical_data)
    return _pipeline
