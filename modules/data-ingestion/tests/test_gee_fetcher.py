"""Tests for GEE data fetcher."""

import pytest
import ee
from unittest.mock import Mock, patch, MagicMock

from gee_fetcher import GEEDataFetcher
from config import IngestionConfig


@pytest.fixture
def config():
    """Create test configuration."""
    return IngestionConfig()


@pytest.fixture
def mock_ee():
    """Mock Earth Engine initialization."""
    with patch('gee_fetcher.ee.Initialize') as mock_init:
        yield mock_init


@pytest.fixture
def fetcher(config, mock_ee):
    """Create GEE fetcher instance."""
    return GEEDataFetcher(config)


def test_initialization(fetcher):
    """Test GEE fetcher initialization."""
    assert fetcher.config is not None
    assert fetcher.region is not None


def test_create_region_geometry(fetcher):
    """Test region geometry creation."""
    region = fetcher._create_region_geometry()
    assert region is not None


@patch('gee_fetcher.ee.ImageCollection')
def test_fetch_precipitation(mock_collection, fetcher):
    """Test precipitation data fetching."""
    # Mock the image collection
    mock_img = Mock()
    mock_collection.return_value.filterDate.return_value.filterBounds.return_value = mock_img
    
    result = fetcher.fetch_precipitation('2020-01-01', '2020-12-31', 'yearly')
    assert result is not None


@patch('gee_fetcher.ee.ImageCollection')
def test_fetch_temperature(mock_collection, fetcher):
    """Test temperature data fetching."""
    mock_img = Mock()
    mock_collection.return_value.filterDate.return_value.filterBounds.return_value.select.return_value = mock_img
    
    result = fetcher.fetch_temperature('2020-01-01', '2020-12-31')
    assert result is not None


@patch('gee_fetcher.ee.Image')
def test_fetch_elevation(mock_image, fetcher):
    """Test elevation data fetching."""
    mock_dem = Mock()
    mock_image.return_value.clip.return_value = mock_dem
    
    result = fetcher.fetch_elevation()
    assert result is not None


def test_config_defaults():
    """Test configuration defaults."""
    config = IngestionConfig()
    assert config.grid_resolution_km == 1.0
    assert config.crs == "EPSG:4326"
    assert len(config.region_bounds) == 4
