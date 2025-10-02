#!/bin/bash
set -e

# AquaPredict Backend Setup Script
# Run this on the backend API compute instance

echo "=== AquaPredict Backend Setup ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/AquaPredict"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/var/log/aquapredict"
SERVICE_USER="opc"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

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
    nginx \
    gcc \
    gcc-c++ \
    make \
    postgresql \
    postgresql-devel \
    gdal \
    gdal-devel \
    proj \
    proj-devel \
    geos \
    geos-devel

# Step 3: Install Node.js
print_info "Installing Node.js 20..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
    sudo yum install -y nodejs
fi

# Step 4: Clone repository
print_info "Setting up application directory..."
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p /opt
    cd /opt
    
    # Prompt for repository URL
    read -p "Enter your GitHub repository URL: " REPO_URL
    sudo git clone "$REPO_URL" AquaPredict
    sudo chown -R $SERVICE_USER:$SERVICE_USER AquaPredict
else
    print_warn "Application directory already exists. Pulling latest changes..."
    cd "$APP_DIR"
    git pull
fi

cd "$APP_DIR"

# Step 5: Setup Python virtual environment
print_info "Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3.11 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# Step 6: Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r modules/backend/requirements.txt
pip install gunicorn uvicorn[standard]

# Step 7: Setup OCI CLI
print_info "Installing OCI CLI..."
if ! command -v oci &> /dev/null; then
    bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)" -- --accept-all-defaults
    echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
    export PATH=$PATH:~/bin
fi

# Step 8: Create environment file
print_info "Creating environment configuration..."
cat > "$APP_DIR/.env" << 'EOF'
# OCI Configuration
OCI_NAMESPACE=frxiensafavx
OCI_REGION=eu-frankfurt-1
OCI_BUCKET_RAW=aquapredict-data-raw
OCI_BUCKET_PROCESSED=aquapredict-data-processed
OCI_BUCKET_MODELS=aquapredict-models
OCI_BUCKET_REPORTS=aquapredict-reports

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4
LOG_LEVEL=info

# Model Configuration
MODEL_PATH=/opt/AquaPredict/models
ENABLE_GPU=false

# Feature Flags
ENABLE_CACHING=true
ENABLE_METRICS=true
EOF

chmod 600 "$APP_DIR/.env"

# Step 9: Create log directory
print_info "Creating log directory..."
sudo mkdir -p "$LOG_DIR"
sudo chown $SERVICE_USER:$SERVICE_USER "$LOG_DIR"

# Step 10: Create systemd service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/aquapredict-api.service > /dev/null << EOF
[Unit]
Description=AquaPredict Backend API
After=network.target

[Service]
Type=notify
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/modules/backend
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn \\
    --bind 0.0.0.0:8000 \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --timeout 300 \\
    --access-logfile $LOG_DIR/access.log \\
    --error-logfile $LOG_DIR/error.log \\
    --log-level info \\
    app.main:app

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Step 11: Configure nginx
print_info "Configuring nginx..."
sudo tee /etc/nginx/conf.d/aquapredict.conf > /dev/null << 'EOF'
upstream backend_api {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    client_body_timeout 300s;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API endpoints
    location /api/ {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_buffering off;
    }
    
    # Health check
    location /health {
        proxy_pass http://backend_api/health;
        access_log off;
    }
    
    # Metrics endpoint (restrict access in production)
    location /metrics {
        proxy_pass http://backend_api/metrics;
        # allow 10.0.0.0/8;
        # deny all;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

# Step 12: Configure firewall
print_info "Configuring firewall..."
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload
fi

# Step 13: Enable and start services
print_info "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable aquapredict-api
sudo systemctl enable nginx

print_info "Starting services..."
sudo systemctl start aquapredict-api
sudo systemctl start nginx

# Step 14: Wait for service to start
print_info "Waiting for API to start..."
sleep 5

# Step 15: Health check
print_info "Running health check..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_info "✓ Backend API is running successfully!"
else
    print_warn "Backend API health check failed. Check logs with: sudo journalctl -u aquapredict-api -f"
fi

# Step 16: Display status
print_info "Service status:"
sudo systemctl status aquapredict-api --no-pager

print_info ""
print_info "=== Setup Complete ==="
print_info "Backend API is running on port 8000"
print_info "Nginx is proxying on port 80"
print_info ""
print_info "Useful commands:"
print_info "  View logs:    sudo journalctl -u aquapredict-api -f"
print_info "  Restart API:  sudo systemctl restart aquapredict-api"
print_info "  Check status: sudo systemctl status aquapredict-api"
print_info "  Test API:     curl http://localhost:8000/health"
print_info ""
print_info "Next steps:"
print_info "  1. Configure OCI credentials: oci setup config"
print_info "  2. Upload your ML models to: $APP_DIR/models"
print_info "  3. Update .env file with your specific configuration"
print_info "  4. Test from load balancer: curl http://152.70.18.57/health"
