"""Integration tests for AquaPredict pipeline."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "modules"))


class TestDataPipeline:
    """Test end-to-end data pipeline."""
    
    def test_feature_engineering_pipeline(self):
        """Test feature engineering pipeline."""
        from feature_engineering import FeatureEngineer
        
        engineer = FeatureEngineer()
        
        # Create sample data
        dem = np.random.rand(100, 100) * 1000
        flow_acc = np.random.rand(100, 100) * 100
        
        # Compute TWI
        twi = engineer.compute_twi(dem, flow_acc)
        
        assert twi.shape == dem.shape
        assert not np.all(np.isnan(twi))
    
    def test_preprocessing_pipeline(self):
        """Test preprocessing pipeline."""
        from preprocessing import DataPreprocessor
        
        preprocessor = DataPreprocessor()
        
        # Create sample data with missing values
        data = np.random.rand(100, 100)
        data[data < 0.1] = np.nan
        
        # Fill missing values
        filled = preprocessor.fill_missing(data)
        
        assert filled.shape == data.shape
        assert np.isnan(filled).sum() < np.isnan(data).sum()
    
    def test_model_training_pipeline(self):
        """Test model training pipeline."""
        from modeling import AquiferClassifier
        
        # Create sample training data
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        
        # Train classifier
        classifier = AquiferClassifier(model_type='random_forest')
        metrics = classifier.train(X, y)
        
        assert 'cv_accuracy_mean' in metrics
        
        # Make predictions
        predictions = classifier.predict(X[:10])
        
        assert len(predictions) == 10
        assert all(p in [0, 1] for p in predictions)


class TestAPIIntegration:
    """Test API integration."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health endpoint."""
        from httpx import AsyncClient
        
        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
    
    @pytest.mark.asyncio
    async def test_prediction_endpoint(self):
        """Test prediction endpoint."""
        from httpx import AsyncClient
        
        async with AsyncClient(base_url="http://localhost:8000") as client:
            response = await client.post(
                "/api/v1/predict/aquifer",
                json={
                    "location": {"lat": 0.0, "lon": 36.0},
                    "use_cached_features": False,
                    "features": {
                        "elevation": 1500,
                        "slope": 5.2,
                        "twi": 8.5,
                        "precip_mean": 800,
                        "temp_mean": 22.5
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "prediction" in data
                assert "probability" in data


class TestEndToEnd:
    """Test complete end-to-end workflow."""
    
    def test_complete_workflow(self):
        """Test complete workflow from features to prediction."""
        from feature_engineering import FeatureEngineer
        from preprocessing import DataPreprocessor
        from modeling import AquiferClassifier
        
        # Step 1: Generate features
        engineer = FeatureEngineer()
        dem = np.random.rand(50, 50) * 1000
        flow_acc = np.random.rand(50, 50) * 100
        precip = np.random.rand(12, 50, 50) * 100
        temp = np.random.rand(12, 50, 50) * 30
        
        features = {
            'twi': engineer.compute_twi(dem, flow_acc),
            'tpi': engineer.compute_tpi(dem),
            'spi_3': engineer.compute_spi(precip, timescale=3)
        }
        
        # Step 2: Preprocess
        preprocessor = DataPreprocessor()
        for key in features:
            if features[key].ndim == 3:
                features[key] = features[key][0]  # Take first timestep
            features[key] = preprocessor.normalize(features[key])
        
        # Step 3: Prepare training data
        X = np.column_stack([
            features['twi'].flatten(),
            features['tpi'].flatten(),
            features['spi_3'].flatten()
        ])
        y = np.random.randint(0, 2, X.shape[0])
        
        # Remove NaN rows
        valid_mask = ~np.isnan(X).any(axis=1)
        X = X[valid_mask]
        y = y[valid_mask]
        
        # Step 4: Train model
        classifier = AquiferClassifier(model_type='random_forest')
        classifier.train(X, y)
        
        # Step 5: Make predictions
        predictions = classifier.predict(X[:10])
        probabilities = classifier.predict_proba(X[:10])
        
        assert len(predictions) == 10
        assert probabilities.shape[0] == 10
        assert probabilities.shape[1] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
