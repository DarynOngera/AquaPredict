"""
Script to export trained models from notebook
Run this at the end of your training notebook to save models
"""

import joblib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def export_model(
    model: Any,
    model_name: str,
    model_type: str,
    metrics: Dict[str, float],
    feature_names: list,
    output_dir: str = "models",
    version: str = "v1"
):
    """
    Export a trained model with metadata
    
    Args:
        model: Trained sklearn/xgboost model
        model_name: Name of the model (e.g., 'random_forest_precip')
        model_type: Type of model (e.g., 'RandomForestRegressor')
        metrics: Dictionary of evaluation metrics (e.g., {'rmse': 2.5, 'r2': 0.85})
        feature_names: List of feature names used for training
        output_dir: Directory to save models
        version: Model version
    """
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_filename = f"{model_name}_{version}.joblib"
    model_path = output_path / model_filename
    joblib.dump(model, model_path)
    print(f"✓ Saved model to: {model_path}")
    
    # Create metadata
    metadata = {
        'model_name': model_name,
        'model_type': model_type,
        'version': version,
        'created_at': datetime.now().isoformat(),
        'metrics': metrics,
        'feature_names': feature_names,
        'n_features': len(feature_names),
        'model_file': model_filename
    }
    
    # Save metadata
    metadata_filename = f"{model_name}_{version}_metadata.json"
    metadata_path = output_path / metadata_filename
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to: {metadata_path}")
    
    return model_path, metadata_path


def export_all_models(
    models_dict: Dict[str, Any],
    metrics_dict: Dict[str, Dict[str, float]],
    feature_names: list,
    output_dir: str = "models"
):
    """
    Export multiple models at once
    
    Args:
        models_dict: Dictionary of {model_name: model_object}
        metrics_dict: Dictionary of {model_name: metrics_dict}
        feature_names: List of feature names
        output_dir: Directory to save models
    
    Example:
        models = {
            'linear_regression': lr_model,
            'random_forest': rf_model,
            'xgboost': xgb_model
        }
        
        metrics = {
            'linear_regression': {'rmse': 3.2, 'r2': 0.75, 'mae': 2.5},
            'random_forest': {'rmse': 2.5, 'r2': 0.85, 'mae': 1.8},
            'xgboost': {'rmse': 2.3, 'r2': 0.87, 'mae': 1.7}
        }
        
        export_all_models(models, metrics, feature_names)
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save feature names
    feature_file = output_path / "feature_names.json"
    with open(feature_file, 'w') as f:
        json.dump(feature_names, f, indent=2)
    print(f"✓ Saved feature names to: {feature_file}")
    
    # Export each model
    exported_models = {}
    
    for model_name, model in models_dict.items():
        model_type = type(model).__name__
        metrics = metrics_dict.get(model_name, {})
        
        model_path, metadata_path = export_model(
            model=model,
            model_name=f"{model_name}_precip",
            model_type=model_type,
            metrics=metrics,
            feature_names=feature_names,
            output_dir=output_dir
        )
        
        exported_models[model_name] = {
            'model_path': str(model_path),
            'metadata_path': str(metadata_path)
        }
    
    print(f"\n✅ Exported {len(exported_models)} models successfully!")
    return exported_models


# Example usage in your notebook:
"""
# At the end of your training notebook, add:

from export_models import export_all_models

# Prepare your models dictionary
models = {
    'linear_regression': lr_model,
    'random_forest': rf_model,
    'xgboost': xgb_model
}

# Prepare metrics dictionary
metrics = {
    'linear_regression': {
        'rmse': lr_rmse,
        'r2': lr_r2,
        'mae': lr_mae
    },
    'random_forest': {
        'rmse': rf_rmse,
        'r2': rf_r2,
        'mae': rf_mae
    },
    'xgboost': {
        'rmse': xgb_rmse,
        'r2': xgb_r2,
        'mae': xgb_mae
    }
}

# Export all models
exported = export_all_models(
    models_dict=models,
    metrics_dict=metrics,
    feature_names=feature_names,  # Your list of feature names
    output_dir='/content/models'  # Or your preferred directory
)

# Download from Colab
from google.colab import files
import shutil

# Zip the models directory
shutil.make_archive('/content/aquapredict_models', 'zip', '/content/models')
files.download('/content/aquapredict_models.zip')
"""
