# Bastion Service for SSH access to private instances

resource "oci_bastion_bastion" "aquapredict_bastion" {
  bastion_type                 = "STANDARD"
  compartment_id               = var.compartment_id
  target_subnet_id             = var.target_subnet_id
  client_cidr_block_allow_list = ["0.0.0.0/0"]  # Restrict this to your IP in production
  name                         = "aquapredict-bastion"
  max_session_ttl_in_seconds   = 10800  # 3 hours

  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
  }
}

output "bastion_id" {
  value = oci_bastion_bastion.aquapredict_bastion.id
}

output "bastion_name" {
  value = oci_bastion_bastion.aquapredict_bastion.name
}
