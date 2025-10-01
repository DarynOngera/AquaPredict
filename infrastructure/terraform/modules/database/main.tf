# Oracle Autonomous Database Module for AquaPredict
# Provides spatial database for geospatial data storage

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
}

# Autonomous Database (optional - requires feature to be enabled)
resource "oci_database_autonomous_database" "aquapredict_adb" {
  count                    = var.create_database ? 1 : 0
  compartment_id           = var.compartment_id
  db_name                  = var.db_name
  display_name             = "AquaPredict Spatial Database"
  db_workload              = "DW"  # Data Warehouse workload
  is_free_tier             = var.is_free_tier
  cpu_core_count           = var.cpu_core_count
  data_storage_size_in_tbs = var.data_storage_size_in_tbs
  admin_password           = var.admin_password
  
  # Enable auto-scaling
  is_auto_scaling_enabled = var.enable_auto_scaling
  
  # Network configuration
  subnet_id                = var.subnet_id
  nsg_ids                  = var.nsg_ids
  
  # License model
  license_model = var.license_model
  
  # Backup configuration
  is_mtls_connection_required = false
  
  freeform_tags = {
    "Project"     = "AquaPredict"
    "Environment" = var.environment
    "Component"   = "Database"
  }
}

# Database wallet
resource "oci_database_autonomous_database_wallet" "aquapredict_wallet" {
  count                  = var.create_database ? 1 : 0
  autonomous_database_id = oci_database_autonomous_database.aquapredict_adb[0].id
  password               = var.wallet_password
  base64_encode_content  = true
}

# Save wallet to local file
resource "local_file" "wallet_file" {
  count           = var.create_database ? 1 : 0
  content_base64  = oci_database_autonomous_database_wallet.aquapredict_wallet[0].content
  filename        = "${path.module}/wallet_${var.db_name}.zip"
  file_permission = "0600"
}

# Database user for application
resource "null_resource" "create_app_user" {
  count      = var.create_database ? 1 : 0
  depends_on = [oci_database_autonomous_database.aquapredict_adb]

  provisioner "local-exec" {
    command = <<-EOT
      # Extract wallet
      unzip -o ${local_file.wallet_file[0].filename} -d ${path.module}/wallet_${var.db_name}
      
      # Create SQL script
      cat > ${path.module}/create_user.sql <<EOF
      -- Create application user
      CREATE USER ${var.app_user} IDENTIFIED BY "${var.app_password}";
      
      -- Grant privileges
      GRANT CONNECT, RESOURCE TO ${var.app_user};
      GRANT UNLIMITED TABLESPACE TO ${var.app_user};
      GRANT CREATE SESSION TO ${var.app_user};
      GRANT CREATE TABLE TO ${var.app_user};
      GRANT CREATE VIEW TO ${var.app_user};
      GRANT CREATE SEQUENCE TO ${var.app_user};
      GRANT CREATE PROCEDURE TO ${var.app_user};
      
      -- Grant spatial privileges
      GRANT EXECUTE ON SDO_GEOMETRY TO ${var.app_user};
      GRANT EXECUTE ON SDO_UTIL TO ${var.app_user};
      GRANT EXECUTE ON SDO_GEOM TO ${var.app_user};
      
      -- Create schema objects
      ALTER SESSION SET CURRENT_SCHEMA = ${var.app_user};
      
      -- Locations table with spatial index
      CREATE TABLE locations (
        location_id VARCHAR2(50) PRIMARY KEY,
        latitude NUMBER(10, 6) NOT NULL,
        longitude NUMBER(10, 6) NOT NULL,
        geometry SDO_GEOMETRY,
        country VARCHAR2(100),
        region VARCHAR2(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      -- Insert spatial metadata
      INSERT INTO user_sdo_geom_metadata VALUES (
        'LOCATIONS',
        'GEOMETRY',
        SDO_DIM_ARRAY(
          SDO_DIM_ELEMENT('X', -180, 180, 0.005),
          SDO_DIM_ELEMENT('Y', -90, 90, 0.005)
        ),
        4326
      );
      
      -- Create spatial index
      CREATE INDEX locations_spatial_idx ON locations(geometry)
        INDEXTYPE IS MDSYS.SPATIAL_INDEX;
      
      -- Features table
      CREATE TABLE features (
        feature_id VARCHAR2(50) PRIMARY KEY,
        location_id VARCHAR2(50) REFERENCES locations(location_id),
        elevation NUMBER,
        slope NUMBER,
        twi NUMBER,
        precip_mean NUMBER,
        temp_mean NUMBER,
        ndvi NUMBER,
        landcover NUMBER,
        data_source VARCHAR2(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE INDEX features_location_idx ON features(location_id);
      
      -- Predictions table
      CREATE TABLE predictions (
        prediction_id VARCHAR2(50) PRIMARY KEY,
        location_id VARCHAR2(50) REFERENCES locations(location_id),
        prediction VARCHAR2(20) NOT NULL,
        probability NUMBER(5, 4) NOT NULL,
        confidence_interval_lower NUMBER(5, 4),
        confidence_interval_upper NUMBER(5, 4),
        geological_formation VARCHAR2(100),
        estimated_porosity VARCHAR2(50),
        recommended_drilling_depth VARCHAR2(50),
        model_version VARCHAR2(20),
        data_source VARCHAR2(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE INDEX predictions_location_idx ON predictions(location_id);
      CREATE INDEX predictions_created_idx ON predictions(created_at);
      
      -- Forecasts table
      CREATE TABLE forecasts (
        forecast_id VARCHAR2(50) PRIMARY KEY,
        location_id VARCHAR2(50) REFERENCES locations(location_id),
        forecast_date DATE NOT NULL,
        recharge_rate NUMBER,
        precipitation NUMBER,
        temperature NUMBER,
        confidence NUMBER(5, 4),
        model_version VARCHAR2(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE INDEX forecasts_location_idx ON forecasts(location_id);
      CREATE INDEX forecasts_date_idx ON forecasts(forecast_date);
      
      -- Audit log table
      CREATE TABLE audit_logs (
        log_id VARCHAR2(50) PRIMARY KEY,
        user_id VARCHAR2(100),
        action VARCHAR2(50),
        resource_type VARCHAR2(50),
        resource_id VARCHAR2(50),
        details CLOB,
        ip_address VARCHAR2(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      CREATE INDEX audit_logs_created_idx ON audit_logs(created_at);
      CREATE INDEX audit_logs_user_idx ON audit_logs(user_id);
      
      -- Settings table
      CREATE TABLE user_settings (
        user_id VARCHAR2(100) PRIMARY KEY,
        settings CLOB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      
      COMMIT;
      EOF
      
      # Execute SQL script
      sqlplus admin/${var.admin_password}@${oci_database_autonomous_database.aquapredict_adb[0].connection_strings[0].profiles[0].value} @${path.module}/create_user.sql
    EOT
  }
}

# Outputs
output "adb_id" {
  value = var.create_database ? oci_database_autonomous_database.aquapredict_adb[0].id : "Database not created"
}

output "connection_string" {
  value     = var.create_database ? oci_database_autonomous_database.aquapredict_adb[0].connection_strings[0].profiles[0].value : "Database not created"
  sensitive = true
}

output "connection_urls" {
  value = var.create_database ? {
    high   = oci_database_autonomous_database.aquapredict_adb[0].connection_urls[0].apex_url
    medium = oci_database_autonomous_database.aquapredict_adb[0].connection_urls[0].sql_dev_web_url
    low    = oci_database_autonomous_database.aquapredict_adb[0].connection_urls[0].machine_learning_user_management_url
  } : {}
}

output "wallet_path" {
  value = var.create_database ? local_file.wallet_file[0].filename : "Database not created"
}

output "app_user" {
  value = var.app_user
}

output "app_connection_string" {
  value     = var.create_database ? "${var.app_user}/${var.app_password}@${oci_database_autonomous_database.aquapredict_adb[0].connection_strings[0].profiles[0].value}" : "Database not created"
  sensitive = true
}
