# Modeling Module

This module implements machine learning models for aquifer prediction, depth classification, and groundwater recharge forecasting.

## Models

### Classification Models
- **Random Forest**: Aquifer presence/absence classification
- **XGBoost**: Aquifer depth classification (shallow/medium/deep)
- **Ensemble**: Combined predictions with confidence intervals

### Regression Models
- **Random Forest Regressor**: Continuous depth prediction
- **XGBoost Regressor**: Groundwater level prediction

### Time-Series Models
- **LSTM**: Groundwater recharge forecasting
- **Temporal Fusion Transformer (TFT)**: Multi-horizon forecasting with attention

### Rule-Based Models
- **Depletion Model**: Rule-based groundwater depletion assessment

## Features

- Cross-validation with spatial CV
- Hyperparameter tuning
- Model evaluation (ROC-AUC, RMSE, MAE, R²)
- Feature importance analysis
- Model persistence and versioning
- Ensemble predictions with uncertainty quantification

## Usage

```python
from modeling import AquiferClassifier, RechargeForecaster

# Train aquifer classifier
classifier = AquiferClassifier(model_type='xgboost')
classifier.train(X_train, y_train)
predictions = classifier.predict(X_test)

# Train recharge forecaster
forecaster = RechargeForecaster(model_type='lstm')
forecaster.train(time_series_data)
forecast = forecaster.forecast(horizon=12)
```

## Model Evaluation

- **Classification**: ROC-AUC, Precision, Recall, F1-Score
- **Regression**: RMSE, MAE, R², MAPE
- **Spatial CV**: 5-fold spatial cross-validation
- **Temporal CV**: Time-series split for forecasting

## Testing

```bash
pytest tests/
```
