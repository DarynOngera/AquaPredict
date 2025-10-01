variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "create_notebook" {
  description = "Create notebook session (requires additional quotas)"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Data Science project name"
  type        = string
  default     = "aquapredict-ml"
}

variable "subnet_id" {
  description = "Subnet OCID for Data Science resources"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "object_storage_namespace" {
  description = "Object Storage namespace"
  type        = string
}

# Notebook Session Configuration
variable "notebook_shape" {
  description = "Notebook session shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "notebook_ocpus" {
  description = "Notebook session OCPUs"
  type        = number
  default     = 4
}

variable "notebook_memory_gb" {
  description = "Notebook session memory in GB"
  type        = number
  default     = 64
}

variable "notebook_storage_gb" {
  description = "Notebook session block storage in GB"
  type        = number
  default     = 100
}

# Model Deployment Configuration
variable "deploy_models" {
  description = "Deploy models to endpoints"
  type        = bool
  default     = false
}

variable "deployment_shape" {
  description = "Model deployment instance shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "deployment_ocpus" {
  description = "Model deployment OCPUs per instance"
  type        = number
  default     = 2
}

variable "deployment_memory_gb" {
  description = "Model deployment memory in GB per instance"
  type        = number
  default     = 16
}

variable "deployment_instance_count" {
  description = "Number of instances for model deployment"
  type        = number
  default     = 1
}

variable "deployment_bandwidth_mbps" {
  description = "Bandwidth for model deployment in Mbps"
  type        = number
  default     = 10
}

# Training Job Configuration
variable "training_job_shape" {
  description = "Training job shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "training_job_ocpus" {
  description = "Training job OCPUs"
  type        = number
  default     = 8
}

variable "training_job_memory_gb" {
  description = "Training job memory in GB"
  type        = number
  default     = 128
}

variable "training_job_storage_gb" {
  description = "Training job block storage in GB"
  type        = number
  default     = 200
}

variable "training_job_timeout_minutes" {
  description = "Training job maximum runtime in minutes"
  type        = number
  default     = 480
}

# Logging Configuration
variable "log_group_id" {
  description = "Log Group OCID for model deployment logs"
  type        = string
  default     = null
}

variable "access_log_id" {
  description = "Access Log OCID"
  type        = string
  default     = null
}

variable "predict_log_id" {
  description = "Predict Log OCID"
  type        = string
  default     = null
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
