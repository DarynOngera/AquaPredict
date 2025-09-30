"""Database manager for prediction service."""

import logging
from typing import Optional, Dict, Any, List
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import ServiceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and queries."""
    
    def __init__(self, config: ServiceConfig):
        """
        Initialize Database Manager.
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.engine = None
        self.async_session = None
        self._connected = False
    
    async def connect(self):
        """Connect to database."""
        if not self.config.database_url:
            logger.warning("No database URL configured, skipping connection")
            return
        
        try:
            logger.info("Connecting to database...")
            
            # Create async engine
            self.engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.db_pool_size,
                max_overflow=self.config.db_max_overflow,
                echo=self.config.debug
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._connected = True
            logger.info("✓ Connected to database")
        
        except Exception as e:
            logger.error(f"Error connecting to database: {e}", exc_info=True)
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from database."""
        if self.engine:
            await self.engine.dispose()
            self._connected = False
            logger.info("Disconnected from database")
    
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._connected
    
    async def get_features(
        self,
        lat: float,
        lon: float
    ) -> Optional[Dict[str, float]]:
        """
        Get features for a location from database.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary of features or None
        """
        if not self._connected:
            return None
        
        try:
            async with self.async_session() as session:
                # Query features from database
                # This is a simplified example - adjust based on your schema
                query = text("""
                    SELECT * FROM features
                    WHERE ST_Distance(
                        location,
                        SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL)
                    ) < 1000
                    ORDER BY ST_Distance(
                        location,
                        SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL)
                    )
                    FETCH FIRST 1 ROWS ONLY
                """)
                
                result = await session.execute(query, {"lat": lat, "lon": lon})
                row = result.fetchone()
                
                if row:
                    # Convert row to dictionary
                    return dict(row._mapping)
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting features: {e}", exc_info=True)
            return None
    
    async def get_historical_recharge(
        self,
        lat: float,
        lon: float,
        months: int = 24
    ) -> Optional[np.ndarray]:
        """
        Get historical recharge data for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            months: Number of months of history
            
        Returns:
            Historical recharge array or None
        """
        if not self._connected:
            return None
        
        try:
            async with self.async_session() as session:
                # Query historical data
                query = text("""
                    SELECT recharge_value, date
                    FROM recharge_history
                    WHERE location_id = (
                        SELECT id FROM locations
                        WHERE ST_Distance(
                            geom,
                            SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL)
                        ) < 1000
                        ORDER BY ST_Distance(
                            geom,
                            SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL)
                        )
                        FETCH FIRST 1 ROWS ONLY
                    )
                    ORDER BY date DESC
                    FETCH FIRST :months ROWS ONLY
                """)
                
                result = await session.execute(
                    query,
                    {"lat": lat, "lon": lon, "months": months}
                )
                rows = result.fetchall()
                
                if rows:
                    # Extract values and reverse to chronological order
                    values = [row[0] for row in rows]
                    return np.array(values[::-1])
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting historical recharge: {e}", exc_info=True)
            return None
    
    async def store_prediction(self, prediction: Dict[str, Any]):
        """
        Store prediction in database.
        
        Args:
            prediction: Prediction data
        """
        if not self._connected:
            return
        
        try:
            async with self.async_session() as session:
                # Store prediction
                query = text("""
                    INSERT INTO predictions (
                        lat, lon, prediction, probability, timestamp
                    ) VALUES (
                        :lat, :lon, :prediction, :probability, :timestamp
                    )
                """)
                
                await session.execute(query, {
                    "lat": prediction['location']['lat'],
                    "lon": prediction['location']['lon'],
                    "prediction": prediction['prediction'],
                    "probability": prediction['probability'],
                    "timestamp": prediction['timestamp']
                })
                
                await session.commit()
        
        except Exception as e:
            logger.error(f"Error storing prediction: {e}", exc_info=True)
    
    async def store_forecast(self, forecast: Dict[str, Any]):
        """
        Store forecast in database.
        
        Args:
            forecast: Forecast data
        """
        if not self._connected:
            return
        
        try:
            async with self.async_session() as session:
                # Store forecast
                query = text("""
                    INSERT INTO forecasts (
                        lat, lon, forecast_values, horizon, timestamp
                    ) VALUES (
                        :lat, :lon, :forecast, :horizon, :timestamp
                    )
                """)
                
                await session.execute(query, {
                    "lat": forecast['location']['lat'],
                    "lon": forecast['location']['lon'],
                    "forecast": str(forecast['forecast']),
                    "horizon": forecast['horizon'],
                    "timestamp": forecast['timestamp']
                })
                
                await session.commit()
        
        except Exception as e:
            logger.error(f"Error storing forecast: {e}", exc_info=True)
    
    async def query_spatial_data(
        self,
        bbox: List[float],
        feature: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Query spatial data within bounding box.
        
        Args:
            bbox: Bounding box [west, south, east, north]
            feature: Optional feature name
            
        Returns:
            List of data records
        """
        if not self._connected:
            return None
        
        try:
            async with self.async_session() as session:
                # Query spatial data
                query = text("""
                    SELECT * FROM spatial_data
                    WHERE SDO_FILTER(
                        geom,
                        SDO_GEOMETRY(2003, 4326, NULL,
                            SDO_ELEM_INFO_ARRAY(1, 1003, 3),
                            SDO_ORDINATE_ARRAY(:west, :south, :east, :north)
                        )
                    ) = 'TRUE'
                """)
                
                result = await session.execute(query, {
                    "west": bbox[0],
                    "south": bbox[1],
                    "east": bbox[2],
                    "north": bbox[3]
                })
                
                rows = result.fetchall()
                
                return [dict(row._mapping) for row in rows]
        
        except Exception as e:
            logger.error(f"Error querying spatial data: {e}", exc_info=True)
            return None
