# AquaPredict Quick Start Deployment

## Current Infrastructure Status ✅

- **Load Balancer IP**: `152.70.18.57` (Your public endpoint)
- **Backend API**: `10.0.1.95` (Private subnet)
- **Data Processor**: `10.0.1.179` (Private subnet)
- **Object Storage Namespace**: `frxiensafavx`

## Step-by-Step Deployment

### Step 1: Setup SSH Access to Private Instances

Since your instances are in a private subnet, you need to access them via OCI Bastion or temporarily assign public IPs.

#### Option A: Use OCI Bastion Service (Recommended)

1. Go to OCI Console → Bastion
2. Create a Bastion in your VCN's public subnet
3. Create a session to connect to your instances

#### Option B: Temporarily Assign Public IPs

Let's temporarily enable public IPs for deployment:

```bash
cd ~/projects/AquaPredict/infrastructure/terraform

# Edit terraform.tfvars
nano terraform.tfvars

# Change this line:
# compute_assign_public_ip = false
# To:
# compute_assign_public_ip = true

# Apply changes
terraform apply -auto-approve
```

After deployment is complete, we'll remove the public IPs for security.

---

### Step 2: Get Instance Public IPs (if using Option B)

```bash
cd ~/projects/AquaPredict/infrastructure/terraform

# Get backend API IP
terraform state show module.compute.oci_core_instance.backend_api | grep public_ip

# Get data processor IP
terraform state show module.compute.oci_core_instance.data_processor | grep public_ip
```

---

### Step 3: Prepare Deployment Scripts

Make scripts executable:

```bash
cd ~/projects/AquaPredict/infrastructure/deployment/scripts
chmod +x setup_backend.sh
chmod +x setup_data_processor.sh
```

---

### Step 4: Copy Scripts to Backend Instance

```bash
# Get the public IP from Step 2, then:
BACKEND_IP="<your-backend-public-ip>"

# Copy setup script
scp -i ~/.ssh/your-key.pem \
    setup_backend.sh \
    opc@$BACKEND_IP:/tmp/

# SSH into backend
ssh -i ~/.ssh/your-key.pem opc@$BACKEND_IP
```

---

### Step 5: Run Backend Setup

On the backend instance:

```bash
# Run setup script
cd /tmp
bash setup_backend.sh

# When prompted, enter your repository URL:
# https://github.com/yourusername/AquaPredict.git
```

The script will:
- ✅ Install Python 3.11, Node.js, nginx
- ✅ Clone your repository
- ✅ Setup virtual environment
- ✅ Install dependencies
- ✅ Create systemd service
- ✅ Configure nginx
- ✅ Start the API

---

### Step 6: Configure OCI Credentials on Backend

Still on the backend instance:

```bash
# Setup OCI CLI
oci setup config

# You'll need:
# - User OCID (from terraform.tfvars)
# - Tenancy OCID (from terraform.tfvars)
# - Region: eu-frankfurt-1
# - Generate new API key or use existing

# Test access
oci os bucket list --compartment-id <your-compartment-id>
```

---

### Step 7: Setup Data Processor

From your local machine:

```bash
PROCESSOR_IP="<your-processor-public-ip>"

# Copy setup script
scp -i ~/.ssh/your-key.pem \
    setup_data_processor.sh \
    opc@$PROCESSOR_IP:/tmp/

# SSH into processor
ssh -i ~/.ssh/your-key.pem opc@$PROCESSOR_IP

# Run setup
cd /tmp
bash setup_data_processor.sh
```

---

### Step 8: Test Deployment

From your local machine:

```bash
# Test backend API via load balancer
curl http://152.70.18.57/health

# Should return: {"status": "healthy"}
```

---

### Step 9: Remove Public IPs (Security)

After deployment is complete:

```bash
cd ~/projects/AquaPredict/infrastructure/terraform

# Edit terraform.tfvars
nano terraform.tfvars

# Change back to:
compute_assign_public_ip = false

# Apply
terraform apply -auto-approve
```

---

## Alternative: Simple Manual Deployment

If you prefer to do it manually without scripts:

### Backend Instance Setup

```bash
# SSH into backend instance
ssh -i ~/.ssh/your-key.pem opc@<backend-ip>

# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install -y python3.11 python3.11-pip git nginx

# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/AquaPredict.git
sudo chown -R opc:opc AquaPredict
cd AquaPredict

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r modules/backend/requirements.txt
pip install gunicorn uvicorn

# Create simple systemd service
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

# Start service
sudo systemctl daemon-reload
sudo systemctl enable aquapredict-api
sudo systemctl start aquapredict-api

# Configure nginx
sudo tee /etc/nginx/conf.d/aquapredict.conf > /dev/null << 'EOF'
server {
    listen 80;
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
EOF

sudo systemctl start nginx
```

---

## Next Steps After Deployment

1. **Upload ML Models**
   ```bash
   # From your local machine
   scp -i ~/.ssh/your-key.pem -r models/* opc@<backend-ip>:/opt/AquaPredict/models/
   ```

2. **Upload Notebooks to OCI Data Science**
   - We'll do this in the next phase
   - You can upload .ipynb files directly to OCI Data Science

3. **Configure Environment Variables**
   - Edit `/opt/AquaPredict/.env` on each instance
   - Add API keys, credentials, etc.

4. **Setup Monitoring**
   - View logs: `sudo journalctl -u aquapredict-api -f`
   - Check status: `sudo systemctl status aquapredict-api`

---

## Troubleshooting

### Can't SSH to instances
- Check security list allows SSH (port 22)
- Verify you're using correct private key
- If using bastion, ensure session is active

### API not responding
```bash
# Check if service is running
sudo systemctl status aquapredict-api

# View logs
sudo journalctl -u aquapredict-api -f

# Check if port is listening
sudo netstat -tlnp | grep 8000
```

### Load balancer returns 502
- Backend service might not be running
- Check backend health: `curl http://10.0.1.95:8000/health`
- Verify security lists allow traffic from load balancer

---

## Ready to Deploy?

Choose your path:
- **Automated**: Use the setup scripts (recommended)
- **Manual**: Follow the manual steps above

Let me know when you're ready to start, and I'll guide you through each step!
