variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "target_subnet_id" {
  description = "Target subnet ID for bastion"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
