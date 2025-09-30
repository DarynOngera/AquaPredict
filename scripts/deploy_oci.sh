#!/bin/bash

# Deploy AquaPredict to OCI

set -e

echo "=========================================="
echo "Deploying AquaPredict to OCI"
echo "=========================================="

# Check prerequisites
command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed." >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but not installed." >&2; exit 1; }
command -v oci >/dev/null 2>&1 || { echo "OCI CLI is required but not installed." >&2; exit 1; }

# Phase 1: Deploy Infrastructure
echo -e "\n>>> Phase 1: Deploying Infrastructure with Terraform..."
cd infrastructure/terraform

terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get outputs
ADB_CONNECTION=$(terraform output -raw adb_connection_string)
OKE_CLUSTER_ID=$(terraform output -raw oke_cluster_id)
OCIR_SERVER=$(terraform output -raw ocir_login_server)

cd ../..

echo "✓ Infrastructure deployed"

# Phase 2: Configure kubectl
echo -e "\n>>> Phase 2: Configuring kubectl..."
oci ce cluster create-kubeconfig \
  --cluster-id ${OKE_CLUSTER_ID} \
  --file ~/.kube/config \
  --region ${OCI_REGION} \
  --token-version 2.0.0

kubectl config use-context ${OKE_CLUSTER_ID}

echo "✓ kubectl configured"

# Phase 3: Build and Push Images
echo -e "\n>>> Phase 3: Building and pushing Docker images..."
./scripts/build_images.sh latest
./scripts/push_images.sh latest

echo "✓ Images pushed to OCIR"

# Phase 4: Deploy to Kubernetes
echo -e "\n>>> Phase 4: Deploying to Kubernetes..."

# Create namespace
kubectl apply -f infrastructure/k8s/namespace.yaml

# Create secrets
kubectl create secret generic db-credentials \
  --from-literal=url="${ADB_CONNECTION}" \
  -n aquapredict \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret docker-registry ocir-secret \
  --docker-server=${OCIR_SERVER} \
  --docker-username="${OCI_TENANCY}/${OCI_USER}" \
  --docker-password="${OCIR_AUTH_TOKEN}" \
  -n aquapredict \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy applications
kubectl apply -f infrastructure/k8s/deployments/ -n aquapredict
kubectl apply -f infrastructure/k8s/services/ -n aquapredict
kubectl apply -f infrastructure/k8s/ingress.yaml -n aquapredict

echo "✓ Applications deployed"

# Phase 5: Wait for deployments
echo -e "\n>>> Phase 5: Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/prediction-service -n aquapredict
kubectl wait --for=condition=available --timeout=300s \
  deployment/frontend -n aquapredict

echo "✓ Deployments ready"

# Get service URLs
echo -e "\n=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
kubectl get svc -n aquapredict
echo ""
echo "Ingress:"
kubectl get ingress -n aquapredict
echo ""
echo "To access the application, configure DNS to point to the Load Balancer IP"
echo ""
