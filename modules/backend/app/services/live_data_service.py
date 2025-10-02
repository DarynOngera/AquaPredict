"""
Live Data Service
Fetches real-time meteorological data from public APIs
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class LiveDataService:
    """Service to fetch live meteorological data"""
    
    def __init__(self):
        # Open-Meteo API (free, no API key needed)
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.archive_url = "https://archive-api.open-meteo.com/v1/archive"
    
    def fetch_current_features(self, lon: float, lat: float) -> Dict[str, float]:
        """
        Fetch current meteorological features for a location
        
        Args:
            lon: Longitude
            lat: Latitude
        
        Returns:
            Dictionary with meteorological features
        """
        try:
            # Get current date and past week for lag features
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            
            # Fetch historical data for precipitation lags
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': week_ago.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d'),
                'daily': 'precipitation_sum,temperature_2m_mean,surface_pressure_mean',
                'timezone': 'auto'
            }
            
            logger.info(f"Fetching live data for ({lon:.4f}, {lat:.4f})")
            response = requests.get(self.archive_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_features(data)
            else:
                logger.warning(f"API returned {response.status_code}, using estimates")
                return self._get_estimated_features(lon, lat)
        
        except Exception as e:
            logger.warning(f"Failed to fetch live data: {e}, using estimates")
            return self._get_estimated_features(lon, lat)
    
    def _parse_features(self, data: dict) -> Dict[str, float]:
        """Parse API response into model features"""
        try:
            daily = data.get('daily', {})
            precip = daily.get('precipitation_sum', [])
            temp = daily.get('temperature_2m_mean', [])
            pressure = daily.get('surface_pressure_mean', [])
            
            # Get recent values (last 7 days)
            if len(precip) >= 7:
                lag1_precip = precip[-1] if precip[-1] is not None else 0.0
                lag2_precip = precip[-2] if precip[-2] is not None else 0.0
                roll3_precip = np.mean([p for p in precip[-3:] if p is not None])
                roll7_precip = np.mean([p for p in precip[-7:] if p is not None])
            else:
                lag1_precip = lag2_precip = roll3_precip = roll7_precip = 0.0
            
            # Get current temperature and pressure
            current_temp = temp[-1] if temp and temp[-1] is not None else 22.0
            current_pressure = pressure[-1] if pressure and pressure[-1] is not None else 1013.0
            
            # Estimate other features
            dewpoint = current_temp - 7.0  # Typical dewpoint depression
            surface_pressure = current_pressure - 60.0  # Adjust for elevation
            
            logger.info(f"Live data: temp={current_temp:.1f}°C, precip_lag1={lag1_precip:.2f}mm")
            
            return {
                'lag1_precip': float(lag1_precip),
                'lag2_precip': float(lag2_precip),
                'roll3_precip': float(roll3_precip),
                'roll7_precip': float(roll7_precip),
                '2m_air_temp': float(current_temp),
                'dewpoint_2m': float(dewpoint),
                'mslp': float(current_pressure),
                'surface_pressure': float(surface_pressure),
                'u10': 0.0,  # Wind data not in free tier
                'v10': 0.0
            }
        
        except Exception as e:
            logger.error(f"Error parsing API data: {e}")
            raise
    
    def _get_estimated_features(self, lon: float, lat: float) -> Dict[str, float]:
        """Fallback: estimate features based on location"""
        # Temperature: varies with latitude
        temp_base = 25.0 - (abs(lat) * 1.2)
        temp_base += (lon - 38) * 0.3
        
        # Precipitation: coastal vs inland
        precip_base = 1.0 + (lon - 36) * 0.8
        precip_base += abs(lat - 0) * 0.5
        precip_base = max(0.1, min(precip_base, 15.0))
        
        # Pressure
        pressure_base = 1013.0 - (abs(lat) * 0.8)
        surface_pressure = 950.0 - (abs(lat) * 3.0)
        
        return {
            'lag1_precip': precip_base,
            'lag2_precip': precip_base * 0.85,
            'roll3_precip': precip_base * 0.92,
            'roll7_precip': precip_base * 0.88,
            '2m_air_temp': temp_base,
            'dewpoint_2m': temp_base - 7.0,
            'mslp': pressure_base,
            'surface_pressure': surface_pressure,
            'u10': -1.0 + (lon - 38) * 0.4,
            'v10': 0.5 + lat * 0.3,
        }


# Global instance
_live_data_service: Optional[LiveDataService] = None


def get_live_data_service() -> LiveDataService:
    """Get or create live data service singleton"""
    global _live_data_service
    if _live_data_service is None:
        _live_data_service = LiveDataService()
    return _live_data_service
