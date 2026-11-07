-- =============================================================================
-- CareConnect Hospital Management System
-- Database Schema: cvd_screenings (CVD & Retinal Multi-Task AI Screenings)
-- =============================================================================

-- Table creation with all required columns, constraints, and indices:
CREATE TABLE IF NOT EXISTS cvd_screenings (
    screening_id             INT AUTO_INCREMENT PRIMARY KEY,
    patient_id               INT NOT NULL,
    doctor_id                INT NULL,
    appointment_id           INT NULL,
    image_path               VARCHAR(500) NOT NULL,
    model_name               VARCHAR(100) DEFAULT 'Residual U-Net' COMMENT 'Segmentation model used: Residual U-Net, U-Net, Attention U-Net',
    vessel_overlay_path      VARCHAR(500) NULL COMMENT 'File path to generated vessel segmentation mask overlay',
    mask_path                VARCHAR(500) NULL COMMENT 'Alias for vessel_overlay_path for API compatibility',
    vessel_density           DOUBLE NULL COMMENT 'Calculated vessel area percentage of total retinal area',
    cvd_prediction           VARCHAR(20) DEFAULT 'Negative' COMMENT 'Positive or Negative',
    cvd_result               VARCHAR(20) DEFAULT 'Negative' COMMENT 'Alias for cvd_prediction',
    cvd_probability          DOUBLE DEFAULT 0.0 COMMENT 'Continuous risk probability 0.0 to 1.0',
    hypertension_prediction  VARCHAR(20) DEFAULT 'Negative' COMMENT 'Positive or Negative',
    ht_result                VARCHAR(20) DEFAULT 'Negative' COMMENT 'Alias for hypertension_prediction',
    hypertension_probability DOUBLE DEFAULT 0.0 COMMENT 'Continuous risk probability 0.0 to 1.0',
    ht_probability           DOUBLE DEFAULT 0.0 COMMENT 'Alias for hypertension_probability',
    dr_grade                 VARCHAR(50) DEFAULT 'No DR' COMMENT 'Diabetic retinopathy grade (No DR, Mild, Moderate, Severe, Proliferative or 0-4)',
    dr_confidence            DOUBLE DEFAULT 0.0 COMMENT 'Classification confidence 0.0 to 1.0',
    risk_level               VARCHAR(60) DEFAULT 'Low Risk' COMMENT 'Clinical risk assessment level: Low Risk, Moderate Risk, High Risk',
    recommendation           TEXT NULL COMMENT 'Clinical referral and management recommendation',
    recommendations          TEXT NULL COMMENT 'Alias for recommendation',
    notes                    TEXT NULL COMMENT 'Attending clinician notes or symptoms',
    screening_date           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_cvd_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_cvd_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL,
    CONSTRAINT fk_cvd_appointment FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    INDEX idx_cvd_patient (patient_id),
    INDEX idx_cvd_doctor (doctor_id),
    INDEX idx_cvd_date (screening_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- Migration Script (Idempotent ALTER statements for existing databases)
-- =============================================================================

-- Add model_name column if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'model_name');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN model_name VARCHAR(100) DEFAULT ''Residual U-Net'' AFTER image_path', 'SELECT ''model_name already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add vessel_overlay_path if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'vessel_overlay_path');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN vessel_overlay_path VARCHAR(500) NULL AFTER model_name', 'SELECT ''vessel_overlay_path already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add mask_path alias if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'mask_path');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN mask_path VARCHAR(500) NULL AFTER vessel_overlay_path', 'SELECT ''mask_path already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add vessel_density if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'vessel_density');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN vessel_density DOUBLE NULL AFTER mask_path', 'SELECT ''vessel_density already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add recommendation if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'recommendation');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN recommendation TEXT NULL AFTER risk_level', 'SELECT ''recommendation already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add recommendations alias if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'recommendations');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN recommendations TEXT NULL AFTER recommendation', 'SELECT ''recommendations already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add created_at alias if not present
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'cvd_screenings' AND COLUMN_NAME = 'created_at');
SET @sql = IF(@col_exists = 0, 'ALTER TABLE cvd_screenings ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER screening_date', 'SELECT ''created_at already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
