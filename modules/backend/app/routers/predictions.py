"""
Prediction API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

from app.services.model_service import get_model_service, ModelService

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


class PredictionRequest(BaseModel):
    """Request model for precipitation prediction"""
    model_config = {"protected_namespaces": ()}
    
    features: Dict[str, float] = Field(
        ...,
        description="Feature values for prediction",
        example={
            "precip_lag_1": 5.2,
            "precip_lag_7": 3.8,
            "precip_rolling_mean_7": 4.1,
            "precip_rolling_mean_30": 3.5,
            "ndvi_mean": 0.65,
            "lst_mean": 298.5,
            "elevation": 450.0,
            "slope": 5.2,
            "month_sin": 0.5,
            "month_cos": 0.866
        }
    )
    model_name: Optional[str] = Field(
        None,
        description="Specific model to use (linear_regression, random_forest, xgboost). If None, uses ensemble"
    )


class PredictionResponse(BaseModel):
    """Response model for prediction"""
    
    prediction_mm: float = Field(..., description="Predicted precipitation in mm")
    model: str = Field(..., description="Model used for prediction")
    timestamp: str = Field(..., description="Prediction timestamp")
    model_metadata: Optional[Dict] = Field(None, description="Model metadata")


class EnsemblePredictionResponse(BaseModel):
    """Response model for ensemble prediction"""
    
    predictions: Dict[str, float] = Field(..., description="Predictions from each model")
    ensemble_mean: float = Field(..., description="Ensemble average prediction")
    timestamp: str = Field(..., description="Prediction timestamp")
    models_used: List[str] = Field(..., description="List of models used")


@router.post("/predict", response_model=PredictionResponse)
async def predict_precipitation(
    request: PredictionRequest,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Make precipitation prediction using specified model or ensemble
    
    - **features**: Dictionary of feature values (see example)
    - **model_name**: Optional model name (linear_regression, random_forest, xgboost)
    
    If model_name is not specified, returns ensemble prediction.
    """
    try:
        if request.model_name:
            # Single model prediction
            result = model_service.predict(request.model_name, request.features)
            return PredictionResponse(**result)
        else:
            # Ensemble prediction
            result = model_service.predict_ensemble(request.features)
            return PredictionResponse(
                prediction_mm=result['ensemble_mean'],
                model='ensemble',
                timestamp=result['timestamp'],
                model_metadata={'models_used': result['models_used']}
            )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/ensemble", response_model=EnsemblePredictionResponse)
async def predict_ensemble(
    request: PredictionRequest,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Make precipitation prediction using all models and return ensemble
    
    Returns predictions from all available models plus ensemble average.
    """
    try:
        result = model_service.predict_ensemble(request.features)
        return EnsemblePredictionResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble prediction error: {str(e)}")


@router.get("/models")
async def get_models_info(model_service: ModelService = Depends(get_model_service)):
    """
    Get information about all loaded models
    
    Returns metadata about available models including:
    - Model paths
    - Training metrics
    - Feature requirements
    """
    try:
        return model_service.get_models_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models info: {str(e)}")


@router.get("/features")
async def get_feature_names(model_service: ModelService = Depends(get_model_service)):
    """
    Get list of required feature names for predictions
    
    Returns the feature names in the order expected by the models.
    """
    try:
        return {
            "feature_names": model_service.get_feature_names(),
            "count": len(model_service.get_feature_names())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting features: {str(e)}")


@router.post("/predict/batch")
async def predict_batch(
    features_list: List[Dict[str, float]],
    model_name: Optional[str] = None,
    model_service: ModelService = Depends(get_model_service)
):
    """
    Make batch predictions for multiple feature sets
    
    - **features_list**: List of feature dictionaries
    - **model_name**: Optional model name
    
    Returns list of predictions.
    """
    try:
        predictions = []
        
        for features in features_list:
            if model_name:
                result = model_service.predict(model_name, features)
            else:
                result = model_service.predict_ensemble(features)
                result = {
                    'prediction_mm': result['ensemble_mean'],
                    'model': 'ensemble',
                    'timestamp': result['timestamp']
                }
            
            predictions.append(result)
        
        return {
            "predictions": predictions,
            "count": len(predictions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")
