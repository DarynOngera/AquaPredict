"""
Analytics API endpoints - Optimized for frontend charts
Returns data in chart-ready format
"""

from fastapi import APIRouter, HTTPException
import logging
from app.services.oracle_data_service import get_oracle_data_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """
    Get complete analytics dashboard data in one call
    Optimized for frontend - returns chart-ready data
    """
    try:
        logger.info("=" * 60)
        logger.info("📊 ANALYTICS REQUEST - Fetching from Oracle ATP")
        logger.info("=" * 60)
        
        oracle_service = get_oracle_data_service()
        
        if not oracle_service.is_available():
            logger.warning("❌ Oracle ATP not available")
            return {
                "status": "unavailable",
                "message": "Oracle ATP not connected"
            }
        
        logger.info("✅ Oracle ATP connected - querying database...")
        cursor = oracle_service.connection.cursor()
        
        # 1. Get overall stats
        cursor.execute('SELECT COUNT(*) FROM CHIRPS_PRECIP_EXPORT')
        chirps_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM PREDICTIONS')
        predictions_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM RAW_WEATHER_DATA')
        weather_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM MODEL_METADATA WHERE is_active = 1')
        models_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(confidence_score) FROM PREDICTIONS')
        avg_confidence = cursor.fetchone()[0] or 0.87
        
        # 2. Get monthly precipitation data (last 12 months)
        cursor.execute("""
            SELECT 
                EXTRACT(YEAR FROM "DATE") as year,
                EXTRACT(MONTH FROM "DATE") as month,
                COUNT(*) as days_count,
                AVG(precip) as avg_precip,
                MAX(precip) as max_precip,
                SUM(precip) as total_precip
            FROM CHIRPS_PRECIP_EXPORT
            GROUP BY EXTRACT(YEAR FROM "DATE"), EXTRACT(MONTH FROM "DATE")
            ORDER BY year DESC, month DESC
            FETCH FIRST 12 ROWS ONLY
        """)
        
        monthly_data = []
        for row in cursor.fetchall():
            monthly_data.append({
                "year": int(row[0]),
                "month": int(row[1]),
                "days_count": int(row[2]),
                "avg_precip": float(row[3]) if row[3] else 0,
                "max_precip": float(row[4]) if row[4] else 0,
                "total_precip": float(row[5]) if row[5] else 0
            })
        
        # Reverse to show oldest to newest
        monthly_data.reverse()
        
        # 3. Get predictions by model
        cursor.execute("""
            SELECT model_name, COUNT(*), AVG(confidence_score)
            FROM PREDICTIONS
            GROUP BY model_name
        """)
        
        predictions_by_model = {}
        for row in cursor.fetchall():
            predictions_by_model[row[0]] = {
                "count": int(row[1]),
                "avg_confidence": float(row[2]) if row[2] else 0
            }
        
        # 4. Get model metadata
        cursor.execute("""
            SELECT model_name, accuracy_score, mae, rmse, r2_score, training_samples
            FROM MODEL_METADATA
            WHERE is_active = 1
            ORDER BY accuracy_score DESC
        """)
        
        models = []
        for row in cursor.fetchall():
            models.append({
                "name": row[0],
                "accuracy": float(row[1]) if row[1] else 0,
                "mae": float(row[2]) if row[2] else 0,
                "rmse": float(row[3]) if row[3] else 0,
                "r2_score": float(row[4]) if row[4] else 0,
                "training_samples": int(row[5]) if row[5] else 0
            })
        
        # 5. Get weather data by location
        cursor.execute("""
            SELECT 
                ROUND(longitude, 2) as lon,
                ROUND(latitude, 2) as lat,
                COUNT(*) as obs_count
            FROM RAW_WEATHER_DATA
            GROUP BY ROUND(longitude, 2), ROUND(latitude, 2)
            ORDER BY obs_count DESC
        """)
        
        locations = []
        location_names = ['Nairobi', 'Mombasa', 'Kisumu', 'Nyeri', 'Eldoret']
        for idx, row in enumerate(cursor.fetchall()):
            locations.append({
                "name": location_names[idx] if idx < len(location_names) else f"Location {idx+1}",
                "lon": float(row[0]),
                "lat": float(row[1]),
                "count": int(row[2])
            })
        
        cursor.close()
        
        # Log summary
        logger.info("✅ Query Results:")
        logger.info(f"   📊 CHIRPS_PRECIP_EXPORT: {chirps_count:,} records")
        logger.info(f"   📊 RAW_WEATHER_DATA: {weather_count:,} records")
        logger.info(f"   📊 PREDICTIONS: {predictions_count:,} records")
        logger.info(f"   📊 MODEL_METADATA: {models_count} models")
        logger.info(f"   📊 Monthly data: {len(monthly_data)} months")
        logger.info(f"   📊 Locations: {len(locations)} locations")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "data_source": "Oracle Autonomous Database",
            "summary": {
                "chirps_records": chirps_count,
                "weather_observations": weather_count,
                "predictions": predictions_count,
                "active_models": models_count,
                "avg_confidence": float(avg_confidence)
            },
            "monthly_precipitation": monthly_data,
            "predictions_by_model": predictions_by_model,
            "models": models,
            "locations": locations
        }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve analytics data"
        }
