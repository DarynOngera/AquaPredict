variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "create_database" {
  description = "Create Autonomous Database (requires feature to be enabled)"
  type        = bool
  default     = true
}

variable "db_name" {
  description = "Database name (alphanumeric, max 14 chars)"
  type        = string
  default     = "aquapredict"
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9]{0,13}$", var.db_name))
    error_message = "Database name must be alphanumeric, start with a letter, and be max 14 characters."
  }
}

variable "admin_password" {
  description = "Admin password for ADB (12-30 chars, must include uppercase, lowercase, number, and special char)"
  type        = string
  sensitive   = true
}

variable "wallet_password" {
  description = "Password for database wallet"
  type        = string
  sensitive   = true
}

variable "app_user" {
  description = "Application database user"
  type        = string
  default     = "aquapredict_app"
}

variable "app_password" {
  description = "Application user password"
  type        = string
  sensitive   = true
}

variable "cpu_core_count" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
  
  validation {
    condition     = var.cpu_core_count >= 1 && var.cpu_core_count <= 128
    error_message = "CPU core count must be between 1 and 128."
  }
}

variable "data_storage_size_in_tbs" {
  description = "Data storage size in terabytes"
  type        = number
  default     = 1
  
  validation {
    condition     = var.data_storage_size_in_tbs >= 1 && var.data_storage_size_in_tbs <= 128
    error_message = "Storage size must be between 1 and 128 TB."
  }
}

variable "is_free_tier" {
  description = "Use free tier (Always Free)"
  type        = bool
  default     = false
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for CPU"
  type        = bool
  default     = true
}

variable "license_model" {
  description = "License model: LICENSE_INCLUDED or BRING_YOUR_OWN_LICENSE"
  type        = string
  default     = "LICENSE_INCLUDED"
  
  validation {
    condition     = contains(["LICENSE_INCLUDED", "BRING_YOUR_OWN_LICENSE"], var.license_model)
    error_message = "License model must be LICENSE_INCLUDED or BRING_YOUR_OWN_LICENSE."
  }
}

variable "subnet_id" {
  description = "Subnet OCID for private endpoint"
  type        = string
  default     = null
}

variable "nsg_ids" {
  description = "Network Security Group OCIDs"
  type        = list(string)
  default     = []
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
