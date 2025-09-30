#!/bin/bash

# Push Docker images to OCI Container Registry

set -e

echo "=========================================="
echo "Pushing Images to OCIR"
echo "=========================================="

# Configuration
VERSION=${1:-latest}
REGION=${OCI_REGION:-us-ashburn-1}
TENANCY=${OCI_TENANCY:-your-tenancy}

REGISTRY="${REGION}.ocir.io/${TENANCY}"

echo "Registry: $REGISTRY"
echo "Version: $VERSION"

# Login to OCIR
echo -e "\n>>> Logging in to OCIR..."
echo "Please enter your OCIR auth token:"
docker login ${REGION}.ocir.io

# Tag and push images
IMAGES=(
  "data-ingestion"
  "preprocessing"
  "feature-engineering"
  "modeling"
  "prediction-service"
  "frontend"
)

for IMAGE in "${IMAGES[@]}"; do
  echo -e "\n>>> Pushing ${IMAGE}..."
  
  # Tag
  docker tag localhost/aquapredict/${IMAGE}:${VERSION} \
    ${REGISTRY}/aquapredict/${IMAGE}:${VERSION}
  
  # Push
  docker push ${REGISTRY}/aquapredict/${IMAGE}:${VERSION}
  
  echo "✓ ${IMAGE} pushed"
done

echo -e "\n=========================================="
echo "✓ All images pushed successfully!"
echo "=========================================="
