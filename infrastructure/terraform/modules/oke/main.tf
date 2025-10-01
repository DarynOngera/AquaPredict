# OKE (Oracle Kubernetes Engine) Module for AquaPredict
# Creates Kubernetes cluster and node pool

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# OKE Cluster
resource "oci_containerengine_cluster" "aquapredict_cluster" {
  compartment_id     = var.compartment_id
  kubernetes_version = var.kubernetes_version
  name               = var.cluster_name
  vcn_id             = var.vcn_id

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = var.lb_subnet_id
  }

  options {
    service_lb_subnet_ids = [var.lb_subnet_id]

    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }

    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Node Pool
resource "oci_containerengine_node_pool" "aquapredict_node_pool" {
  cluster_id         = oci_containerengine_cluster.aquapredict_cluster.id
  compartment_id     = var.compartment_id
  kubernetes_version = var.kubernetes_version
  name               = "${var.cluster_name}-node-pool"
  node_shape         = var.node_shape

  node_shape_config {
    memory_in_gbs = var.node_memory_gb
    ocpus         = var.node_ocpus
  }

  node_config_details {
    placement_configs {
      availability_domain = var.availability_domain
      subnet_id           = var.subnet_id
    }

    size = var.node_pool_size

    node_pool_pod_network_option_details {
      cni_type = "FLANNEL_OVERLAY"
    }
  }

  # Don't specify node_source_details - OCI will automatically use the correct image
  # for the specified kubernetes_version

  initial_node_labels {
    key   = "name"
    value = var.cluster_name
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Get available node images for the cluster
data "oci_containerengine_node_pool_option" "aquapredict_node_pool_option" {
  node_pool_option_id = oci_containerengine_cluster.aquapredict_cluster.id
  compartment_id      = var.compartment_id
}

# Don't specify image_id - let OCI automatically select the correct image for the Kubernetes version
# This ensures compatibility between cluster version and node image

# Outputs
output "cluster_id" {
  value = oci_containerengine_cluster.aquapredict_cluster.id
}

output "cluster_kubernetes_version" {
  value = oci_containerengine_cluster.aquapredict_cluster.kubernetes_version
}

output "cluster_endpoint" {
  value = oci_containerengine_cluster.aquapredict_cluster.endpoints[0].public_endpoint
}

output "node_pool_id" {
  value = oci_containerengine_node_pool.aquapredict_node_pool.id
}

output "node_pool_kubernetes_version" {
  value = oci_containerengine_node_pool.aquapredict_node_pool.kubernetes_version
}
