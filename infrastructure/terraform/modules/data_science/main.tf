# OCI Data Science Module for AquaPredict
# Provides ML model training and deployment infrastructure

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Data Science Project
resource "oci_datascience_project" "aquapredict_ml" {
  compartment_id = var.compartment_id
  display_name   = var.project_name
  description    = "AquaPredict ML model training and deployment"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Data-Science"
  }
}

# Notebook Session for Model Development (optional - requires quotas)
resource "oci_datascience_notebook_session" "ml_notebook" {
  count          = var.create_notebook ? 1 : 0
  compartment_id = var.compartment_id
  project_id     = oci_datascience_project.aquapredict_ml.id
  display_name   = "aquapredict-ml-notebook"

  notebook_session_configuration_details {
    shape     = var.notebook_shape
    subnet_id = var.subnet_id

    block_storage_size_in_gbs = var.notebook_storage_gb

    notebook_session_shape_config_details {
      ocpus         = var.notebook_ocpus
      memory_in_gbs = var.notebook_memory_gb
    }
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "ML-Notebook"
  }
}

# Note: Model catalog resources will be created after training models
# Models will be registered via Python SDK or OCI CLI after training
# Model deployments will be created manually after models are trained

# Job for Batch Model Training
resource "oci_datascience_job" "model_training_job" {
  compartment_id = var.compartment_id
  project_id     = oci_datascience_project.aquapredict_ml.id
  display_name   = "aquapredict-model-training"
  description    = "Scheduled job for model retraining"

  job_configuration_details {
    job_type = "DEFAULT"
    
    command_line_arguments = "--config /opt/ml/config/training_config.yaml"
    environment_variables = {
      "PYTHONPATH"              = "/opt/ml"
      "OCI_REGION"              = var.region
      "OBJECT_STORAGE_NAMESPACE" = var.object_storage_namespace
      "MODEL_BUCKET"            = "aquapredict-models"
    }
    
    maximum_runtime_in_minutes = var.training_job_timeout_minutes
  }

  job_infrastructure_configuration_details {
    job_infrastructure_type = "STANDALONE"
    shape_name              = var.training_job_shape
    subnet_id               = var.subnet_id
    block_storage_size_in_gbs = var.training_job_storage_gb

    job_shape_config_details {
      ocpus         = var.training_job_ocpus
      memory_in_gbs = var.training_job_memory_gb
    }
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Model-Training"
  }
}

# Outputs
output "project_id" {
  value = oci_datascience_project.aquapredict_ml.id
}

output "notebook_session_id" {
  value = var.create_notebook ? oci_datascience_notebook_session.ml_notebook[0].id : null
}

output "notebook_session_url" {
  value = var.create_notebook ? oci_datascience_notebook_session.ml_notebook[0].notebook_session_url : "Notebook not created - set create_notebook=true"
}

output "training_job_id" {
  value = oci_datascience_job.model_training_job.id
}
