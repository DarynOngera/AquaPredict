"""FastAPI prediction service for AquaPredict."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import logging
from datetime import datetime

from config import ServiceConfig
from models import ModelManager
from oracle_database import OracleADBClient
import sys
sys.path.append('../common')
from oci_storage import DataStorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AquaPredict API",
    description="Geospatial AI platform for aquifer prediction and groundwater forecasting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
config = ServiceConfig()
model_manager = ModelManager(config)
db_client = OracleADBClient()
storage_manager = DataStorageManager()


# Pydantic models
class Location(BaseModel):
    """Geographic location."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class AquiferPredictionRequest(BaseModel):
    """Request for aquifer prediction."""
    location: Location
    features: Optional[Dict[str, float]] = None
    use_cached_features: bool = True


class AquiferPredictionResponse(BaseModel):
    """Response for aquifer prediction."""
    location: Location
    prediction: str
    probability: float
    confidence_interval: Optional[List[float]] = None
    timestamp: datetime


class RechargeForecastRequest(BaseModel):
    """Request for recharge forecast."""
    location: Location
    horizon: int = Field(12, ge=1, le=36, description="Forecast horizon in months")
    historical_data: Optional[List[float]] = None


class RechargeForecastResponse(BaseModel):
    """Response for recharge forecast."""
    location: Location
    forecast: List[float]
    horizon: int
    confidence_intervals: Optional[List[List[float]]] = None
    timestamp: datetime


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions."""
    locations: List[Location]
    prediction_type: str = Field(..., pattern="^(aquifer|depth|recharge)$")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    models_loaded: bool
    database_connected: bool


# Health endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        models_loaded=model_manager.models_loaded,
        database_connected=db_manager.is_connected()
    )


@app.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint."""
    if not model_manager.models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")
    
    if not db_manager.is_connected():
        raise HTTPException(status_code=503, detail="Database not connected")
    
    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow(),
        models_loaded=True,
        database_connected=True
    )


# Prediction endpoints
@app.post("/api/v1/predict/aquifer", response_model=AquiferPredictionResponse)
async def predict_aquifer(request: AquiferPredictionRequest):
    """
    Predict aquifer presence at a location.
    
    Args:
        request: Prediction request with location and optional features
        
    Returns:
        Prediction response with probability and confidence
    """
    try:
        logger.info(f"Aquifer prediction request for location: {request.location}")
        
        # Get or compute features
        if request.use_cached_features and request.features is None:
            features = await db_manager.get_features(
                request.location.lat,
                request.location.lon
            )
        else:
            features = request.features
        
        if features is None:
            raise HTTPException(
                status_code=400,
                detail="Features not provided and not available in cache"
            )
        
        # Convert features to array
        feature_array = np.array([list(features.values())])
        
        # Make prediction
        prediction, probability = model_manager.predict_aquifer(feature_array)
        
        # Get confidence interval (simplified)
        confidence_interval = [
            max(0, probability - 0.1),
            min(1, probability + 0.1)
        ]
        
        response = AquiferPredictionResponse(
            location=request.location,
            prediction="present" if prediction == 1 else "absent",
            probability=float(probability),
            confidence_interval=confidence_interval,
            timestamp=datetime.utcnow()
        )
        
        # Store prediction in database
        await db_manager.store_prediction(response.dict())
        
        return response
    
    except Exception as e:
        logger.error(f"Error in aquifer prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/recharge", response_model=RechargeForecastResponse)
async def forecast_recharge(request: RechargeForecastRequest):
    """
    Forecast groundwater recharge.
    
    Args:
        request: Forecast request with location and horizon
        
    Returns:
        Forecast response with predicted values
    """
    try:
        logger.info(f"Recharge forecast request for location: {request.location}")
        
        # Get historical data
        if request.historical_data is None:
            historical_data = await db_manager.get_historical_recharge(
                request.location.lat,
                request.location.lon
            )
        else:
            historical_data = np.array(request.historical_data)
        
        if historical_data is None or len(historical_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="Historical data not available"
            )
        
        # Make forecast
        forecast = model_manager.forecast_recharge(
            historical_data,
            horizon=request.horizon
        )
        
        # Compute confidence intervals (simplified)
        std_dev = np.std(historical_data) * 0.2
        confidence_intervals = [
            [float(f - std_dev), float(f + std_dev)]
            for f in forecast
        ]
        
        response = RechargeForecastResponse(
            location=request.location,
            forecast=forecast.tolist(),
            horizon=request.horizon,
            confidence_intervals=confidence_intervals,
            timestamp=datetime.utcnow()
        )
        
        # Store forecast in database
        await db_manager.store_forecast(response.dict())
        
        return response
    
    except Exception as e:
        logger.error(f"Error in recharge forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/batch")
async def batch_predict(request: BatchPredictionRequest):
    """
    Batch predictions for multiple locations.
    
    Args:
        request: Batch prediction request
        
    Returns:
        List of predictions
    """
    try:
        logger.info(f"Batch prediction request for {len(request.locations)} locations")
        
        results = []
        
        for location in request.locations:
            if request.prediction_type == "aquifer":
                pred_request = AquiferPredictionRequest(location=location)
                result = await predict_aquifer(pred_request)
            elif request.prediction_type == "recharge":
                forecast_request = RechargeForecastRequest(location=location)
                result = await forecast_recharge(forecast_request)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown prediction type: {request.prediction_type}"
                )
            
            results.append(result)
        
        return {"predictions": results, "count": len(results)}
    
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Model management endpoints
@app.get("/api/v1/models")
async def list_models():
    """List available models."""
    return {
        "models": model_manager.list_models(),
        "timestamp": datetime.utcnow()
    }


@app.post("/api/v1/models/reload")
async def reload_models():
    """Reload models from disk."""
    try:
        model_manager.reload_models()
        return {
            "status": "success",
            "message": "Models reloaded successfully",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error reloading models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Data query endpoints
@app.get("/api/v1/data/features")
async def get_available_features():
    """Get list of available features."""
    return {
        "features": model_manager.get_feature_names(),
        "count": len(model_manager.get_feature_names())
    }


@app.post("/api/v1/data/query")
async def query_spatial_data(
    bbox: List[float] = Field(..., description="Bounding box [west, south, east, north]"),
    feature: Optional[str] = None
):
    """
    Query spatial data within bounding box.
    
    Args:
        bbox: Bounding box coordinates
        feature: Optional feature name to filter
        
    Returns:
        Spatial data within bounding box
    """
    try:
        data = await db_manager.query_spatial_data(bbox, feature)
        return {
            "data": data,
            "bbox": bbox,
            "count": len(data) if data else 0
        }
    except Exception as e:
        logger.error(f"Error querying spatial data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting AquaPredict API...")
    
    # Load models
    model_manager.load_models()
    
    # Connect to database
    await db_manager.connect()
    
    logger.info("AquaPredict API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AquaPredict API...")
    
    # Disconnect from database
    await db_manager.disconnect()
    
    logger.info("AquaPredict API shut down successfully")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug,
        workers=config.api_workers
    )
