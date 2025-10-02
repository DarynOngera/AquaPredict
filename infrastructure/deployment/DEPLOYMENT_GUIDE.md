# AquaPredict Direct Deployment Guide

## Infrastructure Overview

Your OCI infrastructure is now deployed with:

- **Load Balancer IP**: `152.70.18.57` (Public access point)
- **Compute Instances**: 
  - Backend API (Private subnet)
  - Data Processor (Private subnet)
- **Object Storage Namespace**: `frxiensafavx`
- **Storage Buckets**:
  - `aquapredict-data-raw` - Raw satellite/sensor data
  - `aquapredict-data-processed` - Processed data
  - `aquapredict-models` - ML models
  - `aquapredict-reports` - Generated reports
  - `aquapredict-backups` - Backups

## Deployment Architecture

```
Internet → Load Balancer (152.70.18.57) → Backend API (Private) → Database
                                        ↓
                                   Object Storage
                                        ↓
                                   Data Processor (Private)
```

## Step 1: SSH Access Setup

First, get the private IPs of your compute instances:

```bash
cd infrastructure/terraform
terraform output -json | jq -r '.compute_backend_api_ip.value'
```

Since instances are in a private subnet, you'll need to:
1. Use OCI Bastion service, OR
2. Temporarily assign public IPs for initial setup

## Step 2: Deploy Backend API

### 2.1 Install Dependencies on Backend Instance

```bash
# SSH into backend instance
ssh -i ~/.ssh/your-key.pem opc@<backend-ip>

# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip python3.11-devel

# Install Node.js 20 (for frontend)
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs

# Install nginx
sudo yum install -y nginx

# Install git
sudo yum install -y git

# Install PostgreSQL client (if using database)
sudo yum install -y postgresql
```

### 2.2 Clone and Setup Application

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/AquaPredict.git
sudo chown -R opc:opc AquaPredict
cd AquaPredict

# Setup Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r modules/backend/requirements.txt
pip install gunicorn uvicorn
```

### 2.3 Configure Environment Variables

```bash
# Create .env file
cat > /opt/AquaPredict/.env << 'EOF'
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

# Google Earth Engine
GEE_SERVICE_ACCOUNT_JSON=/opt/AquaPredict/credentials/gee-service-account.json

# Database (when enabled)
# DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Model paths
MODEL_PATH=/opt/AquaPredict/models
EOF

chmod 600 /opt/AquaPredict/.env
```

### 2.4 Create Systemd Service for Backend API

```bash
sudo tee /etc/systemd/system/aquapredict-api.service > /dev/null << 'EOF'
[Unit]
Description=AquaPredict Backend API
After=network.target

[Service]
Type=notify
User=opc
Group=opc
WorkingDirectory=/opt/AquaPredict/modules/backend
Environment="PATH=/opt/AquaPredict/venv/bin"
EnvironmentFile=/opt/AquaPredict/.env
ExecStart=/opt/AquaPredict/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --access-logfile /var/log/aquapredict/access.log \
    --error-logfile /var/log/aquapredict/error.log \
    app.main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create log directory
sudo mkdir -p /var/log/aquapredict
sudo chown opc:opc /var/log/aquapredict

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable aquapredict-api
sudo systemctl start aquapredict-api
sudo systemctl status aquapredict-api
```

### 2.5 Configure Nginx Reverse Proxy

```bash
sudo tee /etc/nginx/conf.d/aquapredict.conf > /dev/null << 'EOF'
upstream backend_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
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
    }
    
    # Health check
    location /health {
        proxy_pass http://backend_api/health;
        access_log off;
    }
    
    # Static files (if serving frontend from same instance)
    location / {
        root /opt/AquaPredict/modules/frontend/out;
        try_files $uri $uri/ /index.html;
    }
}
EOF

# Test nginx configuration
sudo nginx -t

# Start nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Step 3: Deploy Frontend (Next.js)

### 3.1 Build Frontend

```bash
cd /opt/AquaPredict/modules/frontend

# Install dependencies
npm install

# Configure environment
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://152.70.18.57/api
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
EOF

# Build for production
npm run build

# Export static site (if using static export)
npm run export
```

### 3.2 Option A: Serve via Nginx (Static Export)

Already configured in nginx above. Frontend will be served from `/opt/AquaPredict/modules/frontend/out`

### 3.2 Option B: Run Next.js Server with PM2

```bash
# Install PM2 globally
sudo npm install -g pm2

# Start Next.js
cd /opt/AquaPredict/modules/frontend
pm2 start npm --name "aquapredict-frontend" -- start
pm2 save
pm2 startup

# Configure nginx to proxy to Next.js
sudo tee /etc/nginx/conf.d/aquapredict.conf > /dev/null << 'EOF'
upstream backend_api {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name _;
    
    # API endpoints
    location /api/ {
        proxy_pass http://backend_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

sudo nginx -t && sudo systemctl reload nginx
```

## Step 4: Deploy Data Processor

### 4.1 Setup on Data Processor Instance

```bash
# SSH into data processor instance
ssh -i ~/.ssh/your-key.pem opc@<processor-ip>

# Install dependencies (same as backend)
sudo yum update -y
sudo yum install -y python3.11 python3.11-pip git

# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/AquaPredict.git
sudo chown -R opc:opc AquaPredict
cd AquaPredict

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r modules/data_processor/requirements.txt
```

### 4.2 Create Systemd Service for Data Processor

```bash
sudo tee /etc/systemd/system/aquapredict-processor.service > /dev/null << 'EOF'
[Unit]
Description=AquaPredict Data Processor
After=network.target

[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=/opt/AquaPredict/modules/data_processor
Environment="PATH=/opt/AquaPredict/venv/bin"
EnvironmentFile=/opt/AquaPredict/.env
ExecStart=/opt/AquaPredict/venv/bin/python processor.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable aquapredict-processor
sudo systemctl start aquapredict-processor
```

## Step 5: Setup OCI Object Storage Access

### 5.1 Configure OCI CLI on Instances

```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configure OCI CLI
oci setup config

# Test access
oci os bucket list --compartment-id <your-compartment-id>
```

### 5.2 Use Instance Principals (Recommended)

Create a dynamic group and policies to allow instances to access Object Storage without API keys:

```bash
# In OCI Console:
# 1. Create Dynamic Group with rule:
#    ANY {instance.compartment.id = 'ocid1.compartment...'}
# 
# 2. Create Policy:
#    Allow dynamic-group aquapredict-instances to manage objects in compartment aquapredict
#    Allow dynamic-group aquapredict-instances to read buckets in compartment aquapredict
```

## Step 6: Monitoring and Logs

### 6.1 View Application Logs

```bash
# Backend API logs
sudo journalctl -u aquapredict-api -f

# Data Processor logs
sudo journalctl -u aquapredict-processor -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application logs
tail -f /var/log/aquapredict/access.log
tail -f /var/log/aquapredict/error.log
```

### 6.2 Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check from load balancer
curl http://152.70.18.57/health
```

## Step 7: SSL/TLS Setup (Optional but Recommended)

### 7.1 Install Certbot

```bash
sudo yum install -y certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot-renew.timer
```

## Quick Deployment Script

I'll create automated deployment scripts in the next step.

## Troubleshooting

### Service won't start
```bash
# Check service status
sudo systemctl status aquapredict-api
sudo journalctl -xe

# Check permissions
ls -la /opt/AquaPredict
```

### Can't access from load balancer
```bash
# Check if service is listening
sudo netstat -tlnp | grep 8000

# Check firewall
sudo firewall-cmd --list-all
```

### Object Storage access denied
```bash
# Verify OCI configuration
oci os bucket list --compartment-id <compartment-id>

# Check instance principal setup
```

## Next Steps

1. **Setup Bastion or VPN** for secure SSH access
2. **Configure monitoring** with OCI Monitoring service
3. **Setup automated backups**
4. **Configure CI/CD pipeline** for automated deployments
5. **Integrate ML models** (next phase)
