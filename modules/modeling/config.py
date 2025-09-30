"""Configuration for modeling module."""

import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    """Configuration for modeling."""
    
    # Data paths
    data_dir: str = os.getenv("DATA_DIR", "./data")
    features_dir: str = os.path.join(data_dir, "features")
    models_dir: str = "./models"
    trained_models_dir: str = os.path.join(models_dir, "trained")
    checkpoints_dir: str = os.path.join(models_dir, "checkpoints")
    
    # Training parameters
    train_test_split: float = float(os.getenv("TRAIN_TEST_SPLIT", "0.8"))
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))
    cv_folds: int = int(os.getenv("CV_FOLDS", "5"))
    
    # Random Forest parameters
    rf_n_estimators: int = 100
    rf_max_depth: int = 20
    rf_min_samples_split: int = 5
    rf_min_samples_leaf: int = 2
    
    # XGBoost parameters
    xgb_n_estimators: int = 100
    xgb_max_depth: int = 6
    xgb_learning_rate: float = 0.1
    xgb_subsample: float = 0.8
    xgb_colsample_bytree: float = 0.8
    
    # LSTM parameters
    lstm_hidden_size: int = 64
    lstm_num_layers: int = 2
    lstm_dropout: float = 0.2
    lstm_learning_rate: float = 0.001
    lstm_batch_size: int = 32
    lstm_epochs: int = 50
    
    # TFT parameters
    tft_hidden_size: int = 32
    tft_attention_head_size: int = 4
    tft_dropout: float = 0.1
    tft_learning_rate: float = 0.001
    
    # Evaluation
    use_spatial_cv: bool = True
    n_spatial_clusters: int = 5
    
    # Hyperparameter tuning
    use_optuna: bool = True
    optuna_n_trials: int = 50
    
    def __post_init__(self):
        """Create directories if they don't exist."""
        os.makedirs(self.trained_models_dir, exist_ok=True)
        os.makedirs(self.checkpoints_dir, exist_ok=True)
    
    def get_rf_params(self) -> Dict[str, Any]:
        """Get Random Forest parameters."""
        return {
            'n_estimators': self.rf_n_estimators,
            'max_depth': self.rf_max_depth,
            'min_samples_split': self.rf_min_samples_split,
            'min_samples_leaf': self.rf_min_samples_leaf,
            'random_state': self.random_seed,
            'n_jobs': -1
        }
    
    def get_xgb_params(self) -> Dict[str, Any]:
        """Get XGBoost parameters."""
        return {
            'n_estimators': self.xgb_n_estimators,
            'max_depth': self.xgb_max_depth,
            'learning_rate': self.xgb_learning_rate,
            'subsample': self.xgb_subsample,
            'colsample_bytree': self.xgb_colsample_bytree,
            'random_state': self.random_seed,
            'n_jobs': -1
        }
