"""
AquaPredict Backend API
Comprehensive backend service with GEE integration, model inference, settings, and export functionality.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
import numpy as np
import logging
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import io
import csv

from gee_service import GEEService
from model_service import ModelService
from settings_service import SettingsService
from export_service import ExportService
from simulated_data import SimulatedDataProvider

# Import inference router
from app.routers import inference

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AquaPredict Backend API",
    description="Comprehensive geospatial AI platform for aquifer prediction and groundwater management",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include inference router
app.include_router(inference.router)

# Initialize services
gee_service = GEEService()
model_service = ModelService()
settings_service = SettingsService()
export_service = ExportService()
simulated_data = SimulatedDataProvider()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class Location(BaseModel):
    """Geographic location."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")

    @validator('lat', 'lon')
    def round_coordinates(cls, v):
        return round(v, 6)


class PredictionRequest(BaseModel):
    """Request for aquifer prediction."""
    location: Location
    use_real_data: bool = Field(True, description="Use real GEE data if available")
    features: Optional[Dict[str, float]] = None


class PredictionResponse(BaseModel):
    """Response for aquifer prediction."""
    location: Location
    prediction: str
    probability: float
    confidence_interval: Optional[List[float]] = None
    depth_bands: List[Dict[str, Any]]
    geological_formation: str
    estimated_porosity: str
    recommended_drilling_depth: str
    data_source: Literal["gee", "simulated"]
    timestamp: str
    features_used: Dict[str, float]


class ForecastRequest(BaseModel):
    """Request for recharge forecast."""
    location: Location
    horizon: int = Field(12, ge=1, le=36, description="Forecast horizon in months")
    use_real_data: bool = Field(True, description="Use real GEE data if available")


class ForecastResponse(BaseModel):
    """Response for recharge forecast."""
    location: Location
    forecast: List[Dict[str, Any]]
    summary: Dict[str, Any]
    data_source: Literal["gee", "simulated"]
    timestamp: str


class ExtractionRecommendationRequest(BaseModel):
    """Request for extraction recommendations."""
    location: Location
    use_real_data: bool = Field(True, description="Use real GEE data if available")


class SettingsUpdate(BaseModel):
    """Settings update request."""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    default_region: Optional[str] = None
    default_location: Optional[Location] = None
    map_base_layer: Optional[str] = None
    map_zoom: Optional[int] = None
    show_prediction_markers: Optional[bool] = None
    auto_center: Optional[bool] = None
    aquifer_model: Optional[str] = None
    recharge_model: Optional[str] = None
    confidence_threshold: Optional[float] = None
    cache_predictions: Optional[bool] = None


class ExportRequest(BaseModel):
    """Data export request."""
    export_type: Literal["prediction", "forecast", "history", "report"]
    format: Literal["csv", "json", "geojson", "pdf"]
    data: Dict[str, Any]
    include_metadata: bool = True


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "AquaPredict Backend API",
        "version": "2.0.0",
        "status": "operational",
        "capabilities": [
            "Aquifer Prediction (GEE + ML)",
            "Recharge Forecasting",
            "Sustainable Extraction Recommendations",
            "Settings Management",
            "Data Export (CSV, JSON, GeoJSON, PDF)",
            "Simulated Data Fallbacks"
        ],
        "data_sources": {
            "gee": gee_service.is_available(),
            "models": model_service.models_loaded
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "gee": gee_service.is_available(),
            "models": model_service.models_loaded,
            "settings": True,
            "export": True
        }
    }


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/predict/aquifer", response_model=PredictionResponse)
async def predict_aquifer(request: PredictionRequest):
    """
    Predict aquifer presence at a location using GEE data and ML models.
    Falls back to simulated data if GEE unavailable.
    """
    try:
        logger.info(f"Aquifer prediction request: {request.location}")
        
        # Get features from GEE or simulated data
        if request.features:
            features = request.features
            data_source = "provided"
        elif request.use_real_data and gee_service.is_available():
            try:
                features = await gee_service.get_features(
                    request.location.lat,
                    request.location.lon
                )
                data_source = "gee"
            except Exception as e:
                logger.warning(f"GEE fetch failed, using simulated: {e}")
                features = simulated_data.generate_features(
                    request.location.lat,
                    request.location.lon
                )
                data_source = "simulated"
        else:
            features = simulated_data.generate_features(
                request.location.lat,
                request.location.lon
            )
            data_source = "simulated"
        
        # Make prediction
        prediction_result = model_service.predict_aquifer(features)
        
        return PredictionResponse(
            location=request.location,
            prediction=prediction_result["prediction"],
            probability=prediction_result["probability"],
            confidence_interval=prediction_result["confidence_interval"],
            depth_bands=prediction_result["depth_bands"],
            geological_formation=prediction_result["geological_formation"],
            estimated_porosity=prediction_result["estimated_porosity"],
            recommended_drilling_depth=prediction_result["recommended_drilling_depth"],
            data_source=data_source,
            timestamp=datetime.utcnow().isoformat(),
            features_used=features
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/recharge", response_model=ForecastResponse)
async def forecast_recharge(request: ForecastRequest):
    """
    Forecast groundwater recharge using GEE climate data and LSTM models.
    Falls back to simulated data if GEE unavailable.
    """
    try:
        logger.info(f"Recharge forecast request: {request.location}")
        
        # Get historical climate data
        if request.use_real_data and gee_service.is_available():
            try:
                climate_data = await gee_service.get_climate_timeseries(
                    request.location.lat,
                    request.location.lon,
                    months_back=24
                )
                data_source = "gee"
            except Exception as e:
                logger.warning(f"GEE fetch failed, using simulated: {e}")
                climate_data = simulated_data.generate_climate_timeseries(
                    request.location.lat,
                    request.location.lon,
                    months=24
                )
                data_source = "simulated"
        else:
            climate_data = simulated_data.generate_climate_timeseries(
                request.location.lat,
                request.location.lon,
                months=24
            )
            data_source = "simulated"
        
        # Make forecast
        forecast_result = model_service.forecast_recharge(
            climate_data,
            horizon=request.horizon
        )
        
        return ForecastResponse(
            location=request.location,
            forecast=forecast_result["forecast"],
            summary=forecast_result["summary"],
            data_source=data_source,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Forecast error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/recommendations/extraction")
async def get_extraction_recommendations(request: ExtractionRecommendationRequest):
    """Get sustainable extraction recommendations."""
    try:
        # Get features
        if request.use_real_data and gee_service.is_available():
            try:
                features = await gee_service.get_features(
                    request.location.lat,
                    request.location.lon
                )
            except:
                features = simulated_data.generate_features(
                    request.location.lat,
                    request.location.lon
                )
        else:
            features = simulated_data.generate_features(
                request.location.lat,
                request.location.lon
            )
        
        # Calculate recommendations
        recommendations = model_service.calculate_extraction_recommendations(features)
        
        return {
            "location": request.location.dict(),
            **recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Recommendations error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SETTINGS ENDPOINTS
# ============================================================================

@app.get("/api/v1/settings")
async def get_settings():
    """Get current user settings."""
    return settings_service.get_settings()


@app.put("/api/v1/settings")
async def update_settings(settings: SettingsUpdate):
    """Update user settings."""
    try:
        updated = settings_service.update_settings(settings.dict(exclude_none=True))
        return {
            "status": "success",
            "settings": updated,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Settings update error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/settings/reset")
async def reset_settings():
    """Reset settings to defaults."""
    settings_service.reset_to_defaults()
    return {
        "status": "success",
        "message": "Settings reset to defaults",
        "settings": settings_service.get_settings()
    }


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.post("/api/v1/export")
async def export_data(request: ExportRequest):
    """Export data in various formats."""
    try:
        logger.info(f"Export request: {request.export_type} as {request.format}")
        
        if request.format == "csv":
            content = export_service.export_csv(request.data, request.export_type)
            media_type = "text/csv"
            filename = f"aquapredict_{request.export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        elif request.format == "json":
            content = export_service.export_json(request.data, request.include_metadata)
            media_type = "application/json"
            filename = f"aquapredict_{request.export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        elif request.format == "geojson":
            content = export_service.export_geojson(request.data)
            media_type = "application/geo+json"
            filename = f"aquapredict_{request.export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.geojson"
        
        elif request.format == "pdf":
            content = export_service.export_pdf(request.data, request.export_type)
            media_type = "application/pdf"
            filename = f"aquapredict_{request.export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return StreamingResponse(
            io.BytesIO(content.encode() if isinstance(content, str) else content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/models")
async def list_models():
    """List available models and their status."""
    return model_service.get_model_info()


@app.post("/api/v1/models/reload")
async def reload_models():
    """Reload models from disk."""
    try:
        model_service.reload_models()
        return {
            "status": "success",
            "message": "Models reloaded successfully",
            "models": model_service.get_model_info()
        }
    except Exception as e:
        logger.error(f"Model reload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/models/upload")
async def upload_model(
    model_type: str = Query(..., description="Model type: aquifer or recharge"),
    model_file: bytes = None
):
    """Upload a new model (e.g., from Colab training)."""
    try:
        model_service.save_model(model_type, model_file)
        return {
            "status": "success",
            "message": f"{model_type} model uploaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Model upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DATA SOURCE ENDPOINTS
# ============================================================================

@app.get("/api/v1/data/sources")
async def get_data_sources():
    """Get status of all data sources with preview configurations."""
    return {
        "gee": {
            "available": gee_service.is_available(),
            "datasets": [
                {
                    "id": "chirps",
                    "name": "CHIRPS - Precipitation",
                    "collection": "UCSB-CHG/CHIRPS/DAILY",
                    "description": "Climate Hazards Group InfraRed Precipitation with Station data",
                    "band": "precipitation",
                    "unit": "mm/day",
                    "temporal_resolution": "Daily",
                    "spatial_resolution": "5km",
                    "visualization": {
                        "min": 1,
                        "max": 17,
                        "palette": ["001137", "0aab1e", "e7eb05", "ff4a2d", "e90000"]
                    },
                    "default_center": {"lat": 7.71, "lon": 17.93, "zoom": 2}
                },
                {
                    "id": "era5",
                    "name": "ERA5 - Temperature",
                    "collection": "ECMWF/ERA5/MONTHLY",
                    "description": "ECMWF Reanalysis v5 - Temperature data",
                    "band": "mean_2m_air_temperature",
                    "unit": "Kelvin",
                    "temporal_resolution": "Monthly",
                    "spatial_resolution": "27.8km",
                    "visualization": {
                        "min": 250,
                        "max": 320,
                        "palette": ["000080", "0000ff", "00ffff", "ffff00", "ff0000", "800000"]
                    },
                    "default_center": {"lat": 0.0, "lon": 37.9, "zoom": 5}
                },
                {
                    "id": "srtm",
                    "name": "SRTM - Elevation",
                    "collection": "USGS/SRTMGL1_003",
                    "description": "Shuttle Radar Topography Mission - Digital Elevation Model",
                    "band": "elevation",
                    "unit": "meters",
                    "temporal_resolution": "Static",
                    "spatial_resolution": "30m",
                    "visualization": {
                        "min": 0,
                        "max": 3000,
                        "palette": ["006633", "E5FFCC", "662A00", "D8D8D8", "F5F5F5"]
                    },
                    "default_center": {"lat": 0.0236, "lon": 37.9062, "zoom": 6}
                },
                {
                    "id": "sentinel2",
                    "name": "Sentinel-2 - NDVI",
                    "collection": "COPERNICUS/S2_SR",
                    "description": "Sentinel-2 Surface Reflectance - Vegetation Index",
                    "band": "NDVI",
                    "unit": "index",
                    "temporal_resolution": "5 days",
                    "spatial_resolution": "10m",
                    "visualization": {
                        "min": -1,
                        "max": 1,
                        "palette": ["brown", "yellow", "green", "darkgreen"]
                    },
                    "default_center": {"lat": 0.0236, "lon": 37.9062, "zoom": 8}
                },
                {
                    "id": "worldcover",
                    "name": "ESA WorldCover - Land Cover",
                    "collection": "ESA/WorldCover/v100",
                    "description": "ESA WorldCover 10m Land Cover Classification",
                    "band": "Map",
                    "unit": "class",
                    "temporal_resolution": "Annual",
                    "spatial_resolution": "10m",
                    "visualization": {
                        "min": 10,
                        "max": 100,
                        "palette": ["006400", "ffbb22", "ffff4c", "f096ff", "fa0000", "b4b4b4", "f0f0f0", "0064c8", "0096a0", "00cf75", "fae6a0"]
                    },
                    "default_center": {"lat": 0.0236, "lon": 37.9062, "zoom": 8}
                }
            ]
        },
        "simulated": {
            "available": True,
            "description": "Fallback simulated data based on hydrogeological principles"
        },
        "models": {
            "loaded": model_service.models_loaded,
            "count": len(model_service.get_model_info())
        }
    }


@app.get("/api/v1/data/features")
async def get_feature_info():
    """Get information about available features."""
    return {
        "features": [
            {"name": "elevation", "unit": "meters", "source": "SRTM"},
            {"name": "slope", "unit": "degrees", "source": "Derived from SRTM"},
            {"name": "twi", "unit": "index", "source": "Calculated"},
            {"name": "precip_mean", "unit": "mm/year", "source": "CHIRPS"},
            {"name": "temp_mean", "unit": "°C", "source": "ERA5"},
            {"name": "ndvi", "unit": "index", "source": "Sentinel-2"},
            {"name": "landcover", "unit": "class", "source": "ESA WorldCover"}
        ]
    }


@app.get("/api/v1/data/preview/{dataset_id}")
async def get_dataset_preview(
    dataset_id: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    region: Optional[str] = Query("kenya", description="Region: kenya, nairobi, mombasa, custom"),
    west: Optional[float] = Query(None, description="West longitude for custom region"),
    south: Optional[float] = Query(None, description="South latitude for custom region"),
    east: Optional[float] = Query(None, description="East longitude for custom region"),
    north: Optional[float] = Query(None, description="North latitude for custom region")
):
    """
    Get detailed dataset preview with regional statistics over a date range.
    
    Args:
        dataset_id: Dataset identifier (chirps, era5, srtm, etc.)
        start_date: Start date for temporal datasets
        end_date: End date for temporal datasets
        region: Predefined region or 'custom'
        west, south, east, north: Bounding box for custom region
    """
    try:
        if not gee_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Google Earth Engine not available. Please configure GEE credentials."
            )
        
        # Define region bounds
        regions = {
            'kenya': [33.9, -4.7, 41.9, 5.5],
            'nairobi': [36.6, -1.5, 37.1, -1.1],
            'mombasa': [39.5, -4.2, 39.8, -3.9],
            'mt_kenya': [37.0, -0.5, 37.5, 0.0],
            'turkana': [35.0, 2.5, 36.5, 4.5]
        }
        
        if region == 'custom' and all([west, south, east, north]):
            bbox = [west, south, east, north]
        else:
            bbox = regions.get(region, regions['kenya'])
        
        # Get regional statistics over date range
        stats = await gee_service.get_regional_stats(dataset_id, bbox, start_date, end_date)
        
        # Try to get tile URL for visualization (optional)
        tile_url = None
        try:
            tile_url = await gee_service.get_tile_url(dataset_id, start_date, end_date)
        except Exception as tile_error:
            logger.warning(f"Could not generate tile URL: {tile_error}")
        
        return {
            "dataset_id": dataset_id,
            "tile_url": tile_url,
            "region": region,
            "bbox": bbox,
            "statistics": stats,
            "start_date": stats.get('date_range', [start_date, end_date])[0] if stats.get('date_range') else start_date,
            "end_date": stats.get('date_range', [start_date, end_date])[1] if stats.get('date_range') else end_date,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Dataset preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 60)
    logger.info("Starting AquaPredict Backend API")
    logger.info("=" * 60)
    
    # Initialize GEE
    try:
        await gee_service.initialize()
        logger.info("Google Earth Engine initialized")
    except Exception as e:
        logger.warning("GEE unavailable - using simulated data")
    
    logger.info("=" * 60)
    logger.info("AquaPredict API ready")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AquaPredict Backend API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
