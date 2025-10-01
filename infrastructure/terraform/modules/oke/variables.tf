variable "compartment_id" {
  description = "Compartment OCID"
  type        = string
}

variable "vcn_id" {
  description = "VCN OCID"
  type        = string
}

variable "subnet_id" {
  description = "Subnet OCID for node pool"
  type        = string
}

variable "lb_subnet_id" {
  description = "Subnet OCID for load balancers"
  type        = string
}

variable "availability_domain" {
  description = "Availability Domain for nodes"
  type        = string
}

variable "cluster_name" {
  description = "OKE cluster name"
  type        = string
  default     = "aquapredict-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "v1.28.2"
}

variable "node_pool_size" {
  description = "Number of nodes in the pool"
  type        = number
  default     = 3
}

variable "node_shape" {
  description = "Node shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "node_ocpus" {
  description = "OCPUs per node"
  type        = number
  default     = 2
}

variable "node_memory_gb" {
  description = "Memory in GB per node"
  type        = number
  default     = 16
}

variable "node_image_id" {
  description = "Node image OCID (leave empty for latest)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}
