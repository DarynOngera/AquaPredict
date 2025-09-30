terraform {
  required_version = ">= 1.5"
  
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Compartment for AquaPredict
resource "oci_identity_compartment" "aquapredict" {
  compartment_id = var.tenancy_ocid
  description    = "AquaPredict Geospatial AI Platform"
  name           = "aquapredict"
  
  enable_delete = false
}

# VCN and Networking
module "network" {
  source = "./modules/network"
  
  compartment_id = oci_identity_compartment.aquapredict.id
  vcn_cidr       = var.vcn_cidr
  region         = var.region
}

# Autonomous Database
module "adb" {
  source = "./modules/adb"
  
  compartment_id        = oci_identity_compartment.aquapredict.id
  subnet_id             = module.network.private_subnet_id
  db_name               = var.db_name
  admin_password        = var.db_admin_password
  cpu_core_count        = var.adb_cpu_core_count
  data_storage_size_in_tbs = var.adb_storage_tb
}

# OKE Cluster
module "oke" {
  source = "./modules/oke"
  
  compartment_id     = oci_identity_compartment.aquapredict.id
  vcn_id             = module.network.vcn_id
  subnet_id          = module.network.private_subnet_id
  lb_subnet_id       = module.network.public_subnet_id
  cluster_name       = var.oke_cluster_name
  kubernetes_version = var.kubernetes_version
  node_pool_size     = var.oke_node_pool_size
  node_shape         = var.oke_node_shape
}

# Object Storage
module "object_storage" {
  source = "./modules/object_storage"
  
  compartment_id = oci_identity_compartment.aquapredict.id
  namespace      = var.object_storage_namespace
  
  buckets = [
    "aquapredict-data-raw",
    "aquapredict-data-processed",
    "aquapredict-models",
    "aquapredict-reports"
  ]
}

# Container Registry
module "ocir" {
  source = "./modules/ocir"
  
  compartment_id = oci_identity_compartment.aquapredict.id
  
  repositories = [
    "aquapredict/data-ingestion",
    "aquapredict/preprocessing",
    "aquapredict/feature-engineering",
    "aquapredict/modeling",
    "aquapredict/prediction-service",
    "aquapredict/frontend",
    "aquapredict/reporting"
  ]
}

# Data Science
module "data_science" {
  source = "./modules/data_science"
  
  compartment_id = oci_identity_compartment.aquapredict.id
  project_name   = "aquapredict-ml"
  subnet_id      = module.network.private_subnet_id
}

# Outputs
output "adb_connection_string" {
  value     = module.adb.connection_string
  sensitive = true
}

output "oke_cluster_id" {
  value = module.oke.cluster_id
}

output "object_storage_namespace" {
  value = module.object_storage.namespace
}

output "ocir_login_server" {
  value = module.ocir.login_server
}

output "data_science_project_id" {
  value = module.data_science.project_id
}
