# Deploy AquaPredict - Step by Step

## Your Infrastructure is Ready! 🎉

- **Load Balancer**: `152.70.18.57`
- **Backend API**: `10.0.1.95` (private)
- **Data Processor**: `10.0.1.179` (private)

---

## Quick Deploy Using OCI Cloud Shell (5 minutes)

### Step 1: Open OCI Cloud Shell

1. Go to: https://cloud.oracle.com
2. Click the **Cloud Shell** icon `>_` in the top-right corner
3. Wait for Cloud Shell to start

### Step 2: Upload Deployment Scripts to Cloud Shell

In Cloud Shell, run:

```bash
# Create directory
mkdir -p ~/aquapredict-deploy
cd ~/aquapredict-deploy

# Download setup scripts (we'll create them inline)
cat > setup_backend.sh << 'SCRIPT_END'
#!/bin/bash
set -e

echo "=== Setting up AquaPredict Backend ==="

# Update system
sudo yum update -y

# Install dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# Clone repository
cd /opt
if [ ! -d "AquaPredict" ]; then
    read -p "Enter GitHub repo URL: " REPO_URL
    sudo git clone $REPO_URL AquaPredict
    sudo chown -R opc:opc AquaPredict
fi

cd /opt/AquaPredict

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install fastapi uvicorn gunicorn pydantic python-dotenv

# Create systemd service
sudo tee /etc/systemd/system/aquapredict-api.service > /dev/null << 'EOF'
[Unit]
Description=AquaPredict API
After=network.target

[Service]
Type=notify
User=opc
WorkingDirectory=/opt/AquaPredict/modules/backend
Environment="PATH=/opt/AquaPredict/venv/bin"
ExecStart=/opt/AquaPredict/venv/bin/gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    app.main:app

Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
sudo tee /etc/nginx/conf.d/aquapredict.conf > /dev/null << 'EOF'
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Start services
sudo systemctl daemon-reload
sudo systemctl enable aquapredict-api nginx
sudo systemctl start aquapredict-api nginx

echo "✅ Backend setup complete!"
echo "Test: curl http://localhost:8000/health"
SCRIPT_END

chmod +x setup_backend.sh
```

### Step 3: SSH to Backend Instance

From Cloud Shell:

```bash
# SSH to backend (Cloud Shell has access to private subnets)
ssh -i ~/.ssh/id_rsa opc@10.0.1.95
```

**If you don't have SSH key in Cloud Shell:**

```bash
# Generate SSH key
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""

# Display public key
cat ~/.ssh/id_rsa.pub

# Copy this key and add it to your instance via OCI Console:
# Compute → Instances → aquapredict-backend-api → Edit → Add SSH Key
```

### Step 4: Run Setup on Backend

Once connected to backend instance:

```bash
# Copy the setup script content (from Step 2) and create it on the instance
cat > setup_backend.sh << 'SCRIPT_END'
[paste the script content here]
SCRIPT_END

chmod +x setup_backend.sh

# Run setup
./setup_backend.sh

# When prompted for repo URL, enter:
# https://github.com/DarynOngera/AquaPredict.git
```

### Step 5: Verify Backend is Running

```bash
# Check service status
sudo systemctl status aquapredict-api

# Test locally
curl http://localhost:8000/health

# View logs
sudo journalctl -u aquapredict-api -f
```

### Step 6: Test from Load Balancer

From your local machine or Cloud Shell:

```bash
curl http://152.70.18.57/health
```

---

## Alternative: Manual Quick Setup

If you prefer to do it manually:

### On Backend Instance (10.0.1.95):

```bash
# 1. SSH via Cloud Shell
ssh opc@10.0.1.95

# 2. Install Python and dependencies
sudo yum install -y python3.11 python3.11-pip git nginx

# 3. Clone your repo
cd /opt
sudo git clone https://github.com/DarynOngera/AquaPredict.git
sudo chown -R opc:opc AquaPredict
cd AquaPredict

# 4. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 5. Install packages
pip install fastapi uvicorn gunicorn pydantic python-dotenv requests

# 6. Test run (temporary)
cd modules/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Press Ctrl+C when done testing

# 7. Create systemd service (for permanent deployment)
# Follow the systemd service creation from the script above
```

---

## What to Do After Deployment

### 1. Upload Your ML Models

```bash
# From your local machine, via Cloud Shell
scp -r models/* opc@10.0.1.95:/opt/AquaPredict/models/
```

### 2. Upload Your Notebooks

We'll integrate these with OCI Data Science in the next step.

### 3. Configure Environment Variables

```bash
# On backend instance
nano /opt/AquaPredict/.env

# Add:
OCI_NAMESPACE=frxiensafavx
OCI_REGION=eu-frankfurt-1
# ... other configs
```

---

## Troubleshooting

### Can't SSH from Cloud Shell?

Make sure your SSH public key is added to the instance:
1. Generate key in Cloud Shell: `ssh-keygen`
2. Get public key: `cat ~/.ssh/id_rsa.pub`
3. Add to instance via OCI Console

### Service won't start?

```bash
# Check logs
sudo journalctl -u aquapredict-api -xe

# Check if Python app runs manually
cd /opt/AquaPredict/modules/backend
source /opt/AquaPredict/venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Load balancer returns 502?

- Check if backend service is running: `sudo systemctl status aquapredict-api`
- Test backend directly: `curl http://10.0.1.95:8000/health`
- Check nginx: `sudo systemctl status nginx`

---

## Ready?

**Start here**: Open https://cloud.oracle.com and click the Cloud Shell icon!

Then follow Step 2 onwards. I'll help you with each step.
