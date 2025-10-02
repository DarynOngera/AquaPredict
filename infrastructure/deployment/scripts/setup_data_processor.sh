#!/bin/bash
set -e

# AquaPredict Data Processor Setup Script
# Run this on the data processor compute instance

echo "=== AquaPredict Data Processor Setup ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
APP_DIR="/opt/AquaPredict"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/aquapredict"
SERVICE_USER="opc"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please run as regular user (opc), not root"
    exit 1
fi

# Step 1: Update system
print_info "Updating system packages..."
sudo yum update -y

# Step 2: Install dependencies
print_info "Installing system dependencies..."
sudo yum install -y \
    python3.11 \
    python3.11-pip \
    python3.11-devel \
    git \
    gcc \
    gcc-c++ \
    make \
    gdal \
    gdal-devel \
    proj \
    proj-devel \
    geos \
    geos-devel \
    hdf5 \
    hdf5-devel \
    netcdf \
    netcdf-devel

# Step 3: Clone repository
print_info "Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p /opt
    cd /opt
    
    read -p "Enter your GitHub repository URL: " REPO_URL
    sudo git clone "$REPO_URL" AquaPredict
    sudo chown -R $SERVICE_USER:$SERVICE_USER AquaPredict
else
    print_warn "Application directory already exists. Pulling latest changes..."
    cd "$APP_DIR"
    git pull
fi

cd "$APP_DIR"

# Step 4: Setup Python virtual environment
print_info "Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3.11 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Step 5: Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r modules/data_processor/requirements.txt

# Step 6: Install OCI CLI
print_info "Installing OCI CLI..."
if ! command -v oci &> /dev/null; then
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
    export PATH=$PATH:~/bin
fi

# Step 7: Create environment file
print_info "Creating environment configuration..."
cat > "$APP_DIR/.env" << 'EOF'
# OCI Configuration
OCI_NAMESPACE=frxiensafavx
OCI_REGION=eu-frankfurt-1
OCI_BUCKET_RAW=aquapredict-data-raw
OCI_BUCKET_PROCESSED=aquapredict-data-processed
OCI_BUCKET_MODELS=aquapredict-models

# Processing Configuration
BATCH_SIZE=100
MAX_WORKERS=4
PROCESSING_INTERVAL=300

# Google Earth Engine
GEE_SERVICE_ACCOUNT_JSON=/opt/AquaPredict/credentials/gee-service-account.json

# Logging
LOG_LEVEL=info
EOF

chmod 600 "$APP_DIR/.env"

# Step 8: Create log directory
print_info "Creating log directory..."
sudo mkdir -p "$LOG_DIR"
sudo chown $SERVICE_USER:$SERVICE_USER "$LOG_DIR"

# Step 9: Create systemd service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/aquapredict-processor.service > /dev/null << EOF
[Unit]
Description=AquaPredict Data Processor
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/modules/data_processor
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/python processor.py

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 10: Enable and start service
print_info "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable aquapredict-processor
sudo systemctl start aquapredict-processor

# Step 11: Wait and check status
sleep 3
print_info "Service status:"
sudo systemctl status aquapredict-processor --no-pager

print_info ""
print_info "=== Setup Complete ==="
print_info ""
print_info "Useful commands:"
print_info "  View logs:    sudo journalctl -u aquapredict-processor -f"
print_info "  Restart:      sudo systemctl restart aquapredict-processor"
print_info "  Check status: sudo systemctl status aquapredict-processor"
print_info ""
print_info "Next steps:"
print_info "  1. Configure OCI credentials: oci setup config"
print_info "  2. Upload GEE service account to: $APP_DIR/credentials/"
print_info "  3. Test data processing pipeline"
