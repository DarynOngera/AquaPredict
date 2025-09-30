#!/bin/bash

# Build Docker images for all modules

set -e

echo "=========================================="
echo "Building AquaPredict Docker Images"
echo "=========================================="

# Get version from git or use default
VERSION=${1:-latest}
REGISTRY=${REGISTRY:-localhost}

echo "Version: $VERSION"
echo "Registry: $REGISTRY"

# Build data-ingestion
echo -e "\n>>> Building data-ingestion..."
docker build -t ${REGISTRY}/aquapredict/data-ingestion:${VERSION} \
  -f modules/data-ingestion/Dockerfile \
  modules/data-ingestion/

# Build preprocessing
echo -e "\n>>> Building preprocessing..."
docker build -t ${REGISTRY}/aquapredict/preprocessing:${VERSION} \
  -f modules/preprocessing/Dockerfile \
  modules/preprocessing/

# Build feature-engineering
echo -e "\n>>> Building feature-engineering..."
docker build -t ${REGISTRY}/aquapredict/feature-engineering:${VERSION} \
  -f modules/feature-engineering/Dockerfile \
  modules/feature-engineering/

# Build modeling
echo -e "\n>>> Building modeling..."
docker build -t ${REGISTRY}/aquapredict/modeling:${VERSION} \
  -f modules/modeling/Dockerfile \
  modules/modeling/

# Build prediction-service
echo -e "\n>>> Building prediction-service..."
docker build -t ${REGISTRY}/aquapredict/prediction-service:${VERSION} \
  -f modules/prediction-service/Dockerfile \
  modules/prediction-service/

# Build frontend
echo -e "\n>>> Building frontend..."
docker build -t ${REGISTRY}/aquapredict/frontend:${VERSION} \
  -f modules/frontend/Dockerfile \
  modules/frontend/

echo -e "\n=========================================="
echo "✓ All images built successfully!"
echo "=========================================="
echo ""
echo "Images:"
docker images | grep aquapredict
