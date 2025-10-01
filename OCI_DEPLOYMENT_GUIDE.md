# AquaPredict OCI Infrastructure Deployment Guide

Complete guide for deploying AquaPredict on Oracle Cloud Infrastructure (OCI).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Component Configuration](#component-configuration)
6. [Deployment Steps](#deployment-steps)
7. [Post-Deployment](#post-deployment)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Cost Optimization](#cost-optimization)

---

## Prerequisites

### Required Tools

- **OCI CLI** (v3.0+): `bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"`
- **Terraform** (v1.5+): [Download](https://www.terraform.io/downloads)
- **kubectl** (v1.28+): [Install Guide](https://kubernetes.io/docs/tasks/tools/)
- **SQLPlus** (for database setup): [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html)
- **Git**: For cloning the repository

### OCI Account Requirements

- Active OCI account with sufficient credits
- Required IAM permissions:
  - Manage compute instances
  - Manage autonomous databases
  - Manage object storage
  - Manage OKE clusters
  - Manage data science resources
  - Manage networking (VCN, subnets, security lists)

### API Keys

1. **OCI API Key**: Generate in OCI Console → User Settings → API Keys
2. **Google Earth Engine Service Account**: [GEE Setup Guide](https://developers.google.com/earth-engine/guides/service_account)
3. **SSH Key Pair**: `ssh-keygen -t rsa -b 4096 -f ~/.ssh/aquapredict_key`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        OCI Tenancy                               │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Compartment: aquapredict                       │ │
│  │                                                             │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │                    VCN (10.0.0.0/16)                  │  │ │
│  │  │                                                        │  │ │
│  │  │  Public Subnet          Private Subnet                │  │ │
│  │  │  ┌──────────────┐      ┌──────────────┐              │  │ │
│  │  │  │ Load Balancer│      │ Backend API  │              │  │ │
│  │  │  │              │      │ Compute      │              │  │ │
│  │  │  └──────┬───────┘      └──────┬───────┘              │  │ │
│  │  │         │                     │                       │  │ │
│  │  │         │      ┌──────────────┴───────────┐          │  │ │
│  │  │         │      │ Data Processor Compute   │          │  │ │
│  │  │         │      └──────────────┬───────────┘          │  │ │
│  │  │         │                     │                       │  │ │
│  │  │         │      ┌──────────────┴───────────┐          │  │ │
│  │  │         │      │ Autonomous Database      │          │  │ │
│  │  │         │      │ (Spatial + Auto-scaling) │          │  │ │
│  │  │         │      └──────────────────────────┘          │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │ Object       │  │ Data Science │  │ OKE Cluster  │    │ │
│  │  │ Storage      │  │ Notebooks    │  │ (Optional)   │    │ │
│  │  │              │  │ + Models     │  │              │    │ │
│  │  │ • Raw Data   │  │              │  │ • Frontend   │    │ │
│  │  │ • Processed  │  │ Model Deploy │  │ • Services   │    │ │
│  │  │ • Models     │  │ Endpoints    │  │              │    │ │
│  │  │ • Reports    │  │              │  │              │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Components

1. **Compute Instances**
   - Backend API server (VM.Standard.E4.Flex, 2 OCPUs, 16GB RAM)
   - Data processor (VM.Standard.E4.Flex, 2 OCPUs, 16GB RAM)
   - Load balancer for high availability

2. **Autonomous Database**
   - Oracle Spatial for geospatial queries
   - Auto-scaling enabled (2-8 OCPUs)
   - 1TB storage with auto-expansion

3. **Object Storage**
   - Raw data bucket (with lifecycle policies)
   - Processed data bucket
   - Models bucket (versioned)
   - Reports bucket (auto-archive)
   - Backups bucket

4. **OCI Data Science**
   - Notebook session for model development
   - Model catalog for versioning
   - Model deployment endpoints (optional)
   - Scheduled training jobs

5. **OKE (Optional)**
   - Kubernetes cluster for containerized services
   - 3-node pool with auto-scaling

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AquaPredict.git
cd AquaPredict
```

### 2. Configure OCI CLI

```bash
oci setup config
# Follow prompts to configure:
# - User OCID
# - Tenancy OCID
# - Region
# - API Key path
```

### 3. Prepare Configuration

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 4. Deploy Infrastructure

```bash
chmod +x ../scripts/deploy-infrastructure.sh
../scripts/deploy-infrastructure.sh
```

This script will:
- Initialize Terraform
- Validate configuration
- Create infrastructure plan
- Apply changes (with confirmation)
- Configure kubectl
- Download database wallet
- Display deployment summary

---

## Detailed Setup

### Step 1: OCI Configuration

#### 1.1 Create Compartment (Optional)

```bash
oci iam compartment create \
  --compartment-id <tenancy-ocid> \
  --name aquapredict \
  --description "AquaPredict Geospatial AI Platform"
```

#### 1.2 Get Availability Domain

```bash
oci iam availability-domain list --compartment-id <compartment-ocid>
```

Note the availability domain name for `terraform.tfvars`.

### Step 2: Configure Variables

Edit `infrastructure/terraform/terraform.tfvars`:

```hcl
# OCI Authentication
tenancy_ocid     = "ocid1.tenancy.oc1..xxx"
user_ocid        = "ocid1.user.oc1..xxx"
fingerprint      = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path = "~/.oci/oci_api_key.pem"
region           = "us-ashburn-1"
compartment_ocid = "ocid1.compartment.oc1..xxx"

# Availability Domain
availability_domain = "xxxx:US-ASHBURN-AD-1"

# Database Configuration
db_name           = "aquapredict"
db_admin_password = "SecureP@ssw0rd123!"
db_wallet_password = "WalletP@ssw0rd123!"
db_app_password   = "AppP@ssw0rd123!"

# SSH Key
ssh_public_key = "ssh-rsa AAAAB3NzaC1yc2E... your-email@example.com"

# Google Earth Engine
gee_service_account_json = "{\"type\":\"service_account\",...}"
```

### Step 3: Deploy Infrastructure

#### 3.1 Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

#### 3.2 Validate Configuration

```bash
terraform validate
```

#### 3.3 Plan Deployment

```bash
terraform plan -out=tfplan
```

Review the plan carefully. Expected resources:
- 1 Compartment
- 1 VCN with subnets
- 2 Compute instances
- 1 Autonomous Database
- 5 Object Storage buckets
- 1 Load Balancer
- 1 Data Science project
- 1 Notebook session

#### 3.4 Apply Configuration

```bash
terraform apply tfplan
```

This will take 15-30 minutes.

### Step 4: Database Setup

#### 4.1 Download Wallet

```bash
cd ../scripts
chmod +x setup-database.sh
./setup-database.sh
```

#### 4.2 Create Schema

The script will:
- Extract wallet
- Create tables with spatial indexes
- Create stored procedures
- Insert sample data (optional)

### Step 5: Data Science Setup

```bash
chmod +x setup-data-science.sh
./setup-data-science.sh
```

This creates:
- Conda environment specification
- Training notebooks
- Deployment scripts
- Batch prediction scripts

---

## Component Configuration

### Compute Instances

#### Backend API Instance

**Access via SSH:**
```bash
ssh -i ~/.ssh/aquapredict_key opc@<backend-api-ip>
```

**Check API Status:**
```bash
sudo systemctl status aquapredict-api
sudo docker ps
curl http://localhost:8000/health
```

**View Logs:**
```bash
sudo journalctl -u aquapredict-api -f
sudo docker logs aquapredict-api -f
```

#### Data Processor Instance

**Access:**
```bash
ssh -i ~/.ssh/aquapredict_key opc@<processor-ip>
```

**Check Status:**
```bash
sudo systemctl status aquapredict-processor
```

### Autonomous Database

#### Connect via SQLPlus

```bash
export TNS_ADMIN=~/credentials/wallet
sqlplus aquapredict_app/<password>@aquapredict_high
```

#### Common Queries

```sql
-- Check table counts
SELECT table_name, num_rows 
FROM user_tables 
ORDER BY table_name;

-- View recent predictions
SELECT * FROM predictions 
ORDER BY created_at DESC 
FETCH FIRST 10 ROWS ONLY;

-- Spatial query: locations within 50km
SELECT location_id, latitude, longitude
FROM TABLE(find_locations_within_radius(-1.2921, 36.8219, 50));
```

### Object Storage

#### Upload Files via OCI CLI

```bash
# Upload model
oci os object put \
  --bucket-name aquapredict-models \
  --file model.pkl \
  --name models/aquifer_v1/model.pkl

# List objects
oci os object list \
  --bucket-name aquapredict-models \
  --prefix models/
```

### Data Science

#### Access Notebook Session

1. Get URL: `terraform output data_science_notebook_url`
2. Open in browser
3. Authenticate with OCI credentials

#### Install Environment

```bash
# In notebook terminal
conda env create -f environments/aquapredict_env.yaml
conda activate aquapredict_ml
```

#### Train Model

```bash
python notebooks/01_aquifer_model_training.py
```

---

## Post-Deployment

### 1. Configure DNS

Point your domain to the Load Balancer IP:

```bash
# Get Load Balancer IP
terraform output compute_load_balancer_ip

# Create DNS A record
api.aquapredict.com -> <load-balancer-ip>
```

### 2. Setup SSL Certificate

```bash
ssh -i ~/.ssh/aquapredict_key opc@<backend-api-ip>

# Install certificate
sudo certbot --nginx -d api.aquapredict.com
```

### 3. Configure Monitoring

#### Enable OCI Monitoring

```bash
# Create alarm for high CPU
oci monitoring alarm create \
  --compartment-id <compartment-ocid> \
  --display-name "High CPU Alert" \
  --metric-compartment-id <compartment-ocid> \
  --namespace oci_computeagent \
  --query "CpuUtilization[1m].mean() > 80"
```

### 4. Setup Backups

#### Database Backups

Autonomous Database has automatic backups. Configure retention:

```bash
oci db autonomous-database update \
  --autonomous-database-id <adb-ocid> \
  --backup-retention-period-in-days 30
```

#### Object Storage Lifecycle

Already configured in Terraform:
- Raw data → Archive after 90 days
- Reports → Delete after 365 days

---

## Monitoring & Maintenance

### Health Checks

```bash
# API Health
curl http://<load-balancer-ip>/health

# Database Connection
sqlplus aquapredict_app/<password>@aquapredict_high <<EOF
SELECT 'Connected' FROM dual;
EOF

# Object Storage
oci os bucket get --bucket-name aquapredict-models
```

### Performance Monitoring

#### Database Performance

```sql
-- Active sessions
SELECT username, status, sql_id 
FROM v$session 
WHERE username = 'AQUAPREDICT_APP';

-- Top SQL by execution time
SELECT sql_id, elapsed_time, executions 
FROM v$sql 
ORDER BY elapsed_time DESC 
FETCH FIRST 10 ROWS ONLY;
```

#### Compute Metrics

```bash
# CPU and Memory
ssh opc@<backend-ip> "top -bn1 | head -20"

# Disk usage
ssh opc@<backend-ip> "df -h"
```

### Log Analysis

```bash
# API logs
ssh opc@<backend-ip> "sudo tail -f /var/log/aquapredict/api.log"

# Database audit logs
sqlplus aquapredict_app/<password>@aquapredict_high <<EOF
SELECT * FROM audit_logs 
ORDER BY created_at DESC 
FETCH FIRST 20 ROWS ONLY;
EOF
```

---

## Troubleshooting

### Common Issues

#### 1. Terraform Apply Fails

**Error: "Service limit exceeded"**
```bash
# Check service limits
oci limits value list --compartment-id <compartment-ocid> --service-name compute

# Request limit increase in OCI Console
```

**Error: "Invalid credentials"**
```bash
# Verify OCI CLI config
oci iam user get --user-id <user-ocid>

# Regenerate API key if needed
```

#### 2. Database Connection Issues

**Error: "TNS:could not resolve the connect identifier"**
```bash
# Check TNS_ADMIN
echo $TNS_ADMIN

# Verify wallet files
ls -la $TNS_ADMIN

# Test connection
tnsping aquapredict_high
```

#### 3. Compute Instance Not Accessible

```bash
# Check instance status
oci compute instance get --instance-id <instance-ocid>

# Check security list rules
oci network security-list list --compartment-id <compartment-ocid>

# Verify SSH key
ssh-keygen -lf ~/.ssh/aquapredict_key.pub
```

#### 4. Model Training Fails

```bash
# Check notebook session status
oci data-science notebook-session get --notebook-session-id <session-ocid>

# View notebook logs
# Access notebook terminal and check:
conda list
python --version
```

### Getting Help

- **OCI Support**: [support.oracle.com](https://support.oracle.com)
- **Documentation**: [docs.oracle.com/iaas](https://docs.oracle.com/iaas)
- **Community**: [cloud.oracle.com/community](https://cloud.oracle.com/community)

---

## Cost Optimization

### Estimated Monthly Costs

| Component | Configuration | Estimated Cost |
|-----------|--------------|----------------|
| Compute (2 instances) | 2 OCPUs, 16GB RAM each | $140 |
| Autonomous Database | 2 OCPUs, 1TB storage | $520 |
| Object Storage | 1TB standard | $23 |
| Data Science Notebook | 4 OCPUs (when active) | $0.50/hour |
| Load Balancer | Flexible, 10-100 Mbps | $20 |
| **Total** | | **~$703/month** |

### Cost Reduction Strategies

#### 1. Use Always Free Tier

```hcl
# In terraform.tfvars
adb_is_free_tier = true
adb_cpu_core_count = 1
```

Free tier includes:
- 2 Autonomous Databases (1 OCPU each)
- 2 Compute instances (AMD, 1/8 OCPU each)
- 10GB Object Storage

#### 2. Auto-Scaling

Already enabled for:
- Autonomous Database (scales down when idle)
- OKE node pool (if deployed)

#### 3. Stop Non-Production Resources

```bash
# Stop notebook session when not in use
oci data-science notebook-session deactivate \
  --notebook-session-id <session-ocid>

# Stop compute instances
oci compute instance action \
  --instance-id <instance-ocid> \
  --action STOP
```

#### 4. Use Archive Storage

Objects automatically moved to archive tier:
- Raw data after 90 days
- Reports after immediate use

#### 5. Monitor Usage

```bash
# Check current usage
oci usage-api usage-summary list \
  --tenant-id <tenancy-ocid> \
  --time-usage-started 2025-09-01T00:00:00Z \
  --time-usage-ended 2025-10-01T00:00:00Z \
  --granularity DAILY
```

---

## Next Steps

1. **Deploy Frontend**: Follow `FRONTEND_DEPLOYMENT.md`
2. **Configure CI/CD**: Setup GitHub Actions for automated deployments
3. **Load Real Data**: Import GEE data using data ingestion scripts
4. **Train Models**: Use Data Science notebooks to train production models
5. **Setup Monitoring**: Configure OCI Monitoring and Notifications
6. **Performance Tuning**: Optimize database queries and API endpoints
7. **Security Hardening**: Implement WAF, enable audit logs, rotate credentials

---

## Additional Resources

- [OCI Documentation](https://docs.oracle.com/iaas)
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [Oracle Spatial Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/spatl/)
- [OCI Data Science](https://docs.oracle.com/en-us/iaas/data-science/using/data-science.htm)
- [Project README](./README.md)
- [API Documentation](./docs/API.md)

---

**Last Updated**: 2025-10-01  
**Version**: 1.0.0  
**Maintainer**: AquaPredict Team
