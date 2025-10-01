#!/bin/bash
# AquaPredict Database Setup Script
# Sets up Oracle Autonomous Database with spatial schema

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
WALLET_DIR="../../credentials/wallet"
SQL_DIR="../sql"
DB_USER="${DB_USER:-aquapredict_app}"

# Check if wallet exists
check_wallet() {
    log_info "Checking for database wallet..."
    
    if [ ! -d "$WALLET_DIR" ]; then
        log_error "Wallet directory not found at $WALLET_DIR"
        log_info "Please download the wallet first using:"
        log_info "  terraform output -raw database_wallet_path"
        exit 1
    fi
    
    log_info "Wallet found!"
}

# Create SQL scripts directory
setup_sql_dir() {
    log_info "Setting up SQL scripts directory..."
    mkdir -p "$SQL_DIR"
}

# Create schema SQL script
create_schema_script() {
    log_info "Creating schema setup script..."
    
    cat > "$SQL_DIR/01_create_schema.sql" <<'EOF'
-- AquaPredict Database Schema Setup
-- Oracle Autonomous Database with Spatial Extensions

SET ECHO ON
SET SERVEROUTPUT ON

-- Create locations table with spatial geometry
CREATE TABLE locations (
    location_id VARCHAR2(50) PRIMARY KEY,
    latitude NUMBER(10, 6) NOT NULL,
    longitude NUMBER(10, 6) NOT NULL,
    geometry SDO_GEOMETRY,
    country VARCHAR2(100),
    region VARCHAR2(100),
    elevation NUMBER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_latitude CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (longitude BETWEEN -180 AND 180)
);

-- Insert spatial metadata for locations table
INSERT INTO user_sdo_geom_metadata VALUES (
    'LOCATIONS',
    'GEOMETRY',
    SDO_DIM_ARRAY(
        SDO_DIM_ELEMENT('X', -180, 180, 0.005),
        SDO_DIM_ELEMENT('Y', -90, 90, 0.005)
    ),
    4326  -- WGS84 coordinate system
);

-- Create spatial index
CREATE INDEX locations_spatial_idx ON locations(geometry)
    INDEXTYPE IS MDSYS.SPATIAL_INDEX
    PARAMETERS ('layer_gtype=POINT');

-- Create regular indexes
CREATE INDEX locations_country_idx ON locations(country);
CREATE INDEX locations_region_idx ON locations(region);

-- Features table
CREATE TABLE features (
    feature_id VARCHAR2(50) PRIMARY KEY,
    location_id VARCHAR2(50) NOT NULL,
    elevation NUMBER,
    slope NUMBER,
    twi NUMBER,
    precip_mean NUMBER,
    precip_std NUMBER,
    temp_mean NUMBER,
    temp_std NUMBER,
    ndvi NUMBER,
    landcover NUMBER,
    soil_type VARCHAR2(50),
    geology VARCHAR2(100),
    data_source VARCHAR2(50) DEFAULT 'GEE',
    quality_score NUMBER(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_features_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX features_location_idx ON features(location_id);
CREATE INDEX features_source_idx ON features(data_source);

-- Predictions table
CREATE TABLE predictions (
    prediction_id VARCHAR2(50) PRIMARY KEY,
    location_id VARCHAR2(50) NOT NULL,
    prediction VARCHAR2(20) NOT NULL,
    probability NUMBER(5, 4) NOT NULL,
    confidence_interval_lower NUMBER(5, 4),
    confidence_interval_upper NUMBER(5, 4),
    depth_bands CLOB,
    geological_formation VARCHAR2(100),
    estimated_porosity VARCHAR2(50),
    recommended_drilling_depth VARCHAR2(50),
    model_version VARCHAR2(20),
    model_type VARCHAR2(50) DEFAULT 'XGBoost',
    data_source VARCHAR2(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_predictions_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE,
    CONSTRAINT chk_prediction CHECK (prediction IN ('present', 'absent')),
    CONSTRAINT chk_probability CHECK (probability BETWEEN 0 AND 1)
);

CREATE INDEX predictions_location_idx ON predictions(location_id);
CREATE INDEX predictions_created_idx ON predictions(created_at DESC);
CREATE INDEX predictions_prediction_idx ON predictions(prediction);

-- Forecasts table
CREATE TABLE forecasts (
    forecast_id VARCHAR2(50) PRIMARY KEY,
    location_id VARCHAR2(50) NOT NULL,
    forecast_date DATE NOT NULL,
    recharge_rate NUMBER,
    precipitation NUMBER,
    temperature NUMBER,
    evapotranspiration NUMBER,
    confidence NUMBER(5, 4),
    model_version VARCHAR2(20),
    model_type VARCHAR2(50) DEFAULT 'LSTM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_forecasts_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX forecasts_location_idx ON forecasts(location_id);
CREATE INDEX forecasts_date_idx ON forecasts(forecast_date);
CREATE INDEX forecasts_created_idx ON forecasts(created_at DESC);

-- Time series data table
CREATE TABLE timeseries_data (
    timeseries_id VARCHAR2(50) PRIMARY KEY,
    location_id VARCHAR2(50) NOT NULL,
    data_type VARCHAR2(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    value NUMBER,
    unit VARCHAR2(20),
    source VARCHAR2(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_timeseries_location FOREIGN KEY (location_id) 
        REFERENCES locations(location_id) ON DELETE CASCADE
);

CREATE INDEX timeseries_location_idx ON timeseries_data(location_id);
CREATE INDEX timeseries_type_idx ON timeseries_data(data_type);
CREATE INDEX timeseries_timestamp_idx ON timeseries_data(timestamp DESC);

-- Audit logs table
CREATE TABLE audit_logs (
    log_id VARCHAR2(50) PRIMARY KEY,
    user_id VARCHAR2(100),
    action VARCHAR2(50) NOT NULL,
    resource_type VARCHAR2(50),
    resource_id VARCHAR2(50),
    details CLOB,
    ip_address VARCHAR2(50),
    user_agent VARCHAR2(500),
    status VARCHAR2(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX audit_logs_created_idx ON audit_logs(created_at DESC);
CREATE INDEX audit_logs_user_idx ON audit_logs(user_id);
CREATE INDEX audit_logs_action_idx ON audit_logs(action);

-- User settings table
CREATE TABLE user_settings (
    user_id VARCHAR2(100) PRIMARY KEY,
    settings CLOB CHECK (settings IS JSON),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model metadata table
CREATE TABLE model_metadata (
    model_id VARCHAR2(50) PRIMARY KEY,
    model_name VARCHAR2(100) NOT NULL,
    model_type VARCHAR2(50) NOT NULL,
    version VARCHAR2(20) NOT NULL,
    algorithm VARCHAR2(50),
    framework VARCHAR2(50),
    metrics CLOB CHECK (metrics IS JSON),
    hyperparameters CLOB CHECK (hyperparameters IS JSON),
    training_date TIMESTAMP,
    storage_path VARCHAR2(500),
    status VARCHAR2(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_model_status CHECK (status IN ('active', 'deprecated', 'testing'))
);

CREATE INDEX model_metadata_type_idx ON model_metadata(model_type);
CREATE INDEX model_metadata_status_idx ON model_metadata(status);

COMMIT;

-- Display table counts
SELECT 'Schema created successfully!' AS status FROM dual;
SELECT table_name FROM user_tables ORDER BY table_name;

EOF

    log_info "Schema script created!"
}

# Create spatial functions script
create_spatial_functions() {
    log_info "Creating spatial functions..."
    
    cat > "$SQL_DIR/02_spatial_functions.sql" <<'EOF'
-- Spatial utility functions for AquaPredict

-- Function to find locations within radius (km)
CREATE OR REPLACE FUNCTION find_locations_within_radius(
    p_lat NUMBER,
    p_lon NUMBER,
    p_radius_km NUMBER
) RETURN SYS_REFCURSOR IS
    v_cursor SYS_REFCURSOR;
    v_point SDO_GEOMETRY;
BEGIN
    -- Create point geometry
    v_point := SDO_GEOMETRY(
        2001,
        4326,
        SDO_POINT_TYPE(p_lon, p_lat, NULL),
        NULL,
        NULL
    );
    
    -- Find locations within radius
    OPEN v_cursor FOR
        SELECT 
            location_id,
            latitude,
            longitude,
            country,
            region,
            SDO_GEOM.SDO_DISTANCE(geometry, v_point, 0.005, 'unit=KM') AS distance_km
        FROM locations
        WHERE SDO_WITHIN_DISTANCE(
            geometry,
            v_point,
            'distance=' || p_radius_km || ' unit=KM'
        ) = 'TRUE'
        ORDER BY distance_km;
    
    RETURN v_cursor;
END;
/

-- Function to find nearest N locations
CREATE OR REPLACE FUNCTION find_nearest_locations(
    p_lat NUMBER,
    p_lon NUMBER,
    p_count NUMBER DEFAULT 10
) RETURN SYS_REFCURSOR IS
    v_cursor SYS_REFCURSOR;
    v_point SDO_GEOMETRY;
BEGIN
    v_point := SDO_GEOMETRY(
        2001,
        4326,
        SDO_POINT_TYPE(p_lon, p_lat, NULL),
        NULL,
        NULL
    );
    
    OPEN v_cursor FOR
        SELECT 
            location_id,
            latitude,
            longitude,
            country,
            region,
            SDO_GEOM.SDO_DISTANCE(geometry, v_point, 0.005, 'unit=KM') AS distance_km
        FROM locations
        ORDER BY distance_km
        FETCH FIRST p_count ROWS ONLY;
    
    RETURN v_cursor;
END;
/

-- Procedure to insert location with geometry
CREATE OR REPLACE PROCEDURE insert_location(
    p_location_id VARCHAR2,
    p_latitude NUMBER,
    p_longitude NUMBER,
    p_country VARCHAR2 DEFAULT NULL,
    p_region VARCHAR2 DEFAULT NULL
) IS
BEGIN
    INSERT INTO locations (
        location_id,
        latitude,
        longitude,
        geometry,
        country,
        region
    ) VALUES (
        p_location_id,
        p_latitude,
        p_longitude,
        SDO_GEOMETRY(
            2001,
            4326,
            SDO_POINT_TYPE(p_longitude, p_latitude, NULL),
            NULL,
            NULL
        ),
        p_country,
        p_region
    );
    
    COMMIT;
END;
/

-- Function to get prediction statistics by region
CREATE OR REPLACE FUNCTION get_region_stats(
    p_region VARCHAR2
) RETURN SYS_REFCURSOR IS
    v_cursor SYS_REFCURSOR;
BEGIN
    OPEN v_cursor FOR
        SELECT 
            l.region,
            COUNT(DISTINCT l.location_id) AS total_locations,
            COUNT(p.prediction_id) AS total_predictions,
            SUM(CASE WHEN p.prediction = 'present' THEN 1 ELSE 0 END) AS aquifer_present_count,
            ROUND(AVG(CASE WHEN p.prediction = 'present' THEN p.probability END), 4) AS avg_probability,
            MAX(p.created_at) AS last_prediction_date
        FROM locations l
        LEFT JOIN predictions p ON l.location_id = p.location_id
        WHERE l.region = p_region
        GROUP BY l.region;
    
    RETURN v_cursor;
END;
/

COMMIT;

SELECT 'Spatial functions created successfully!' AS status FROM dual;

EOF

    log_info "Spatial functions script created!"
}

# Create sample data script
create_sample_data() {
    log_info "Creating sample data script..."
    
    cat > "$SQL_DIR/03_sample_data.sql" <<'EOF'
-- Sample data for testing AquaPredict

-- Insert sample locations in Kenya
BEGIN
    -- Nairobi
    insert_location('LOC001', -1.2921, 36.8219, 'Kenya', 'Nairobi');
    
    -- Mombasa
    insert_location('LOC002', -4.0435, 39.6682, 'Kenya', 'Mombasa');
    
    -- Kisumu
    insert_location('LOC003', -0.0917, 34.7680, 'Kenya', 'Kisumu');
    
    -- Nakuru
    insert_location('LOC004', -0.3031, 36.0800, 'Kenya', 'Nakuru');
    
    -- Eldoret
    insert_location('LOC005', 0.5143, 35.2698, 'Kenya', 'Eldoret');
END;
/

-- Insert sample features
INSERT INTO features (feature_id, location_id, elevation, slope, twi, precip_mean, temp_mean, ndvi, landcover, data_source)
VALUES ('FEAT001', 'LOC001', 1795, 5.2, 8.5, 900, 19.5, 0.45, 50, 'GEE');

INSERT INTO features (feature_id, location_id, elevation, slope, twi, precip_mean, temp_mean, ndvi, landcover, data_source)
VALUES ('FEAT002', 'LOC002', 16, 2.1, 6.2, 1100, 26.3, 0.62, 40, 'GEE');

COMMIT;

SELECT 'Sample data inserted successfully!' AS status FROM dual;
SELECT COUNT(*) AS location_count FROM locations;
SELECT COUNT(*) AS feature_count FROM features;

EOF

    log_info "Sample data script created!"
}

# Execute SQL scripts
execute_sql_scripts() {
    log_info "Executing SQL scripts..."
    
    read -p "Enter database connection string (e.g., user/pass@service_high): " DB_CONN
    
    if [ -z "$DB_CONN" ]; then
        log_error "Database connection string is required"
        exit 1
    fi
    
    # Set wallet location
    export TNS_ADMIN="$WALLET_DIR"
    
    # Execute schema creation
    log_info "Creating schema..."
    sqlplus -S "$DB_CONN" @"$SQL_DIR/01_create_schema.sql"
    
    # Execute spatial functions
    log_info "Creating spatial functions..."
    sqlplus -S "$DB_CONN" @"$SQL_DIR/02_spatial_functions.sql"
    
    # Ask if user wants sample data
    read -p "Do you want to insert sample data? (yes/no): " insert_sample
    if [ "$insert_sample" = "yes" ]; then
        log_info "Inserting sample data..."
        sqlplus -S "$DB_CONN" @"$SQL_DIR/03_sample_data.sql"
    fi
    
    log_info "Database setup completed successfully!"
}

# Verify setup
verify_setup() {
    log_info "Verifying database setup..."
    
    cat > "$SQL_DIR/verify.sql" <<'EOF'
SELECT 'Tables:' AS info FROM dual;
SELECT table_name FROM user_tables ORDER BY table_name;

SELECT 'Indexes:' AS info FROM dual;
SELECT index_name, table_name FROM user_indexes WHERE table_name IN (
    'LOCATIONS', 'FEATURES', 'PREDICTIONS', 'FORECASTS'
) ORDER BY table_name, index_name;

SELECT 'Spatial Metadata:' AS info FROM dual;
SELECT table_name, column_name, srid FROM user_sdo_geom_metadata;

SELECT 'Functions/Procedures:' AS info FROM dual;
SELECT object_name, object_type FROM user_objects 
WHERE object_type IN ('FUNCTION', 'PROCEDURE')
ORDER BY object_type, object_name;
EOF

    sqlplus -S "$DB_CONN" @"$SQL_DIR/verify.sql"
}

# Main function
main() {
    log_info "Starting AquaPredict Database Setup..."
    echo ""
    
    check_wallet
    setup_sql_dir
    create_schema_script
    create_spatial_functions
    create_sample_data
    execute_sql_scripts
    verify_setup
    
    log_info "Database setup completed successfully!"
    log_info "SQL scripts saved in: $SQL_DIR"
}

main "$@"
