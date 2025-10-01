# Terraform Deployment Commands - AquaPredict

Quick reference for deploying AquaPredict infrastructure on OCI using Terraform.

---

## Prerequisites & Setup

```bash
# Install OCI CLI
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"

# Configure OCI CLI
oci setup config

# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/aquapredict_key

# Get required OCIDs
oci iam availability-domain list --compartment-id <tenancy-ocid>
cat ~/.oci/config | grep fingerprint
```

---

## Configuration

```bash
# Clone and configure
git clone https://github.com/yourusername/AquaPredict.git
cd AquaPredict/infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your values
```

**Key Variables** (terraform.tfvars):
```hcl
tenancy_ocid         = "ocid1.tenancy.oc1..xxx"
user_ocid            = "ocid1.user.oc1..xxx"
fingerprint          = "xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx"
private_key_path     = "~/.oci/oci_api_key.pem"
region               = "us-ashburn-1"
compartment_ocid     = "ocid1.compartment.oc1..xxx"
availability_domain  = "xxxx:US-ASHBURN-AD-1"
ssh_public_key       = "ssh-rsa AAAAB3..."
db_admin_password    = "SecureP@ssw0rd123!"
db_wallet_password   = "WalletP@ssw0rd123!"
db_app_password      = "AppP@ssw0rd123!"
gee_service_account_json = "{\"type\":\"service_account\",...}"
```

---

## Core Terraform Commands

```bash
# Initialize
terraform init
terraform init -upgrade  # Upgrade providers

# Validate & Format
terraform validate
terraform fmt -recursive

# Plan
terraform plan
terraform plan -out=tfplan

# Apply
terraform apply
terraform apply tfplan
terraform apply -auto-approve  # Skip confirmation

# Show State
terraform show
terraform state list
terraform output
terraform output -json

# Refresh
terraform refresh
```

---

## Module-Specific Deployment

```bash
# Deploy in order (recommended)
terraform apply -target=module.network -auto-approve
terraform apply -target=module.database -auto-approve
terraform apply -target=module.object_storage -auto-approve
terraform apply -target=module.compute -auto-approve
terraform apply -target=module.oke -auto-approve
terraform apply -target=module.data_science -auto-approve
terraform apply -auto-approve  # Apply remaining

# Individual modules
terraform plan -target=module.network
terraform apply -target=module.database
terraform output database_connection_string
```

---

## Post-Deployment Setup

```bash
# Configure kubectl
CLUSTER_OCID=$(terraform output -raw oke_cluster_id)
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_OCID \
  --file ~/.kube/config \
  --region us-ashburn-1
kubectl get nodes

# Download database wallet
mkdir -p ../../credentials/wallet
ADB_OCID=$(terraform state show 'module.database.oci_database_autonomous_database.adb[0]' | grep "^id " | awk '{print $3}' | tr -d '"')
oci db autonomous-database generate-wallet \
  --autonomous-database-id $ADB_OCID \
  --file ../../credentials/wallet.zip \
  --password "$(terraform output -raw db_wallet_password)"
unzip ../../credentials/wallet.zip -d ../../credentials/wallet/

# Test database connection
export TNS_ADMIN=~/projects/AquaPredict/credentials/wallet
sqlplus admin/$(terraform output -raw db_admin_password)@aquapredict_high

# SSH to compute instance
BACKEND_IP=$(terraform output -raw compute_backend_api_ip)
ssh -i ~/.ssh/aquapredict_key opc@$BACKEND_IP
```

---

## Verification Commands

```bash
# List all resources
terraform state list
terraform state list | wc -l

# Verify specific resources
oci compute instance list --compartment-id $(terraform output -raw compartment_id) --output table
oci db autonomous-database list --compartment-id $(terraform output -raw compartment_id) --output table
oci os bucket list --compartment-id $(terraform output -raw compartment_id)
oci ce cluster list --compartment-id $(terraform output -raw compartment_id)
```

---

## Maintenance

```bash
# Update infrastructure
git pull origin main
terraform plan
terraform apply

# Scale resources
terraform apply -var="adb_cpu_core_count=4"
terraform apply -var="oke_node_pool_size=5"

# Taint/replace resource
terraform taint 'module.compute.oci_core_instance.backend_api'
terraform apply

# State management
terraform state mv 'module.old.resource' 'module.new.resource'
terraform state rm 'module.compute.oci_core_instance.old_instance'
terraform import 'module.network.oci_core_vcn.vcn' <vcn-ocid>
```

---

## Troubleshooting

```bash
# Debug mode
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform-debug.log
terraform apply
tail -f terraform-debug.log

# Common fixes
terraform refresh
terraform validate
oci iam user get --user-id $(terraform output -raw user_ocid)  # Test auth
oci limits value list --compartment-id <compartment-id> --service-name compute  # Check limits
```

---

## Cleanup

```bash
# Destroy in reverse order (recommended)
terraform destroy -target=module.data_science -auto-approve
terraform destroy -target=module.oke -auto-approve
terraform destroy -target=module.compute -auto-approve
terraform destroy -target=module.database -auto-approve
terraform destroy -target=module.object_storage -auto-approve
terraform destroy -target=module.network -auto-approve
terraform destroy -auto-approve

# Or destroy all at once
terraform destroy

# Manual cleanup (if Terraform fails)
oci compute instance terminate --instance-id <instance-ocid> --force
oci db autonomous-database delete --autonomous-database-id <adb-ocid> --force
oci os bucket delete --bucket-name aquapredict-data-raw --force
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `terraform init` | Initialize working directory |
| `terraform plan` | Preview changes |
| `terraform apply` | Apply changes |
| `terraform destroy` | Destroy infrastructure |
| `terraform output` | Show outputs |
| `terraform state list` | List resources |
| `terraform fmt` | Format code |
| `terraform validate` | Validate syntax |

---

**Version**: 1.0.0 | **Updated**: 2025-10-01
