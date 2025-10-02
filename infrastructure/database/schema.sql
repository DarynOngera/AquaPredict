-- AquaPredict Database Schema
-- Oracle Autonomous Database

-- Raw weather data from APIs
CREATE TABLE raw_weather_data (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    longitude NUMBER(10, 6) NOT NULL,
    latitude NUMBER(10, 6) NOT NULL,
    date_recorded DATE NOT NULL,
    temperature NUMBER(5, 2),
    precipitation NUMBER(8, 2),
    pressure NUMBER(8, 2),
    humidity NUMBER(5, 2),
    wind_speed NUMBER(6, 2),
    wind_direction NUMBER(5, 2),
    data_source VARCHAR2(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_weather_location_date UNIQUE (longitude, latitude, date_recorded)
);

-- Engineered features for ML
CREATE TABLE ml_features (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    longitude NUMBER(10, 6) NOT NULL,
    latitude NUMBER(10, 6) NOT NULL,
    date_recorded DATE NOT NULL,
    month NUMBER(2),
    dayofyear NUMBER(3),
    sin_day NUMBER(10, 8),
    cos_day NUMBER(10, 8),
    lag1_precip NUMBER(8, 2),
    lag2_precip NUMBER(8, 2),
    roll3_precip NUMBER(8, 2),
    roll7_precip NUMBER(8, 2),
    air_temp_2m NUMBER(5, 2),
    dewpoint_2m NUMBER(5, 2),
    mslp NUMBER(8, 2),
    surface_pressure NUMBER(8, 2),
    u10 NUMBER(6, 2),
    v10 NUMBER(6, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_features_location_date UNIQUE (longitude, latitude, date_recorded)
);

-- Model predictions
CREATE TABLE predictions (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    longitude NUMBER(10, 6) NOT NULL,
    latitude NUMBER(10, 6) NOT NULL,
    prediction_date DATE NOT NULL,
    model_name VARCHAR2(50) NOT NULL,
    predicted_value NUMBER(10, 4),
    confidence_score NUMBER(5, 4),
    data_source VARCHAR2(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Application logs
CREATE TABLE app_logs (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    log_level VARCHAR2(20),
    service_name VARCHAR2(100),
    message CLOB,
    error_details CLOB,
    user_id VARCHAR2(100),
    request_id VARCHAR2(100),
    ip_address VARCHAR2(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model metadata
CREATE TABLE model_metadata (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_name VARCHAR2(100) NOT NULL,
    model_version VARCHAR2(50),
    model_type VARCHAR2(50),
    training_date DATE,
    accuracy_score NUMBER(5, 4),
    mae NUMBER(10, 4),
    rmse NUMBER(10, 4),
    r2_score NUMBER(5, 4),
    feature_count NUMBER(3),
    training_samples NUMBER(10),
    model_path VARCHAR2(500),
    is_active NUMBER(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_model_name_version UNIQUE (model_name, model_version)
);

-- Create indexes for performance
CREATE INDEX idx_weather_location ON raw_weather_data(longitude, latitude);
CREATE INDEX idx_weather_date ON raw_weather_data(date_recorded);
CREATE INDEX idx_features_location ON ml_features(longitude, latitude);
CREATE INDEX idx_features_date ON ml_features(date_recorded);
CREATE INDEX idx_predictions_date ON predictions(prediction_date);
CREATE INDEX idx_predictions_model ON predictions(model_name);
CREATE INDEX idx_logs_level ON app_logs(log_level);
CREATE INDEX idx_logs_date ON app_logs(created_at);
CREATE INDEX idx_model_active ON model_metadata(is_active);

-- Create views for common queries
CREATE OR REPLACE VIEW v_latest_predictions AS
SELECT p.*, m.model_version, m.accuracy_score
FROM predictions p
JOIN model_metadata m ON p.model_name = m.model_name
WHERE m.is_active = 1
AND p.created_at >= SYSDATE - 7;

CREATE OR REPLACE VIEW v_model_performance AS
SELECT 
    model_name,
    model_version,
    accuracy_score,
    mae,
    rmse,
    r2_score,
    training_date,
    is_active
FROM model_metadata
ORDER BY training_date DESC;

COMMIT;
