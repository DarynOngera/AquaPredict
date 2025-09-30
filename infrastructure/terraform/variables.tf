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
  description = "Database Admin Password"
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

# Object Storage
variable "object_storage_namespace" {
  description = "Object Storage Namespace"
  type        = string
}
