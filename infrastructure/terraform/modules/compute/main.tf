# Compute Instance Module for AquaPredict
# Deploys backend API and processing services

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Get latest Oracle Linux image
data "oci_core_images" "oracle_linux" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# Backend API Instance
resource "oci_core_instance" "backend_api" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "aquapredict-backend-api"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    display_name     = "backend-api-vnic"
    assign_public_ip = var.assign_public_ip
    hostname_label   = "backend-api"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init-backend.yaml", {
      db_connection_string = var.db_connection_string
      object_storage_namespace = var.object_storage_namespace
      gee_service_account = var.gee_service_account
    }))
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Backend-API"
  }
}

# Data Processing Instance
resource "oci_core_instance" "data_processor" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "aquapredict-data-processor"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  create_vnic_details {
    subnet_id        = var.subnet_id
    display_name     = "data-processor-vnic"
    assign_public_ip = false
    hostname_label   = "data-processor"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/cloud-init-processor.yaml", {
      db_connection_string = var.db_connection_string
      object_storage_namespace = var.object_storage_namespace
      gee_service_account = var.gee_service_account
    }))
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Data-Processor"
  }
}

# Block Volume for Model Storage
resource "oci_core_volume" "model_storage" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "aquapredict-model-storage"
  size_in_gbs         = var.model_storage_size_gb

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Model-Storage"
  }
}

# Attach Block Volume to Backend API
resource "oci_core_volume_attachment" "model_storage_attachment" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.backend_api.id
  volume_id       = oci_core_volume.model_storage.id
  display_name    = "model-storage-attachment"
}

# Load Balancer for Backend API
resource "oci_load_balancer_load_balancer" "api_lb" {
  count          = var.create_load_balancer ? 1 : 0
  shape          = "flexible"
  compartment_id = var.compartment_id
  subnet_ids     = [var.lb_subnet_id]
  display_name   = "aquapredict-api-lb"

  shape_details {
    minimum_bandwidth_in_mbps = 10
    maximum_bandwidth_in_mbps = 100
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Load-Balancer"
  }
}

# Backend Set
resource "oci_load_balancer_backend_set" "api_backend_set" {
  count            = var.create_load_balancer ? 1 : 0
  name             = "api-backend-set"
  load_balancer_id = oci_load_balancer_load_balancer.api_lb[0].id
  policy           = "ROUND_ROBIN"

  health_checker {
    port                = 8000
    protocol            = "HTTP"
    url_path            = "/health"
    interval_ms         = 10000
    timeout_in_millis   = 3000
    retries             = 3
    return_code         = 200
  }
}

# Backend
resource "oci_load_balancer_backend" "api_backend" {
  count            = var.create_load_balancer ? 1 : 0
  load_balancer_id = oci_load_balancer_load_balancer.api_lb[0].id
  backendset_name  = oci_load_balancer_backend_set.api_backend_set[0].name
  ip_address       = oci_core_instance.backend_api.private_ip
  port             = 8000
  backup           = false
  drain            = false
  offline          = false
  weight           = 1
}

# Listener
resource "oci_load_balancer_listener" "api_listener" {
  count                    = var.create_load_balancer ? 1 : 0
  load_balancer_id         = oci_load_balancer_load_balancer.api_lb[0].id
  name                     = "api-listener"
  default_backend_set_name = oci_load_balancer_backend_set.api_backend_set[0].name
  port                     = 80
  protocol                 = "HTTP"
}

# Outputs
output "backend_api_id" {
  value = oci_core_instance.backend_api.id
}

output "backend_api_private_ip" {
  value = oci_core_instance.backend_api.private_ip
}

output "backend_api_public_ip" {
  value = var.assign_public_ip ? oci_core_instance.backend_api.public_ip : null
}

output "data_processor_id" {
  value = oci_core_instance.data_processor.id
}

output "data_processor_private_ip" {
  value = oci_core_instance.data_processor.private_ip
}

output "load_balancer_ip" {
  value = var.create_load_balancer ? oci_load_balancer_load_balancer.api_lb[0].ip_address_details[0].ip_address : null
}

output "model_storage_volume_id" {
  value = oci_core_volume.model_storage.id
}
