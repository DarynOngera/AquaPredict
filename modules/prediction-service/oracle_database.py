"""Oracle Autonomous Database integration with Spatial support."""

import oracledb
import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleADBClient:
    """Oracle Autonomous Database client with Spatial support."""
    
    def __init__(self):
        """Initialize Oracle ADB connection."""
        self.wallet_location = os.getenv("WALLET_LOCATION", "./wallet")
        self.wallet_password = os.getenv("WALLET_PASSWORD")
        self.username = os.getenv("DB_USERNAME", "admin")
        self.password = os.getenv("DB_PASSWORD")
        self.dsn = os.getenv("DB_DSN", "aquapredict_high")
        
        # Initialize Oracle client
        try:
            oracledb.init_oracle_client(config_dir=self.wallet_location)
            logger.info("Oracle client initialized")
        except Exception as e:
            logger.warning(f"Oracle client already initialized or error: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get async Oracle ADB connection."""
        connection = None
        try:
            connection = await oracledb.connect_async(
                user=self.username,
                password=self.password,
                dsn=self.dsn,
                wallet_location=self.wallet_location,
                wallet_password=self.wallet_password
            )
            yield connection
        finally:
            if connection:
                await connection.close()
    
    async def insert_location(
        self,
        lat: float,
        lon: float,
        region: Optional[str] = None
    ) -> int:
        """
        Insert location with spatial geometry.
        
        Returns:
            location_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO locations (latitude, longitude, region, geom)
                VALUES (:lat, :lon, :region,
                    SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon2, :lat2, NULL), NULL, NULL))
                RETURNING location_id INTO :location_id
                """
                
                location_id_var = cursor.var(int)
                
                await cursor.execute(sql, {
                    'lat': lat,
                    'lon': lon,
                    'region': region,
                    'lon2': lon,
                    'lat2': lat,
                    'location_id': location_id_var
                })
                
                await conn.commit()
                
                location_id = location_id_var.getvalue()[0]
                logger.info(f"Inserted location {location_id}: ({lat}, {lon})")
                
                return location_id
    
    async def get_or_create_location(
        self,
        lat: float,
        lon: float,
        region: Optional[str] = None,
        tolerance_km: float = 1.0
    ) -> int:
        """
        Get existing location or create new one.
        Uses spatial query to find nearby locations.
        
        Returns:
            location_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                # Find nearest location within tolerance
                sql = """
                SELECT location_id,
                    SDO_GEOM.SDO_DISTANCE(
                        geom,
                        SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon, :lat, NULL), NULL, NULL),
                        0.005
                    ) as distance_km
                FROM locations
                WHERE SDO_WITHIN_DISTANCE(
                    geom,
                    SDO_GEOMETRY(2001, 4326, SDO_POINT_TYPE(:lon2, :lat2, NULL), NULL, NULL),
                    'distance=' || :tolerance || ' unit=KM'
                ) = 'TRUE'
                ORDER BY distance_km
                FETCH FIRST 1 ROWS ONLY
                """
                
                await cursor.execute(sql, {
                    'lat': lat,
                    'lon': lon,
                    'lat2': lat,
                    'lon2': lon,
                    'tolerance': tolerance_km
                })
                
                row = await cursor.fetchone()
                
                if row:
                    logger.info(f"Found existing location {row[0]} at {row[1]:.2f}km")
                    return row[0]
                else:
                    # Create new location
                    return await self.insert_location(lat, lon, region)
    
    async def insert_features(
        self,
        location_id: int,
        features: Dict[str, float]
    ) -> int:
        """
        Insert feature values for a location.
        
        Returns:
            feature_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO features (
                    location_id, elevation, slope, aspect, twi, tpi,
                    precip_mean, precip_std, temp_mean, temp_std,
                    spi_1, spi_3, spi_6, spi_12,
                    spei_3, spei_6, spei_12,
                    data_quality_score
                ) VALUES (
                    :location_id, :elevation, :slope, :aspect, :twi, :tpi,
                    :precip_mean, :precip_std, :temp_mean, :temp_std,
                    :spi_1, :spi_3, :spi_6, :spi_12,
                    :spei_3, :spei_6, :spei_12,
                    :quality_score
                )
                RETURNING feature_id INTO :feature_id
                """
                
                feature_id_var = cursor.var(int)
                
                await cursor.execute(sql, {
                    'location_id': location_id,
                    'elevation': features.get('elevation'),
                    'slope': features.get('slope'),
                    'aspect': features.get('aspect'),
                    'twi': features.get('twi'),
                    'tpi': features.get('tpi'),
                    'precip_mean': features.get('precip_mean'),
                    'precip_std': features.get('precip_std'),
                    'temp_mean': features.get('temp_mean'),
                    'temp_std': features.get('temp_std'),
                    'spi_1': features.get('spi_1'),
                    'spi_3': features.get('spi_3'),
                    'spi_6': features.get('spi_6'),
                    'spi_12': features.get('spi_12'),
                    'spei_3': features.get('spei_3'),
                    'spei_6': features.get('spei_6'),
                    'spei_12': features.get('spei_12'),
                    'quality_score': features.get('quality_score', 1.0),
                    'feature_id': feature_id_var
                })
                
                await conn.commit()
                
                feature_id = feature_id_var.getvalue()[0]
                logger.info(f"Inserted features {feature_id} for location {location_id}")
                
                return feature_id
    
    async def insert_prediction(
        self,
        location_id: int,
        prediction: str,
        probability: float,
        confidence_lower: float,
        confidence_upper: float,
        model_type: str,
        model_version: str,
        feature_importance: Optional[Dict] = None,
        prediction_time_ms: Optional[float] = None
    ) -> int:
        """
        Insert prediction result.
        
        Returns:
            prediction_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO predictions (
                    location_id, prediction, probability,
                    confidence_lower, confidence_upper,
                    model_type, model_version,
                    feature_importance, prediction_time_ms
                ) VALUES (
                    :location_id, :prediction, :probability,
                    :conf_lower, :conf_upper,
                    :model_type, :model_version,
                    :feature_importance, :pred_time
                )
                RETURNING prediction_id INTO :prediction_id
                """
                
                prediction_id_var = cursor.var(int)
                
                await cursor.execute(sql, {
                    'location_id': location_id,
                    'prediction': prediction,
                    'probability': probability,
                    'conf_lower': confidence_lower,
                    'conf_upper': confidence_upper,
                    'model_type': model_type,
                    'model_version': model_version,
                    'feature_importance': json.dumps(feature_importance) if feature_importance else None,
                    'pred_time': prediction_time_ms,
                    'prediction_id': prediction_id_var
                })
                
                await conn.commit()
                
                prediction_id = prediction_id_var.getvalue()[0]
                logger.info(f"Inserted prediction {prediction_id}")
                
                return prediction_id
    
    async def insert_forecast(
        self,
        location_id: int,
        horizon_months: int,
        forecast_values: List[float],
        confidence_intervals: List[Tuple[float, float]],
        model_type: str,
        model_version: str,
        metrics: Optional[Dict] = None,
        forecast_time_ms: Optional[float] = None
    ) -> int:
        """
        Insert forecast result.
        
        Returns:
            forecast_id
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO forecasts (
                    location_id, horizon_months,
                    forecast_values, confidence_intervals,
                    avg_recharge, max_recharge, min_recharge,
                    model_type, model_version,
                    rmse, mae, r2_score,
                    forecast_time_ms
                ) VALUES (
                    :location_id, :horizon,
                    :forecast_vals, :conf_intervals,
                    :avg_rech, :max_rech, :min_rech,
                    :model_type, :model_version,
                    :rmse, :mae, :r2,
                    :forecast_time
                )
                RETURNING forecast_id INTO :forecast_id
                """
                
                forecast_id_var = cursor.var(int)
                
                await cursor.execute(sql, {
                    'location_id': location_id,
                    'horizon': horizon_months,
                    'forecast_vals': json.dumps(forecast_values),
                    'conf_intervals': json.dumps(confidence_intervals),
                    'avg_rech': sum(forecast_values) / len(forecast_values),
                    'max_rech': max(forecast_values),
                    'min_rech': min(forecast_values),
                    'model_type': model_type,
                    'model_version': model_version,
                    'rmse': metrics.get('rmse') if metrics else None,
                    'mae': metrics.get('mae') if metrics else None,
                    'r2': metrics.get('r2') if metrics else None,
                    'forecast_time': forecast_time_ms,
                    'forecast_id': forecast_id_var
                })
                
                await conn.commit()
                
                forecast_id = forecast_id_var.getvalue()[0]
                logger.info(f"Inserted forecast {forecast_id}")
                
                return forecast_id
    
    async def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """Get recent predictions."""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                SELECT 
                    p.prediction_id,
                    l.latitude,
                    l.longitude,
                    l.region,
                    p.prediction,
                    p.probability,
                    p.model_type,
                    p.predicted_at
                FROM predictions p
                JOIN locations l ON p.location_id = l.location_id
                ORDER BY p.predicted_at DESC
                FETCH FIRST :limit ROWS ONLY
                """
                
                await cursor.execute(sql, {'limit': limit})
                
                rows = await cursor.fetchall()
                
                return [
                    {
                        'prediction_id': row[0],
                        'latitude': float(row[1]),
                        'longitude': float(row[2]),
                        'region': row[3],
                        'prediction': row[4],
                        'probability': float(row[5]),
                        'model_type': row[6],
                        'predicted_at': row[7].isoformat() if row[7] else None
                    }
                    for row in rows
                ]
    
    async def get_spatial_predictions(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> List[Dict]:
        """
        Get predictions within bounding box.
        
        Args:
            bbox: (west, south, east, north)
        """
        west, south, east, north = bbox
        
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                SELECT 
                    p.prediction_id,
                    l.latitude,
                    l.longitude,
                    p.prediction,
                    p.probability
                FROM predictions p
                JOIN locations l ON p.location_id = l.location_id
                WHERE SDO_FILTER(
                    l.geom,
                    SDO_GEOMETRY(2003, 4326, NULL,
                        SDO_ELEM_INFO_ARRAY(1, 1003, 3),
                        SDO_ORDINATE_ARRAY(:west, :south, :east, :north)
                    )
                ) = 'TRUE'
                """
                
                await cursor.execute(sql, {
                    'west': west,
                    'south': south,
                    'east': east,
                    'north': north
                })
                
                rows = await cursor.fetchall()
                
                return [
                    {
                        'prediction_id': row[0],
                        'latitude': float(row[1]),
                        'longitude': float(row[2]),
                        'prediction': row[3],
                        'probability': float(row[4])
                    }
                    for row in rows
                ]
    
    async def log_audit_event(
        self,
        event_type: str,
        event_action: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log audit event."""
        async with self.get_connection() as conn:
            async with conn.cursor() as cursor:
                sql = """
                INSERT INTO audit_log (
                    event_type, event_action,
                    user_id, ip_address, details
                ) VALUES (
                    :event_type, :event_action,
                    :user_id, :ip_address, :details
                )
                """
                
                await cursor.execute(sql, {
                    'event_type': event_type,
                    'event_action': event_action,
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'details': json.dumps(details) if details else None
                })
                
                await conn.commit()
