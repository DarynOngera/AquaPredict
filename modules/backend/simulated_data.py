"""
Simulated Data Provider
Provides realistic fallback data when GEE is unavailable.
"""

import numpy as np
import logging
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimulatedDataProvider:
    """Provides simulated data based on hydrogeological principles."""
    
    def __init__(self):
        # Kenya regional characteristics
        self.kenya_bounds = {
            'west': 33.9, 'south': -4.7,
            'east': 41.9, 'north': 5.5
        }
        
        # Regional precipitation patterns (mm/year)
        self.regional_precip = {
            'western': 1800,  # High rainfall
            'central': 1000,  # Moderate
            'eastern': 600,   # Semi-arid
            'coastal': 1200,  # Coastal
            'northern': 400   # Arid
        }
    
    def generate_features(self, lat: float, lon: float) -> Dict[str, float]:
        """
        Generate realistic features for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary of features
        """
        # Determine region
        region = self._determine_region(lat, lon)
        
        # Generate elevation (Kenya: 0-5199m, Mt Kenya)
        # Higher in central/western, lower in coastal/northern
        if region == 'central':
            elevation = np.random.uniform(1200, 2500)
        elif region == 'western':
            elevation = np.random.uniform(1000, 2000)
        elif region == 'coastal':
            elevation = np.random.uniform(0, 500)
        elif region == 'northern':
            elevation = np.random.uniform(300, 1000)
        else:  # eastern
            elevation = np.random.uniform(500, 1500)
        
        # Generate slope (degrees)
        # Steeper in highlands, flatter in lowlands
        if elevation > 1500:
            slope = np.random.uniform(5, 25)
        else:
            slope = np.random.uniform(0, 10)
        
        # Generate precipitation
        base_precip = self.regional_precip.get(region, 800)
        precip_mean = base_precip * np.random.uniform(0.8, 1.2)
        
        # Generate temperature (°C)
        # Cooler at higher elevations
        base_temp = 25 - (elevation / 1000) * 6  # Lapse rate ~6°C/1000m
        temp_mean = base_temp + np.random.uniform(-2, 2)
        
        # Generate NDVI (0-1)
        # Higher in wetter regions
        if precip_mean > 1200:
            ndvi = np.random.uniform(0.6, 0.85)
        elif precip_mean > 800:
            ndvi = np.random.uniform(0.4, 0.7)
        else:
            ndvi = np.random.uniform(0.2, 0.5)
        
        # Calculate TWI (Topographic Wetness Index)
        # Higher in flatter, wetter areas
        slope_factor = max(0.1, slope / 30)
        precip_factor = precip_mean / 1000
        twi = (10 * precip_factor) / slope_factor
        twi = np.clip(twi, 2, 20)
        
        # Generate land cover (ESA WorldCover classes)
        # 10=Tree cover, 20=Shrubland, 30=Grassland, 40=Cropland, 50=Built-up
        # 60=Bare/sparse, 70=Snow/ice, 80=Water, 90=Wetland, 95=Mangroves, 100=Moss
        if ndvi > 0.7:
            landcover = np.random.choice([10, 40, 90], p=[0.5, 0.3, 0.2])
        elif ndvi > 0.4:
            landcover = np.random.choice([20, 30, 40], p=[0.3, 0.4, 0.3])
        else:
            landcover = np.random.choice([30, 60], p=[0.6, 0.4])
        
        features = {
            'elevation': round(elevation, 1),
            'slope': round(slope, 2),
            'twi': round(twi, 2),
            'precip_mean': round(precip_mean, 1),
            'temp_mean': round(temp_mean, 1),
            'ndvi': round(ndvi, 3),
            'landcover': float(landcover)
        }
        
        logger.info(f"Generated simulated features for ({lat}, {lon}): {features}")
        return features
    
    def generate_climate_timeseries(
        self,
        lat: float,
        lon: float,
        months: int = 24
    ) -> Dict[str, List[float]]:
        """
        Generate realistic climate time series.
        
        Args:
            lat: Latitude
            lon: Longitude
            months: Number of months
            
        Returns:
            Dictionary with precipitation and temperature time series
        """
        region = self._determine_region(lat, lon)
        base_precip = self.regional_precip.get(region, 800) / 12  # Monthly
        
        # Kenya bimodal rainfall pattern
        seasonal_patterns = {
            1: 0.4, 2: 0.5, 3: 1.8, 4: 2.2, 5: 1.5,  # Long rains
            6: 0.6, 7: 0.5, 8: 0.5, 9: 0.6,
            10: 1.4, 11: 1.8, 12: 1.2  # Short rains
        }
        
        precipitation = []
        temperature = []
        
        current_date = datetime.now()
        
        for i in range(months):
            month_date = current_date - timedelta(days=30 * (months - i))
            month_num = month_date.month
            
            # Generate precipitation with seasonality and noise
            seasonal_factor = seasonal_patterns[month_num]
            monthly_precip = base_precip * seasonal_factor * np.random.uniform(0.7, 1.3)
            precipitation.append(round(monthly_precip, 1))
            
            # Generate temperature with seasonality
            # Warmer in Jan-Mar, cooler in Jun-Aug
            temp_seasonal = 22 + 3 * np.sin((month_num - 3) * np.pi / 6)
            temp = temp_seasonal + np.random.uniform(-1, 1)
            temperature.append(round(temp, 1))
        
        return {
            'precipitation': precipitation,
            'temperature': temperature,
            'months': months
        }
    
    def _determine_region(self, lat: float, lon: float) -> str:
        """Determine which region of Kenya a location is in."""
        # Simplified regional classification
        if lon < 35.5:
            return 'western'
        elif lon > 39.5:
            return 'coastal'
        elif lat > 0.5:
            return 'northern'
        elif 36.5 <= lon <= 37.5 and -1.5 <= lat <= 0.5:
            return 'central'
        else:
            return 'eastern'
