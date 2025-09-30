"""Pytest configuration and fixtures."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))


@pytest.fixture
def sample_dem():
    """Sample Digital Elevation Model."""
    return np.random.rand(100, 100) * 1000


@pytest.fixture
def sample_precipitation():
    """Sample precipitation time series."""
    return np.random.rand(12, 100, 100) * 100


@pytest.fixture
def sample_temperature():
    """Sample temperature time series."""
    return np.random.rand(12, 100, 100) * 30


@pytest.fixture
def sample_features():
    """Sample feature matrix."""
    return np.random.rand(100, 10)


@pytest.fixture
def sample_labels():
    """Sample binary labels."""
    return np.random.randint(0, 2, 100)


@pytest.fixture
def sample_time_series():
    """Sample time series data."""
    return np.random.rand(100, 3)


@pytest.fixture
def sample_location():
    """Sample geographic location."""
    return {"lat": 0.0, "lon": 36.0}
