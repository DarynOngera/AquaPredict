variable "tenancy_ocid" {
  description = "OCI Tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "OCI User OCID"
  type        = string
}

variable "fingerprint" {
  description = "OCI API Key Fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "Path to OCI API Private Key"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

# Network
variable "vcn_cidr" {
  description = "VCN CIDR Block"
  type        = string
  default     = "10.0.0.0/16"
}

# Autonomous Database
variable "db_name" {
  description = "Database Name"
  type        = string
  default     = "aquapredict"
}

variable "db_admin_password" {
  description = "Database Admin Password (12-30 chars with uppercase, lowercase, number, special char)"
  type        = string
  sensitive   = true
}

variable "db_wallet_password" {
  description = "Database Wallet Password"
  type        = string
  sensitive   = true
}

variable "db_app_user" {
  description = "Application Database User"
  type        = string
  default     = "aquapredict_app"
}

variable "db_app_password" {
  description = "Application User Password"
  type        = string
  sensitive   = true
}

variable "adb_cpu_core_count" {
  description = "ADB CPU Core Count"
  type        = number
  default     = 2
}

variable "adb_storage_tb" {
  description = "ADB Storage in TB"
  type        = number
  default     = 1
}

variable "adb_is_free_tier" {
  description = "Use Always Free tier"
  type        = bool
  default     = false
}

variable "adb_enable_auto_scaling" {
  description = "Enable auto-scaling for ADB"
  type        = bool
  default     = true
}

variable "adb_create_database" {
  description = "Create Autonomous Database (requires feature to be enabled)"
  type        = bool
  default     = false
}

# OKE
variable "oke_cluster_name" {
  description = "OKE Cluster Name"
  type        = string
  default     = "aquapredict-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes Version"
  type        = string
  default     = "v1.28.2"
}

variable "oke_node_pool_size" {
  description = "OKE Node Pool Size"
  type        = number
  default     = 3
}

variable "oke_node_shape" {
  description = "OKE Node Shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

# Compute Instances
variable "availability_domain" {
  description = "Availability Domain for compute instances"
  type        = string
}

variable "compute_instance_shape" {
  description = "Compute instance shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "compute_instance_ocpus" {
  description = "Number of OCPUs per compute instance"
  type        = number
  default     = 2
}

variable "compute_instance_memory_gb" {
  description = "Memory in GB per compute instance"
  type        = number
  default     = 16
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "compute_assign_public_ip" {
  description = "Assign public IP to backend API instance"
  type        = bool
  default     = true
}

variable "compute_create_load_balancer" {
  description = "Create load balancer for API"
  type        = bool
  default     = true
}

# Google Earth Engine
variable "gee_service_account_json" {
  description = "Google Earth Engine service account JSON"
  type        = string
  sensitive   = true
}

# Data Science
variable "ds_deploy_models" {
  description = "Deploy models to OCI Data Science endpoints"
  type        = bool
  default     = false
}

# Environment
variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}
