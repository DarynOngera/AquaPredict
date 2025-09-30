"""Configuration for prediction service."""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class ServiceConfig(BaseSettings):
    """Configuration for prediction service."""
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_workers: int = int(os.getenv("API_WORKERS", "4"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Model paths
    model_path: str = os.getenv("MODEL_PATH", "./models/trained")
    aquifer_model_file: str = "aquifer_classifier.joblib"
    recharge_model_file: str = "recharge_forecaster.joblib"
    
    # Database configuration
    database_url: str = os.getenv("DATABASE_URL", "")
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Cache configuration
    use_redis: bool = os.getenv("USE_REDIS", "False").lower() == "true"
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    cache_ttl: int = 3600  # seconds
    
    # Prediction settings
    batch_size_limit: int = 1000
    max_forecast_horizon: int = 36  # months
    
    class Config:
        env_file = ".env"
