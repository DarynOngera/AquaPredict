"""Spatial cross-validation for geospatial models."""

import numpy as np
from sklearn.cluster import KMeans
from typing import Generator, Tuple


class SpatialCV:
    """Spatial cross-validation using spatial clustering."""
    
    def __init__(self, n_splits: int = 5, random_state: int = 42):
        """
        Initialize Spatial CV.
        
        Args:
            n_splits: Number of CV splits
            random_state: Random seed
        """
        self.n_splits = n_splits
        self.random_state = random_state
    
    def split(
        self,
        X: np.ndarray,
        coordinates: np.ndarray
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test splits based on spatial clustering.
        
        Args:
            X: Feature matrix (not used, for sklearn compatibility)
            coordinates: Spatial coordinates [n_samples, 2] (lon, lat)
            
        Yields:
            Tuple of (train_indices, test_indices)
        """
        # Cluster coordinates into n_splits spatial clusters
        kmeans = KMeans(
            n_clusters=self.n_splits,
            random_state=self.random_state,
            n_init=10
        )
        cluster_labels = kmeans.fit_predict(coordinates)
        
        # Generate splits: each cluster becomes test set once
        for i in range(self.n_splits):
            test_mask = cluster_labels == i
            train_mask = ~test_mask
            
            train_indices = np.where(train_mask)[0]
            test_indices = np.where(test_mask)[0]
            
            yield train_indices, test_indices
