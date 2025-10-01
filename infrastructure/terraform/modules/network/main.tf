# Network Module for AquaPredict
# Creates VCN, subnets, internet gateway, NAT gateway, and security lists

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Virtual Cloud Network (VCN)
resource "oci_core_vcn" "aquapredict_vcn" {
  compartment_id = var.compartment_id
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "aquapredict-vcn"
  dns_label      = "aquapredict"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Internet Gateway
resource "oci_core_internet_gateway" "aquapredict_igw" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-igw"
  enabled        = true

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# NAT Gateway
resource "oci_core_nat_gateway" "aquapredict_nat" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-nat"

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Service Gateway
resource "oci_core_service_gateway" "aquapredict_sg" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-sg"

  services {
    service_id = data.oci_core_services.all_services.services[0].id
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Get all available services
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}

# Route Table for Public Subnet
resource "oci_core_route_table" "public_route_table" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.aquapredict_igw.id
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Route Table for Private Subnet
resource "oci_core_route_table" "private_route_table" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.aquapredict_nat.id
  }

  route_rules {
    destination       = data.oci_core_services.all_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.aquapredict_sg.id
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Security List for Public Subnet
resource "oci_core_security_list" "public_security_list" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-public-sl"

  # Egress Rules
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # Ingress Rules
  # HTTP
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow HTTP"

    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow HTTPS"

    tcp_options {
      min = 443
      max = 443
    }
  }

  # SSH
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Allow SSH"

    tcp_options {
      min = 22
      max = 22
    }
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Security List for Private Subnet
resource "oci_core_security_list" "private_security_list" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.aquapredict_vcn.id
  display_name   = "aquapredict-private-sl"

  # Egress Rules
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol    = "all"
    stateless   = false
  }

  # Ingress Rules
  # Allow all from VCN
  ingress_security_rules {
    protocol    = "all"
    source      = var.vcn_cidr
    stateless   = false
    description = "Allow all from VCN"
  }

  # SSH from public subnet
  ingress_security_rules {
    protocol    = "6" # TCP
    source      = cidrsubnet(var.vcn_cidr, 8, 0)
    stateless   = false
    description = "Allow SSH from public subnet"

    tcp_options {
      min = 22
      max = 22
    }
  }

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Public Subnet
resource "oci_core_subnet" "public_subnet" {
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.aquapredict_vcn.id
  cidr_block        = cidrsubnet(var.vcn_cidr, 8, 0)
  display_name      = "aquapredict-public-subnet"
  dns_label         = "public"
  route_table_id    = oci_core_route_table.public_route_table.id
  security_list_ids = [oci_core_security_list.public_security_list.id]

  prohibit_public_ip_on_vnic = false

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Private Subnet
resource "oci_core_subnet" "private_subnet" {
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.aquapredict_vcn.id
  cidr_block        = cidrsubnet(var.vcn_cidr, 8, 1)
  display_name      = "aquapredict-private-subnet"
  dns_label         = "private"
  route_table_id    = oci_core_route_table.private_route_table.id
  security_list_ids = [oci_core_security_list.private_security_list.id]

  prohibit_public_ip_on_vnic = true

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

# Outputs
output "vcn_id" {
  value = oci_core_vcn.aquapredict_vcn.id
}

output "public_subnet_id" {
  value = oci_core_subnet.public_subnet.id
}

output "private_subnet_id" {
  value = oci_core_subnet.private_subnet.id
}

output "internet_gateway_id" {
  value = oci_core_internet_gateway.aquapredict_igw.id
}

output "nat_gateway_id" {
  value = oci_core_nat_gateway.aquapredict_nat.id
}

output "service_gateway_id" {
  value = oci_core_service_gateway.aquapredict_sg.id
}
