variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "create_model_par" {
  description = "Create pre-authenticated request for model downloads"
  type        = bool
  default     = false
}

variable "model_par_object_name" {
  description = "Object name for model PAR"
  type        = string
  default     = "latest/aquifer_model.pkl"
}
