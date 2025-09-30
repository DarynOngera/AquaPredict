"""Groundwater recharge forecasting models."""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import logging
from typing import Optional, Dict, Any, Tuple
import os

from .config import ModelConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """Dataset for time series forecasting."""
    
    def __init__(
        self,
        data: np.ndarray,
        sequence_length: int = 12,
        forecast_horizon: int = 1
    ):
        """
        Initialize dataset.
        
        Args:
            data: Time series data [n_timesteps, n_features]
            sequence_length: Input sequence length
            forecast_horizon: Forecast horizon
        """
        self.data = torch.FloatTensor(data)
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
    
    def __len__(self) -> int:
        return len(self.data) - self.sequence_length - self.forecast_horizon + 1
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.data[idx:idx + self.sequence_length]
        y = self.data[idx + self.sequence_length:idx + self.sequence_length + self.forecast_horizon, 0]
        return x, y


class LSTMModel(pl.LightningModule):
    """LSTM model for time series forecasting."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        forecast_horizon: int = 1
    ):
        """
        Initialize LSTM model.
        
        Args:
            input_size: Number of input features
            hidden_size: Hidden layer size
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            learning_rate: Learning rate
            forecast_horizon: Forecast horizon
        """
        super().__init__()
        self.save_hyperparameters()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.fc = nn.Linear(hidden_size, forecast_horizon)
        self.learning_rate = learning_rate
    
    def forward(self, x):
        # LSTM forward pass
        lstm_out, _ = self.lstm(x)
        
        # Take last output
        last_output = lstm_out[:, -1, :]
        
        # Fully connected layer
        output = self.fc(last_output)
        
        return output
    
    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.MSELoss()(y_hat, y)
        self.log('train_loss', loss)
        return loss
    
    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self(x)
        loss = nn.MSELoss()(y_hat, y)
        self.log('val_loss', loss)
        return loss
    
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.learning_rate)


class RechargeForecaster:
    """Forecaster for groundwater recharge."""
    
    def __init__(
        self,
        model_type: str = 'lstm',
        config: Optional[ModelConfig] = None
    ):
        """
        Initialize Recharge Forecaster.
        
        Args:
            model_type: Type of model ('lstm', 'tft')
            config: Configuration object
        """
        self.model_type = model_type
        self.config = config or ModelConfig()
        self.model = None
        self.scaler = StandardScaler()
        self.sequence_length = 12  # 12 months lookback
        self.forecast_horizon = 1  # 1 month ahead
    
    def train(
        self,
        data: np.ndarray,
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the forecaster.
        
        Args:
            data: Time series data [n_timesteps, n_features]
            validation_split: Validation split ratio
            
        Returns:
            Dictionary of training metrics
        """
        logger.info("=" * 80)
        logger.info(f"Training {self.model_type} forecaster")
        logger.info(f"Time steps: {data.shape[0]}, Features: {data.shape[1]}")
        logger.info("=" * 80)
        
        # Normalize data
        data_normalized = self.scaler.fit_transform(data)
        
        # Split into train/validation
        split_idx = int(len(data_normalized) * (1 - validation_split))
        train_data = data_normalized[:split_idx]
        val_data = data_normalized[split_idx:]
        
        # Create datasets
        train_dataset = TimeSeriesDataset(
            train_data,
            self.sequence_length,
            self.forecast_horizon
        )
        val_dataset = TimeSeriesDataset(
            val_data,
            self.sequence_length,
            self.forecast_horizon
        )
        
        # Create dataloaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.lstm_batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.lstm_batch_size,
            shuffle=False
        )
        
        # Initialize model
        if self.model_type == 'lstm':
            self.model = LSTMModel(
                input_size=data.shape[1],
                hidden_size=self.config.lstm_hidden_size,
                num_layers=self.config.lstm_num_layers,
                dropout=self.config.lstm_dropout,
                learning_rate=self.config.lstm_learning_rate,
                forecast_horizon=self.forecast_horizon
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train model
        trainer = pl.Trainer(
            max_epochs=self.config.lstm_epochs,
            accelerator='auto',
            devices=1,
            logger=False,
            enable_checkpointing=True,
            default_root_dir=self.config.checkpoints_dir
        )
        
        trainer.fit(self.model, train_loader, val_loader)
        
        logger.info("✓ Training completed")
        
        return {
            'train_samples': len(train_dataset),
            'val_samples': len(val_dataset)
        }
    
    def forecast(
        self,
        data: np.ndarray,
        horizon: int = 12
    ) -> np.ndarray:
        """
        Generate forecast.
        
        Args:
            data: Historical data [n_timesteps, n_features]
            horizon: Forecast horizon (number of steps ahead)
            
        Returns:
            Forecasted values [horizon]
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        self.model.eval()
        
        # Normalize input data
        data_normalized = self.scaler.transform(data)
        
        # Generate forecast iteratively
        forecasts = []
        current_sequence = data_normalized[-self.sequence_length:]
        
        with torch.no_grad():
            for _ in range(horizon):
                # Prepare input
                x = torch.FloatTensor(current_sequence).unsqueeze(0)
                
                # Predict
                y_pred = self.model(x)
                forecast_value = y_pred.numpy()[0, 0]
                
                forecasts.append(forecast_value)
                
                # Update sequence (assuming univariate for simplicity)
                new_row = np.zeros(data_normalized.shape[1])
                new_row[0] = forecast_value
                current_sequence = np.vstack([current_sequence[1:], new_row])
        
        # Denormalize forecasts
        forecasts = np.array(forecasts).reshape(-1, 1)
        
        # Create dummy array for inverse transform
        dummy = np.zeros((len(forecasts), data.shape[1]))
        dummy[:, 0] = forecasts[:, 0]
        forecasts_denorm = self.scaler.inverse_transform(dummy)[:, 0]
        
        return forecasts_denorm
    
    def evaluate(
        self,
        data: np.ndarray,
        test_size: int = 12
    ) -> Dict[str, float]:
        """
        Evaluate the forecaster.
        
        Args:
            data: Time series data
            test_size: Number of test samples
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating forecaster...")
        
        # Split data
        train_data = data[:-test_size]
        test_data = data[-test_size:]
        
        # Generate forecasts
        forecasts = self.forecast(train_data, horizon=test_size)
        
        # Compute metrics (assuming first column is target)
        y_true = test_data[:, 0]
        y_pred = forecasts
        
        metrics = {
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / (y_true + 1e-10))) * 100
        }
        
        logger.info("Evaluation Metrics:")
        for metric, value in metrics.items():
            logger.info(f"  {metric.upper()}: {value:.4f}")
        
        return metrics
    
    def save(self, filepath: str):
        """
        Save the model to disk.
        
        Args:
            filepath: Path to save the model
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        model_data = {
            'model_state': self.model.state_dict() if self.model else None,
            'model_type': self.model_type,
            'scaler': self.scaler,
            'sequence_length': self.sequence_length,
            'forecast_horizon': self.forecast_horizon,
            'config': self.config
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RechargeForecaster':
        """
        Load a model from disk.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            Loaded RechargeForecaster instance
        """
        model_data = joblib.load(filepath)
        
        forecaster = cls(
            model_type=model_data['model_type'],
            config=model_data['config']
        )
        forecaster.scaler = model_data['scaler']
        forecaster.sequence_length = model_data['sequence_length']
        forecaster.forecast_horizon = model_data['forecast_horizon']
        
        # Reconstruct model (need to know input size)
        # This is simplified - in production, store full model architecture
        
        logger.info(f"Model loaded from: {filepath}")
        return forecaster
