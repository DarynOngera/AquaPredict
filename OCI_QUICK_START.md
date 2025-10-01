# AquaPredict OCI Quick Start Guide

Get AquaPredict running on OCI in under 30 minutes.

## Prerequisites Checklist

- [ ] OCI account with admin access
- [ ] OCI CLI installed and configured
- [ ] Terraform v1.5+ installed
- [ ] SSH key pair generated
- [ ] Google Earth Engine service account JSON

## 5-Step Deployment

### Step 1: Configure OCI (5 minutes)

```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configure OCI CLI
oci setup config
# Enter: User OCID, Tenancy OCID, Region, API Key path

# Verify configuration
oci iam region list
```

### Step 2: Prepare Configuration (5 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/AquaPredict.git
cd AquaPredict

# Copy and edit configuration
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values
```

**Required Values:**
```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..xxx"  # From OCI Console
user_ocid        = "ocid1.user.oc1..xxx"     # From OCI Console
fingerprint      = "xx:xx:..."               # From API Key
private_key_path = "~/.oci/oci_api_key.pem"  # Your API key
region           = "us-ashburn-1"            # Your region
compartment_ocid = "ocid1.compartment.oc1..xxx"

# Get availability domain
availability_domain = "xxxx:US-ASHBURN-AD-1"  # Run: oci iam availability-domain list

# Set passwords (must meet complexity requirements)
db_admin_password = "SecureP@ssw0rd123!"
db_wallet_password = "WalletP@ssw0rd123!"
db_app_password = "AppP@ssw0rd123!"

# Add your SSH public key
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2E..."

# Add GEE service account JSON (single line, escaped quotes)
gee_service_account_json = "{\"type\":\"service_account\",...}"
```

### Step 3: Deploy Infrastructure (15 minutes)

```bash
# Run automated deployment script
cd ../scripts
chmod +x deploy-infrastructure.sh
./deploy-infrastructure.sh
```

The script will:
1. ✅ Check prerequisites
2. ✅ Initialize Terraform
3. ✅ Validate configuration
4. ✅ Create deployment plan
5. ✅ Apply infrastructure (requires confirmation)
6. ✅ Configure kubectl
7. ✅ Download database wallet
8. ✅ Display summary

**Expected Output:**
```
[INFO] Deployment Summary
========================================
Backend API IP: 123.45.67.89
Load Balancer IP: 123.45.67.90
Data Science Notebook: https://notebook.us-ashburn-1.oci.oraclecloud.com/...

Object Storage Buckets:
  - raw_data: aquapredict-data-raw
  - processed: aquapredict-data-processed
  - models: aquapredict-models
  - reports: aquapredict-reports
  - backups: aquapredict-backups
========================================
```

### Step 4: Setup Database (3 minutes)

```bash
# Run database setup script
chmod +x setup-database.sh
./setup-database.sh

# When prompted, enter connection string:
# aquapredict_app/<password>@aquapredict_high

# Insert sample data? yes
```

This creates:
- Spatial tables with indexes
- Stored procedures for geospatial queries
- Sample data for testing

### Step 5: Verify Deployment (2 minutes)

```bash
# Test API
curl http://<load-balancer-ip>/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-01T12:00:00Z","services":{"gee":false,"models":false,"settings":true,"export":true}}

# Test database
export TNS_ADMIN=~/credentials/wallet
sqlplus aquapredict_app/<password>@aquapredict_high <<EOF
SELECT COUNT(*) FROM locations;
EOF

# Access Data Science Notebook
# Open the URL from deployment summary in your browser
```

## What's Deployed?

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **Compute - Backend API** | 2 OCPUs, 16GB RAM | FastAPI backend service |
| **Compute - Data Processor** | 2 OCPUs, 16GB RAM | GEE data processing |
| **Autonomous Database** | 2 OCPUs, 1TB, Spatial | Geospatial data storage |
| **Object Storage** | 5 buckets | Data, models, reports |
| **Load Balancer** | Flexible, 10-100 Mbps | High availability |
| **Data Science** | Notebook + Model Catalog | ML training & deployment |

### Network Architecture

```
Internet
    │
    ▼
┌─────────────┐
│Load Balancer│ (Public)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│ Backend API │────▶│   Database   │
└─────────────┘     │   (Spatial)  │
       │            └──────────────┘
       ▼
┌─────────────┐     ┌──────────────┐
│Data Processor│────▶│Object Storage│
└─────────────┘     └──────────────┘
```

## Quick Commands

### Infrastructure Management

```bash
# View all resources
cd infrastructure/terraform
terraform show

# Get outputs
terraform output

# Update infrastructure
terraform plan
terraform apply

# Destroy infrastructure (careful!)
terraform destroy
```

### Access Resources

```bash
# SSH to Backend API
ssh -i ~/.ssh/aquapredict_key opc@<backend-api-ip>

# Connect to Database
sqlplus aquapredict_app/<password>@aquapredict_high

# Access Object Storage
oci os object list --bucket-name aquapredict-models

# View Data Science Notebook
terraform output data_science_notebook_url
```

### Monitor Services

```bash
# API Status
curl http://<load-balancer-ip>/health

# API Logs
ssh opc@<backend-ip> "sudo journalctl -u aquapredict-api -f"

# Database Sessions
sqlplus aquapredict_app/<password>@aquapredict_high <<EOF
SELECT username, status FROM v\$session WHERE username = 'AQUAPREDICT_APP';
EOF
```

## Next Steps

### 1. Configure Domain & SSL

```bash
# Point your domain to Load Balancer IP
# api.yourdomain.com -> <load-balancer-ip>

# Install SSL certificate
ssh opc@<backend-ip>
sudo certbot --nginx -d api.yourdomain.com
```

### 2. Setup Data Science

```bash
cd infrastructure/scripts
chmod +x setup-data-science.sh
./setup-data-science.sh

# Access notebook and install environment
# conda env create -f environments/aquapredict_env.yaml
```

### 3. Load Real Data

```bash
# Configure GEE credentials on backend
ssh opc@<backend-ip>
sudo nano /opt/aquapredict/.env
# Add GEE_SERVICE_ACCOUNT=<your-json>

# Restart API
sudo systemctl restart aquapredict-api
```

### 4. Train Models

```bash
# In Data Science Notebook
python notebooks/01_aquifer_model_training.py

# Deploy model
python scripts/deploy_model.py <model-ocid> aquifer-prediction-v1
```

### 5. Deploy Frontend

```bash
# Follow FRONTEND_DEPLOYMENT.md
cd modules/frontend
npm install
npm run build

# Deploy to OKE or static hosting
```

## Troubleshooting

### Issue: Terraform apply fails with "Service limit exceeded"

**Solution:**
```bash
# Check limits
oci limits value list --compartment-id <compartment-ocid> --service-name compute

# Request increase in OCI Console → Governance → Limits
```

### Issue: Cannot connect to database

**Solution:**
```bash
# Verify wallet location
echo $TNS_ADMIN
ls -la $TNS_ADMIN

# Test connection
tnsping aquapredict_high

# Re-download wallet if needed
terraform output database_wallet_path
```

### Issue: API returns 502 Bad Gateway

**Solution:**
```bash
# Check API service
ssh opc@<backend-ip>
sudo systemctl status aquapredict-api
sudo docker ps

# Check logs
sudo docker logs aquapredict-api

# Restart if needed
sudo systemctl restart aquapredict-api
```

### Issue: High costs

**Solution:**
```bash
# Use Always Free tier
# Edit terraform.tfvars:
adb_is_free_tier = true
adb_cpu_core_count = 1

# Stop notebook when not in use
oci data-science notebook-session deactivate --notebook-session-id <ocid>

# Stop compute instances
oci compute instance action --instance-id <ocid> --action STOP
```

## Cost Estimate

### Production Configuration
- **Monthly**: ~$703
  - Compute: $140
  - Database: $520
  - Storage: $23
  - Load Balancer: $20

### Development Configuration (Always Free)
- **Monthly**: $0
  - 2 Autonomous DBs (1 OCPU each)
  - 2 Compute instances (AMD, 1/8 OCPU)
  - 10GB Object Storage

## Support & Resources

- **Documentation**: [OCI_DEPLOYMENT_GUIDE.md](./OCI_DEPLOYMENT_GUIDE.md)
- **OCI Docs**: https://docs.oracle.com/iaas
- **Terraform Provider**: https://registry.terraform.io/providers/oracle/oci
- **Community**: https://cloud.oracle.com/community

## Cleanup

To remove all resources:

```bash
cd infrastructure/terraform
terraform destroy

# Confirm by typing: yes
```

**Warning**: This will delete all data, including databases and object storage. Make backups first!

---

**Deployment Time**: ~30 minutes  
**Difficulty**: Intermediate  
**Cost**: $0 (Free Tier) to $703/month (Production)

**Questions?** Open an issue on GitHub or contact the team.
