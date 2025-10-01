# Object Storage Module for AquaPredict
# Provides buckets for data, models, and reports

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Get Object Storage namespace
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_id
}

# Raw Data Bucket
resource "oci_objectstorage_bucket" "raw_data" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "aquapredict-data-raw"
  access_type    = "NoPublicAccess"
  
  storage_tier   = "Standard"
  versioning     = "Enabled"
  
  auto_tiering   = "InfrequentAccess"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "DataType"    = "Raw"
  }
}

# Processed Data Bucket
resource "oci_objectstorage_bucket" "processed_data" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "aquapredict-data-processed"
  access_type    = "NoPublicAccess"
  
  storage_tier   = "Standard"
  versioning     = "Enabled"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "DataType"    = "Processed"
  }
}

# Models Bucket
resource "oci_objectstorage_bucket" "models" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "aquapredict-models"
  access_type    = "NoPublicAccess"
  
  storage_tier   = "Standard"
  versioning     = "Enabled"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "DataType"    = "Models"
  }
}

# Reports Bucket
resource "oci_objectstorage_bucket" "reports" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "aquapredict-reports"
  access_type    = "NoPublicAccess"
  
  storage_tier   = "Standard"
  versioning     = "Disabled"
  
  auto_tiering   = "InfrequentAccess"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "DataType"    = "Reports"
  }
}

# Backups Bucket
resource "oci_objectstorage_bucket" "backups" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "aquapredict-backups"
  access_type    = "NoPublicAccess"
  
  storage_tier   = "Archive"
  versioning     = "Enabled"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "DataType"    = "Backups"
  }
}

# Note: Lifecycle policies can be added manually via OCI Console
# They require additional IAM permissions that may not be available initially

# Pre-authenticated Request for Model Downloads (optional)
resource "oci_objectstorage_preauthrequest" "model_download" {
  count      = var.create_model_par ? 1 : 0
  namespace  = data.oci_objectstorage_namespace.ns.namespace
  bucket     = oci_objectstorage_bucket.models.name
  name       = "model-download-par"
  access_type = "ObjectRead"
  time_expires = timeadd(timestamp(), "720h") # 30 days
  
  object_name = var.model_par_object_name
}

# Outputs
output "namespace" {
  value = data.oci_objectstorage_namespace.ns.namespace
}

output "raw_data_bucket" {
  value = oci_objectstorage_bucket.raw_data.name
}

output "processed_data_bucket" {
  value = oci_objectstorage_bucket.processed_data.name
}

output "models_bucket" {
  value = oci_objectstorage_bucket.models.name
}

output "reports_bucket" {
  value = oci_objectstorage_bucket.reports.name
}

output "backups_bucket" {
  value = oci_objectstorage_bucket.backups.name
}

output "bucket_urls" {
  value = {
    raw_data   = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.ns.namespace}/b/${oci_objectstorage_bucket.raw_data.name}/o/"
    processed  = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.ns.namespace}/b/${oci_objectstorage_bucket.processed_data.name}/o/"
    models     = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.ns.namespace}/b/${oci_objectstorage_bucket.models.name}/o/"
    reports    = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.ns.namespace}/b/${oci_objectstorage_bucket.reports.name}/o/"
    backups    = "https://objectstorage.${var.region}.oraclecloud.com/n/${data.oci_objectstorage_namespace.ns.namespace}/b/${oci_objectstorage_bucket.backups.name}/o/"
  }
}

output "model_par_url" {
  value = var.create_model_par ? oci_objectstorage_preauthrequest.model_download[0].access_uri : null
  sensitive = true
}
