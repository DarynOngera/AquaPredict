"""Aquifer classification models."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, 
    recall_score, f1_score, confusion_matrix, classification_report
)
import xgboost as xgb
import joblib
import logging
from typing import Optional, Dict, Any, Tuple
import os

from .config import ModelConfig
from .spatial_cv import SpatialCV

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AquiferClassifier:
    """Classifier for aquifer presence and depth classification."""
    
    def __init__(
        self,
        model_type: str = 'xgboost',
        config: Optional[ModelConfig] = None
    ):
        """
        Initialize Aquifer Classifier.
        
        Args:
            model_type: Type of model ('random_forest', 'xgboost', 'ensemble')
            config: Configuration object
        """
        self.model_type = model_type
        self.config = config or ModelConfig()
        self.model = None
        self.feature_names = None
        self.feature_importance = None
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the model based on type."""
        if self.model_type == 'random_forest':
            self.model = RandomForestClassifier(**self.config.get_rf_params())
            logger.info("Initialized Random Forest Classifier")
        
        elif self.model_type == 'xgboost':
            self.model = xgb.XGBClassifier(**self.config.get_xgb_params())
            logger.info("Initialized XGBoost Classifier")
        
        elif self.model_type == 'ensemble':
            self.model = {
                'rf': RandomForestClassifier(**self.config.get_rf_params()),
                'xgb': xgb.XGBClassifier(**self.config.get_xgb_params())
            }
            logger.info("Initialized Ensemble Classifier")
        
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[list] = None,
        coordinates: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Train the classifier.
        
        Args:
            X: Feature matrix [n_samples, n_features]
            y: Target labels [n_samples]
            feature_names: List of feature names
            coordinates: Spatial coordinates for spatial CV [n_samples, 2]
            
        Returns:
            Dictionary of training metrics
        """
        logger.info("=" * 80)
        logger.info(f"Training {self.model_type} classifier")
        logger.info(f"Training samples: {X.shape[0]}, Features: {X.shape[1]}")
        logger.info("=" * 80)
        
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        # Cross-validation
        if self.config.use_spatial_cv and coordinates is not None:
            logger.info("Using Spatial Cross-Validation")
            spatial_cv = SpatialCV(n_splits=self.config.cv_folds)
            cv_scores = []
            
            for train_idx, val_idx in spatial_cv.split(X, coordinates):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                if self.model_type == 'ensemble':
                    # Train ensemble
                    for name, model in self.model.items():
                        model.fit(X_train, y_train)
                    y_pred = self._ensemble_predict(X_val)
                else:
                    self.model.fit(X_train, y_train)
                    y_pred = self.model.predict(X_val)
                
                score = accuracy_score(y_val, y_pred)
                cv_scores.append(score)
            
            logger.info(f"Spatial CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")
        
        else:
            logger.info("Using Stratified K-Fold Cross-Validation")
            if self.model_type != 'ensemble':
                cv = StratifiedKFold(n_splits=self.config.cv_folds, shuffle=True, 
                                    random_state=self.config.random_seed)
                cv_scores = cross_val_score(self.model, X, y, cv=cv, scoring='accuracy')
                logger.info(f"CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores):.4f})")
        
        # Train final model on all data
        if self.model_type == 'ensemble':
            for name, model in self.model.items():
                model.fit(X, y)
                logger.info(f"  - Trained {name}")
        else:
            self.model.fit(X, y)
        
        # Compute feature importance
        self._compute_feature_importance()
        
        logger.info("✓ Training completed")
        
        return {
            'cv_accuracy_mean': np.mean(cv_scores) if 'cv_scores' in locals() else None,
            'cv_accuracy_std': np.std(cv_scores) if 'cv_scores' in locals() else None
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Feature matrix [n_samples, n_features]
            
        Returns:
            Predicted labels [n_samples]
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if self.model_type == 'ensemble':
            return self._ensemble_predict(X)
        else:
            return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix [n_samples, n_features]
            
        Returns:
            Class probabilities [n_samples, n_classes]
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        if self.model_type == 'ensemble':
            return self._ensemble_predict_proba(X)
        else:
            return self.model.predict_proba(X)
    
    def _ensemble_predict(self, X: np.ndarray) -> np.ndarray:
        """Ensemble prediction (majority voting)."""
        predictions = []
        for model in self.model.values():
            predictions.append(model.predict(X))
        
        # Majority voting
        predictions = np.array(predictions)
        return np.apply_along_axis(
            lambda x: np.bincount(x.astype(int)).argmax(),
            axis=0,
            arr=predictions
        )
    
    def _ensemble_predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Ensemble probability prediction (averaging)."""
        probas = []
        for model in self.model.values():
            probas.append(model.predict_proba(X))
        
        # Average probabilities
        return np.mean(probas, axis=0)
    
    def evaluate(
        self,
        X: np.ndarray,
        y_true: np.ndarray
    ) -> Dict[str, float]:
        """
        Evaluate the classifier.
        
        Args:
            X: Feature matrix
            y_true: True labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating classifier...")
        
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        # Compute metrics
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }
        
        # ROC-AUC for binary classification
        if len(np.unique(y_true)) == 2:
            metrics['roc_auc'] = roc_auc_score(y_true, y_proba[:, 1])
        else:
            # Multi-class ROC-AUC
            try:
                metrics['roc_auc'] = roc_auc_score(
                    y_true, y_proba, 
                    multi_class='ovr', 
                    average='weighted'
                )
            except Exception:
                metrics['roc_auc'] = None
        
        # Log metrics
        logger.info("Evaluation Metrics:")
        for metric, value in metrics.items():
            if value is not None:
                logger.info(f"  {metric}: {value:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        # Classification report
        logger.info(f"\nClassification Report:\n{classification_report(y_true, y_pred)}")
        
        return metrics
    
    def _compute_feature_importance(self):
        """Compute and store feature importance."""
        if self.model_type == 'ensemble':
            # Average importance across ensemble
            importances = []
            for model in self.model.values():
                if hasattr(model, 'feature_importances_'):
                    importances.append(model.feature_importances_)
            
            if importances:
                self.feature_importance = np.mean(importances, axis=0)
        else:
            if hasattr(self.model, 'feature_importances_'):
                self.feature_importance = self.model.feature_importances_
        
        if self.feature_importance is not None:
            # Sort by importance
            indices = np.argsort(self.feature_importance)[::-1]
            
            logger.info("\nTop 10 Most Important Features:")
            for i in range(min(10, len(indices))):
                idx = indices[i]
                logger.info(
                    f"  {i+1}. {self.feature_names[idx]}: "
                    f"{self.feature_importance[idx]:.4f}"
                )
    
    def save(self, filepath: str):
        """
        Save the model to disk.
        
        Args:
            filepath: Path to save the model
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'config': self.config
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'AquiferClassifier':
        """
        Load a model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded AquiferClassifier instance
        """
        model_data = joblib.load(filepath)
        
        classifier = cls(
            model_type=model_data['model_type'],
            config=model_data['config']
        )
        classifier.model = model_data['model']
        classifier.feature_names = model_data['feature_names']
        classifier.feature_importance = model_data['feature_importance']
        
        logger.info(f"Model loaded from: {filepath}")
        return classifier
