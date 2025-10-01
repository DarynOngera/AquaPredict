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
  environment    = var.environment
}

# Autonomous Database
module "database" {
  source = "./modules/database"
  
  compartment_id           = oci_identity_compartment.aquapredict.id
  subnet_id                = module.network.private_subnet_id
  create_database          = var.adb_create_database
  db_name                  = var.db_name
  admin_password           = var.db_admin_password
  wallet_password          = var.db_wallet_password
  app_user                 = var.db_app_user
  app_password             = var.db_app_password
  cpu_core_count           = var.adb_cpu_core_count
  data_storage_size_in_tbs = var.adb_storage_tb
  is_free_tier             = var.adb_is_free_tier
  enable_auto_scaling      = var.adb_enable_auto_scaling
  environment              = var.environment
}

# OKE Cluster
module "oke" {
  source = "./modules/oke"
  
  compartment_id      = oci_identity_compartment.aquapredict.id
  vcn_id              = module.network.vcn_id
  subnet_id           = module.network.private_subnet_id
  lb_subnet_id        = module.network.public_subnet_id
  availability_domain = var.availability_domain
  cluster_name        = var.oke_cluster_name
  kubernetes_version  = var.kubernetes_version
  node_pool_size      = var.oke_node_pool_size
  node_shape          = var.oke_node_shape
  environment         = var.environment
}

# Object Storage
module "object_storage" {
  source = "./modules/object_storage"
  
  compartment_id = oci_identity_compartment.aquapredict.id
  region         = var.region
  environment    = var.environment
}

# Compute Instances
module "compute" {
  source = "./modules/compute"
  
  compartment_id           = oci_identity_compartment.aquapredict.id
  availability_domain      = var.availability_domain
  subnet_id                = module.network.private_subnet_id
  lb_subnet_id             = module.network.public_subnet_id
  instance_shape           = var.compute_instance_shape
  instance_ocpus           = var.compute_instance_ocpus
  instance_memory_gb       = var.compute_instance_memory_gb
  ssh_public_key           = var.ssh_public_key
  assign_public_ip         = var.compute_assign_public_ip
  create_load_balancer     = var.compute_create_load_balancer
  db_connection_string     = module.database.app_connection_string
  object_storage_namespace = module.object_storage.namespace
  gee_service_account      = var.gee_service_account_json
  environment              = var.environment
}

# Data Science
module "data_science" {
  source = "./modules/data_science"
  
  compartment_id           = oci_identity_compartment.aquapredict.id
  project_name             = "aquapredict-ml"
  subnet_id                = module.network.private_subnet_id
  region                   = var.region
  object_storage_namespace = module.object_storage.namespace
  deploy_models            = var.ds_deploy_models
  environment              = var.environment
}

# Outputs
output "database_connection_string" {
  value     = module.database.connection_string
  sensitive = true
}

output "database_app_connection" {
  value     = module.database.app_connection_string
  sensitive = true
}

output "database_wallet_path" {
  value = module.database.wallet_path
}

output "oke_cluster_id" {
  value = module.oke.cluster_id
}

output "object_storage_namespace" {
  value = module.object_storage.namespace
}

output "object_storage_buckets" {
  value = {
    raw_data   = module.object_storage.raw_data_bucket
    processed  = module.object_storage.processed_data_bucket
    models     = module.object_storage.models_bucket
    reports    = module.object_storage.reports_bucket
    backups    = module.object_storage.backups_bucket
  }
}

output "compute_backend_api_ip" {
  value = module.compute.backend_api_public_ip
}

output "compute_load_balancer_ip" {
  value = module.compute.load_balancer_ip
}

output "data_science_project_id" {
  value = module.data_science.project_id
}

output "data_science_notebook_url" {
  value = module.data_science.notebook_session_url
}
