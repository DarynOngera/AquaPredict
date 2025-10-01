#!/bin/bash
# AquaPredict OCI Infrastructure Deployment Script
# This script automates the deployment of all OCI infrastructure components

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check OCI CLI
    if ! command -v oci &> /dev/null; then
        log_error "OCI CLI not found. Please install it first."
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform not found. Please install it first."
        exit 1
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_warn "kubectl not found. You'll need it for OKE deployment."
    fi
    
    log_info "Prerequisites check passed!"
}

# Validate OCI configuration
validate_oci_config() {
    log_info "Validating OCI configuration..."
    
    if ! oci iam region list &> /dev/null; then
        log_error "OCI CLI not configured properly. Run 'oci setup config'"
        exit 1
    fi
    
    log_info "OCI configuration valid!"
}

# Initialize Terraform
init_terraform() {
    log_info "Initializing Terraform..."
    cd ../terraform
    
    terraform init
    
    log_info "Terraform initialized!"
}

# Validate Terraform configuration
validate_terraform() {
    log_info "Validating Terraform configuration..."
    
    terraform validate
    
    if [ $? -eq 0 ]; then
        log_info "Terraform configuration is valid!"
    else
        log_error "Terraform configuration validation failed!"
        exit 1
    fi
}

# Plan Terraform deployment
plan_terraform() {
    log_info "Planning Terraform deployment..."
    
    terraform plan -out=tfplan
    
    log_info "Terraform plan created. Review the plan above."
}

# Apply Terraform configuration
apply_terraform() {
    log_info "Applying Terraform configuration..."
    
    read -p "Do you want to proceed with deployment? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_warn "Deployment cancelled by user."
        exit 0
    fi
    
    terraform apply tfplan
    
    log_info "Infrastructure deployed successfully!"
}

# Save Terraform outputs
save_outputs() {
    log_info "Saving Terraform outputs..."
    
    terraform output -json > outputs.json
    
    # Extract important values
    DB_CONNECTION=$(terraform output -raw database_app_connection)
    BACKEND_IP=$(terraform output -raw compute_backend_api_ip)
    LB_IP=$(terraform output -raw compute_load_balancer_ip)
    NOTEBOOK_URL=$(terraform output -raw data_science_notebook_url)
    
    # Save to .env file
    cat > ../../../.env.production <<EOF
# AquaPredict Production Environment Configuration
# Generated on $(date)

# Database
DB_CONNECTION_STRING=${DB_CONNECTION}

# API Endpoints
BACKEND_API_IP=${BACKEND_IP}
LOAD_BALANCER_IP=${LB_IP}
API_URL=http://${LB_IP}

# OCI Data Science
NOTEBOOK_URL=${NOTEBOOK_URL}

# Object Storage
OBJECT_STORAGE_NAMESPACE=$(terraform output -raw object_storage_namespace)
RAW_DATA_BUCKET=$(terraform output -json object_storage_buckets | jq -r '.raw_data')
MODELS_BUCKET=$(terraform output -json object_storage_buckets | jq -r '.models')

# OKE
OKE_CLUSTER_ID=$(terraform output -raw oke_cluster_id)
EOF
    
    log_info "Outputs saved to .env.production"
}

# Configure kubectl for OKE
configure_kubectl() {
    log_info "Configuring kubectl for OKE..."
    
    CLUSTER_ID=$(terraform output -raw oke_cluster_id)
    REGION=$(terraform output -json | jq -r '.region.value')
    
    oci ce cluster create-kubeconfig \
        --cluster-id ${CLUSTER_ID} \
        --file ~/.kube/config \
        --region ${REGION} \
        --token-version 2.0.0
    
    log_info "kubectl configured for OKE cluster!"
}

# Download database wallet
download_wallet() {
    log_info "Downloading database wallet..."
    
    WALLET_PATH=$(terraform output -raw database_wallet_path)
    
    if [ -f "$WALLET_PATH" ]; then
        mkdir -p ../../../credentials
        cp "$WALLET_PATH" ../../../credentials/wallet.zip
        log_info "Database wallet saved to credentials/wallet.zip"
    else
        log_warn "Wallet not found at expected location"
    fi
}

# Display deployment summary
display_summary() {
    log_info "========================================="
    log_info "Deployment Summary"
    log_info "========================================="
    
    echo ""
    log_info "Backend API IP: $(terraform output -raw compute_backend_api_ip)"
    log_info "Load Balancer IP: $(terraform output -raw compute_load_balancer_ip)"
    log_info "Data Science Notebook: $(terraform output -raw data_science_notebook_url)"
    echo ""
    
    log_info "Object Storage Buckets:"
    terraform output -json object_storage_buckets | jq -r 'to_entries[] | "  - \(.key): \(.value)"'
    echo ""
    
    log_info "========================================="
    log_info "Next Steps:"
    log_info "1. Configure kubectl: source ~/.bashrc && kubectl get nodes"
    log_info "2. Deploy applications: cd ../k8s && kubectl apply -f ."
    log_info "3. Access Data Science Notebook: Open the URL above"
    log_info "4. Configure DNS for Load Balancer IP"
    log_info "========================================="
}

# Main deployment flow
main() {
    log_info "Starting AquaPredict Infrastructure Deployment..."
    echo ""
    
    check_prerequisites
    validate_oci_config
    init_terraform
    validate_terraform
    plan_terraform
    apply_terraform
    save_outputs
    configure_kubectl
    download_wallet
    display_summary
    
    log_info "Deployment completed successfully!"
}

# Run main function
main "$@"
