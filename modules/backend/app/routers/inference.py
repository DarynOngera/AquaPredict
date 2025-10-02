"""
Inference API endpoints for point-based predictions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date as date_type
import logging

from app.services.inference_pipeline import get_inference_pipeline, InferencePipeline
from app.services.model_service import get_model_service, ModelService

router = APIRouter(prefix="/api/inference", tags=["inference"])
logger = logging.getLogger(__name__)


class PointPredictionRequest(BaseModel):
    """Request model for point-based prediction"""
    
    lon: float = Field(..., description="Longitude", ge=-180, le=180, example=36.8219)
    lat: float = Field(..., description="Latitude", ge=-90, le=90, example=-1.2921)
    date: Optional[str] = Field(
        None,
        description="Date in YYYY-MM-DD format (defaults to today)",
        example="2024-01-15"
    )
    model_name: Optional[str] = Field(
        None,
        description="Model to use (linear_regression, random_forest, xgboost). If None, uses ensemble",
        example="random_forest"
    )


class PointPredictionResponse(BaseModel):
    """Response model for point prediction"""
    
    prediction_mm: float = Field(..., description="Predicted precipitation in mm")
    location: dict = Field(..., description="Location coordinates")
    date: str = Field(..., description="Prediction date")
    model: str = Field(..., description="Model used")
    features_extracted: int = Field(..., description="Number of features extracted")
    status: str = Field(..., description="Prediction status")
    timestamp: str = Field(..., description="Prediction timestamp")


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""
    
    points: list[dict] = Field(
        ...,
        description="List of points with lon, lat, and optional date",
        example=[
            {"lon": 36.8219, "lat": -1.2921, "date": "2024-01-15"},
            {"lon": 36.8500, "lat": -1.3000}
        ]
    )
    model_name: Optional[str] = Field(None, description="Model to use for all predictions")


@router.post("/predict", response_model=PointPredictionResponse)
async def predict_point(request: PointPredictionRequest):
    """
    Make precipitation prediction for a single point
    
    This endpoint:
    1. Takes user-selected point (lon, lat) from map
    2. Extracts features from Earth Engine (CHIRPS, ERA5, SRTM)
    3. Builds feature vector matching training format
    4. Runs model prediction
    5. Returns predicted precipitation
    
    **Example Usage:**
    ```python
    import requests
    
    response = requests.post(
        'http://92.5.94.60/api/inference/predict',
        json={
            'lon': 36.8219,
            'lat': -1.2921,
            'date': '2024-01-15',
            'model_name': 'random_forest'
        }
    )
    
    print(response.json())
    # {
    #   "prediction_mm": 12.5,
    #   "location": {"lon": 36.8219, "lat": -1.2921},
    #   "date": "2024-01-15",
    #   "model": "random_forest",
    #   ...
    # }
    ```
    """
    try:
        pipeline = get_inference_pipeline()
        model_service = get_model_service()
        
        # Check if any models are loaded
        if not model_service.models:
            raise HTTPException(
                status_code=503,
                detail="No models loaded. Please place .joblib files in model_artifacts/ directory"
            )
        
        # Parse date
        if request.date:
            try:
                pred_date = datetime.strptime(request.date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            pred_date = datetime.now()
        
        # Get model
        if request.model_name:
            if request.model_name not in model_service.models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{request.model_name}' not found. Available: {list(model_service.models.keys())}"
                )
            model = model_service.models[request.model_name].model
            model_name = request.model_name
        else:
            # Use random forest as default, or first available model
            if 'random_forest' in model_service.models:
                model = model_service.models['random_forest'].model
                model_name = 'random_forest'
            else:
                # Use first available model
                model_name = list(model_service.models.keys())[0]
                model = model_service.models[model_name].model
        
        logger.info(f"Predicting precipitation at ({request.lon:.4f}, {request.lat:.4f}) for {pred_date.date()} using {model_name}")
        
        # Make prediction
        result = pipeline.predict(
            lon=request.lon,
            lat=request.lat,
            date=pred_date,
            model=model
        )
        
        if result['status'] == 'failed':
            logger.error(f"Prediction failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Prediction failed: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Result: {result['prediction']:.2f}mm (model: {model_name})")
        
        return PointPredictionResponse(
            prediction_mm=result['prediction'],
            location=result['location'],
            date=result['date'],
            model=model_name,
            features_extracted=result['features_used'],
            status=result['status'],
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@router.post("/predict/batch")
async def predict_batch(request: BatchPredictionRequest):
    """
    Make predictions for multiple points
    
    Useful for:
    - Generating prediction maps
    - Batch processing multiple locations
    - Time series predictions
    
    **Example:**
    ```python
    response = requests.post(
        'http://92.5.94.60/api/inference/predict/batch',
        json={
            'points': [
                {'lon': 36.8219, 'lat': -1.2921, 'date': '2024-01-15'},
                {'lon': 36.8500, 'lat': -1.3000, 'date': '2024-01-15'},
                {'lon': 36.8700, 'lat': -1.3200}
            ],
            'model_name': 'xgboost'
        }
    )
    ```
    """
    try:
        # Get services
        pipeline = get_inference_pipeline()
        model_service = get_model_service()
        
        # Get model
        if request.model_name:
            if request.model_name not in model_service.models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{request.model_name}' not found"
                )
            model = model_service.models[request.model_name].model
            model_name = request.model_name
        else:
            model = model_service.models['random_forest'].model
            model_name = 'random_forest'
        
        predictions = []
        
        for point in request.points:
            # Parse date
            if 'date' in point and point['date']:
                pred_date = datetime.strptime(point['date'], '%Y-%m-%d')
            else:
                pred_date = datetime.now()
            
            # Make prediction
            result = pipeline.predict(
                lon=point['lon'],
                lat=point['lat'],
                date=pred_date,
                model=model
            )
            
            predictions.append({
                'location': result['location'],
                'date': result['date'],
                'prediction_mm': result.get('prediction'),
                'status': result['status'],
                'error': result.get('error')
            })
        
        return {
            'predictions': predictions,
            'model': model_name,
            'count': len(predictions),
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch prediction error: {str(e)}"
        )


@router.get("/models")
async def get_models_status():
    """
    Get status of loaded models
    """
    model_service = get_model_service()
    return {
        'models_loaded': len(model_service.models),
        'available_models': list(model_service.models.keys()),
        'models_dir': str(model_service.models_dir),
        'models_info': model_service.get_models_info()
    }


@router.get("/features")
async def get_feature_info():
    """
    Get information about features used in predictions
    
    Returns the list of features extracted from Earth Engine
    and used by the models.
    """
    pipeline = get_inference_pipeline()
    return {
        'feature_names': pipeline.feature_names,
        'feature_count': len(pipeline.feature_names),
        'feature_sources': {
            'Spatial': 'longitude, latitude',
            'Temporal': 'month, dayofyear, sin_day, cos_day',
            'Precipitation': 'lag1_precip, lag2_precip, roll3_precip, roll7_precip',
            'Meteorological': '2m_air_temp, dewpoint_2m, mslp, surface_pressure, u10, v10'
        },
        'description': 'Features are built from location and date, with meteorological defaults for unseen locations'
    }


@router.post("/extract-features")
async def extract_features_only(
    lon: float,
    lat: float,
    date: Optional[str] = None
):
    """
    Extract features for a point without making prediction
    
    Useful for:
    - Debugging feature extraction
    - Understanding what data is available
    - Feature analysis
    """
    try:
        # Get pipeline
        pipeline = get_inference_pipeline()
        
        # Parse date
        if date:
            pred_date = datetime.strptime(date, '%Y-%m-%d')
        else:
            pred_date = datetime.now()
        
        # Extract features
        features = pipeline.build_feature_vector(lon, lat, pred_date)
        
        return {
            'location': {'lon': lon, 'lat': lat},
            'date': pred_date.isoformat(),
            'features': features.to_dict(orient='records')[0],
            'feature_count': len(features.columns)
        }
    
    except Exception as e:
        logger.error(f"Feature extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Feature extraction error: {str(e)}"
        )
