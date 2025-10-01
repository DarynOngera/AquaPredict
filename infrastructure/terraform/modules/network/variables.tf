variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "vcn_cidr" {
  description = "VCN CIDR block"
  type        = string
  default     = "10.0.0.0/16"
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
