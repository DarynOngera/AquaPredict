"""
Inference Pipeline for Point-based Predictions
Uses precomputed features from training data or defaults for new locations
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import logging

from app.services.live_data_service import get_live_data_service

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
        Get historical/meteorological features for a location
        Uses live data API when available, falls back to estimates
        
        Args:
            lon: Longitude
            lat: Latitude
            date: Target date
        
        Returns:
            Dictionary with precipitation lags and meteorological features
        """
        # Try to fetch live data from API
        try:
            live_service = get_live_data_service()
            features = live_service.fetch_current_features(lon, lat)
            logger.info(f"Using live data for ({lon:.4f}, {lat:.4f})")
            return features
        except Exception as e:
            logger.warning(f"Live data unavailable, using estimates: {e}")
        
        # Fallback: Try historical data
        if self.historical_data is not None:
            tolerance = 0.1  # degrees
            mask = (
                (np.abs(self.historical_data['longitude'] - lon) < tolerance) &
                (np.abs(self.historical_data['latitude'] - lat) < tolerance)
            )
            
            if mask.any():
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
        
        # Final fallback: location-based estimates
        logger.debug(f"Using location estimates for ({lon:.4f}, {lat:.4f})")
        temp_base = 25.0 - (abs(lat) * 1.2) + (lon - 38) * 0.3
        precip_base = max(0.1, min(1.0 + (lon - 36) * 0.8 + abs(lat) * 0.5, 15.0))
        
        return {
            'lag1_precip': precip_base,
            'lag2_precip': precip_base * 0.85,
            'roll3_precip': precip_base * 0.92,
            'roll7_precip': precip_base * 0.88,
            '2m_air_temp': temp_base,
            'dewpoint_2m': temp_base - 7.0,
            'mslp': 1013.0 - (abs(lat) * 0.8),
            'surface_pressure': 950.0 - (abs(lat) * 3.0),
            'u10': -1.0 + (lon - 38) * 0.4,
            'v10': 0.5 + lat * 0.3,
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
        Make prediction for a single point
        
        Args:
            lon: Longitude
            lat: Latitude  
            date: Target date
            model: Loaded model object
        
        Returns:
            Dictionary with prediction results
        """
        try:
            # Build feature vector
            features = self.build_feature_vector(lon, lat, date)
            
            # Log feature values for debugging
            logger.debug(f"Features: temp={features['2m_air_temp'].values[0]:.1f}°C, "
                        f"precip_lag1={features['lag1_precip'].values[0]:.2f}mm")
            
            # Make prediction
            prediction = model.predict(features.values)[0]
            
            # Log if prediction seems stuck
            if abs(prediction - 0.01) < 0.001:
                logger.warning(f"Low prediction (0.01mm) at ({lon:.2f}, {lat:.2f}) - "
                             f"temp={features['2m_air_temp'].values[0]:.1f}, "
                             f"lag1={features['lag1_precip'].values[0]:.2f}")
            
            return {
                'prediction': float(prediction),
                'location': {'lon': lon, 'lat': lat},
                'date': date.strftime('%Y-%m-%d'),
                'features_used': len(self.feature_names),
                'status': 'success'
            }
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'prediction': 0.0,
                'location': {'lon': lon, 'lat': lat},
                'date': date.strftime('%Y-%m-%d'),
                'features_used': 0,
                'status': 'failed',
                'error': str(e)
            }


# Global pipeline instance
_pipeline: Optional[InferencePipeline] = None


def get_inference_pipeline(historical_data: Optional[pd.DataFrame] = None) -> InferencePipeline:
    """Get or create inference pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = InferencePipeline(historical_data)
    return _pipeline
