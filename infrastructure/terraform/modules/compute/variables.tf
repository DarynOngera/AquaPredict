variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "availability_domain" {
  description = "Availability Domain"
  type        = string
}

variable "subnet_id" {
  description = "Subnet OCID for compute instances"
  type        = string
}

variable "lb_subnet_id" {
  description = "Subnet OCID for load balancer"
  type        = string
}

variable "instance_shape" {
  description = "Compute instance shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs"
  type        = number
  default     = 2
}

variable "instance_memory_gb" {
  description = "Memory in GB"
  type        = number
  default     = 16
}

variable "boot_volume_size_gb" {
  description = "Boot volume size in GB"
  type        = number
  default     = 100
}

variable "model_storage_size_gb" {
  description = "Model storage volume size in GB"
  type        = number
  default     = 200
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "assign_public_ip" {
  description = "Assign public IP to backend API instance"
  type        = bool
  default     = true
}

variable "create_load_balancer" {
  description = "Create load balancer for API"
  type        = bool
  default     = true
}

variable "db_connection_string" {
  description = "Database connection string"
  type        = string
  sensitive   = true
}

variable "object_storage_namespace" {
  description = "Object Storage namespace"
  type        = string
}

variable "gee_service_account" {
  description = "Google Earth Engine service account JSON"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
