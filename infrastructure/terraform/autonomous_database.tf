# Oracle Autonomous Database for AquaPredict
# Stores training data, features, predictions, and logs

resource "oci_database_autonomous_database" "aquapredict_atp" {
  compartment_id           = var.compartment_id
  db_name                  = "AquaPredictDB"
  display_name             = "AquaPredict ATP"
  
  # Database configuration
  db_version               = "19c"
  db_workload              = "OLTP"  # Transaction processing
  is_auto_scaling_enabled  = true
  is_free_tier             = false
  
  # Storage and compute
  cpu_core_count           = 1
  data_storage_size_in_tbs = 1
  
  # Admin credentials
  admin_password           = var.atp_admin_password
  
  # Network
  is_mtls_connection_required = false  # Allow non-mTLS for easier connection
  
  # Backup
  is_auto_backup_enabled   = true
  
  # License
  license_model            = "LICENSE_INCLUDED"
  
  # Tags
  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = "Production"
    "ManagedBy"   = "Terraform"
  }
}

# Create database user for application
resource "null_resource" "create_app_user" {
  depends_on = [oci_database_autonomous_database.aquapredict_atp]
  
  provisioner "local-exec" {
    command = <<-EOT
      # This will be run after ATP is created
      # You'll need to manually create the app user via SQL
      echo "ATP Created. Create app user with:"
      echo "CREATE USER aquapredict_app IDENTIFIED BY <password>;"
      echo "GRANT CONNECT, RESOURCE TO aquapredict_app;"
      echo "GRANT UNLIMITED TABLESPACE TO aquapredict_app;"
    EOT
  }
}

# Output connection details
output "atp_connection_string" {
  value = oci_database_autonomous_database.aquapredict_atp.connection_strings[0].profiles[0].value
  sensitive = true
}

output "atp_ocid" {
  value = oci_database_autonomous_database.aquapredict_atp.id
}

output "atp_wallet_download_url" {
  value = "https://cloud.oracle.com/db/adb/${oci_database_autonomous_database.aquapredict_atp.id}?region=${var.region}"
}
