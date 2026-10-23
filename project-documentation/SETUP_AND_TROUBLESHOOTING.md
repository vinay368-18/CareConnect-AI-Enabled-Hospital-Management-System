# CareConnect HMS & Retinal AI: Setup, Execution & Troubleshooting Guide

**Document ID:** `SETUP_AND_TROUBLESHOOTING.md`  
**System:** CareConnect Hospital Management System & Retinal Screening AI  
**Verified Platform:** Windows 10/11 x64  
**Date:** October 2026  

---

## 1. Environment & Prerequisites

Before starting the CareConnect system, ensure the following verified software components are installed and accessible on your workstation:

| Component | Verified Local Path / Version | Verification Command |
| :--- | :--- | :--- |
| **Java Development Kit** | `C:\Program Files\Common Files\Oracle\Java\javapath\` (Java 21 LTS) | `java -version` |
| **Python Virtual Env** | `C:\Users\vinay\cvd-env` (Python 3.12 x64) | `& "C:\Users\vinay\cvd-env\Scripts\python.exe" --version` |
| **Apache Tomcat** | `C:\Users\vinay\apache-tomcat-10.1.57-windows-x64\apache-tomcat-10.1.57` | `catalina.bat version` |
| **MySQL Server** | MySQL 8.0 or 8.4 (Default Port 3306) | `mysql --version` |
| **Web Browser** | Microsoft Edge / Google Chrome / Mozilla Firefox | Browser standard |

---

## 2. Environment Variables & Safe Configuration

CareConnect uses externalized environment variables to avoid storing hardcoded database passwords and secret API keys in version-controlled source files.

### 2.1 Configuration Options
You can configure these variables either in your current PowerShell session, system-wide, or in Tomcat's `bin/setenv.bat`.

```powershell
# ==============================================================================
# CareConnect Environment Variables (PowerShell Session Example)
# Replace placeholder values with your actual local configuration
# ==============================================================================

# Database Connection (MySQL)
$env:HMS_DB_URL = "jdbc:mysql://localhost:3306/hospital?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC"
$env:HMS_DB_USER = "root"
$env:HMS_DB_PASSWORD = "YOUR_DATABASE_PASSWORD_HERE"

# Python AI Microservice Security
$env:HMS_AI_API_URL = "http://127.0.0.1:5000"
$env:HMS_AI_API_KEY = "careconnect_secret_token_2026_xyz"
$env:HMS_CORS_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"
```

> [!IMPORTANT]
> Never commit actual passwords or keys to Git. A template is provided at `.env.example`.

---

## 3. Database Initialization (MySQL)

If you are setting up the database on a new computer or resetting it, execute the following SQL script in your MySQL client (e.g., MySQL Workbench or MySQL CLI):

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS hospital CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hospital;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    doctor_id INT NULL
);

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    phone VARCHAR(20),
    address TEXT
);

-- 3. Doctors Table
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    experience INT,
    consultation_fee DOUBLE
);

-- 4. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

-- 5. Bills Table
CREATE TABLE IF NOT EXISTS bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    appointment_id INT NULL,
    amount DOUBLE NOT NULL,
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'Pending',
    bill_date DATE NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- 6. CVD Retinal Screenings Table (Includes vessel segmentation columns)
CREATE TABLE IF NOT EXISTS cvd_screenings (
    screening_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NULL,
    appointment_id INT NULL,
    image_path VARCHAR(255) NOT NULL,
    cvd_prediction VARCHAR(20) NOT NULL,
    cvd_probability DOUBLE NOT NULL,
    hypertension_prediction VARCHAR(20) NOT NULL,
    hypertension_probability DOUBLE NOT NULL,
    dr_grade VARCHAR(50) NOT NULL,
    dr_confidence DOUBLE NOT NULL,
    risk_level VARCHAR(100) NOT NULL,
    notes TEXT,
    screening_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vessel_overlay_path VARCHAR(255) NULL,
    vessel_density DOUBLE NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);
```

### 3.1 Initial Admin Account Provisioning
After database creation, run the Java `AdminProvisioner` tool to create your first administrative user with a PBKDF2 hashed password:

```powershell
# Run from project root
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"

# Provision initial admin: username 'admin', password 'AdminPass123!'
& "C:\Program Files\Common Files\Oracle\Java\javapath\java.exe" `
    -cp "build\classes;src\main\webapp\WEB-INF\lib\*" `
    com.hms.util.AdminProvisioner admin AdminPass123!
```

---

## 4. Starting the Python AI Microservice

The AI Microservice provides multi-task deep learning inference on port 5000.

### Option A: Using the Launcher Script
Double-click `start_cvd_ai_service.bat` in the project root, or execute:

```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
.\start_cvd_ai_service.bat
```

### Option B: Direct Python Execution
```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"

# Set the pre-shared secret key
$env:HMS_AI_API_KEY = "careconnect_secret_token_2026_xyz"

# Launch FastAPI on port 5000
& "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\api_server.py"
```

Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:cvd-api:[CVD API] Initializing CareConnect Retinal AI microservice...
INFO:cvd-inference:CareConnectMultiTaskNet model loaded successfully on CPU.
INFO:cvd-api:[CVD API] PyTorch model loaded successfully on CPU.
INFO:cvd-api:[CVD API] Residual U-Net vessel segmentation model loaded.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5000 (Press CTRL+C to quit)
```

### Verifying Microservice Health
In a separate terminal or browser:
```powershell
curl http://127.0.0.1:5000/health
```
Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "2.0.0-experiment_b",
  "architecture": "CareConnectMultiTaskNet (EfficientNet-B0)",
  "device": "cpu",
  "vessel_model_loaded": true,
  "tasks": ["vascular_disease", "systemic_hypertension", "dr_grade"]
}
```

---

## 5. Starting Apache Tomcat & Deploying the Webapp

### Option A: Deployed Webapp Directory (Already Present)
The web application is already deployed inside Tomcat's `webapps` directory at:  
`C:\Users\vinay\apache-tomcat-10.1.57-windows-x64\apache-tomcat-10.1.57\webapps\HospitalManagementSystem`

To start Tomcat:
```powershell
cd "C:\Users\vinay\apache-tomcat-10.1.57-windows-x64\apache-tomcat-10.1.57\bin"
.\startup.bat
```

### Option B: Running from Eclipse IDE
1. Open Eclipse IDE with Jakarta EE / WTP support.
2. Import `HospitalManagementSystem Project`.
3. Add the project to configured Apache Tomcat 10.1 runtime.
4. Click **Run on Server**.

### Accessing the Web Application
Open your web browser and navigate to:
```
http://localhost:8080/HospitalManagementSystem/
```
Or if deployed as the root context:
```
http://localhost:8080/
```

Log in using the administrator credentials created with `AdminProvisioner`.

---

## 6. Running Automated Verification Suites

The codebase contains four independent test suites that can be executed to verify system functionality:

### 6.1 Priority 0 Java Security Test Suite (17 Tests)
Validates PBKDF2 hashing, legacy migration, CSRF generation, XSS escaping, admin provisioning rules, and route gating without requiring external servers.

```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
& "C:\Program Files\Common Files\Oracle\Java\javapath\java.exe" `
    -cp "build\classes;src\main\webapp\WEB-INF\lib\*" `
    com.hms.test.SecurityRemediationTest
```
*Expected Result:* `TOTAL TESTS: 17 | PASSED: 17 | FAILED: 0`

---

### 6.2 Python AI Microservice Unit & Security Suite (13 Tests)
Validates FastAPI endpoints, API key authentication, rate limiting, image corruption handling, resolution bounds, and multi-task model inference.

```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
& "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\test_ai_service.py"
```
*Expected Result:* `Ran 13 tests in ~9s | OK`

---

### 6.3 Machine Learning Data Pipeline Test Suite (9 Tests)
Validates dataset integrity, zero patient leakage across partitions, target purity (`vascular_disease` separation from AMI), and PyTorch forward/backward gradient flow.

```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
& "C:\Users\vinay\cvd-env\Scripts\python.exe" "ml\tests\test_data_pipeline.py"
```
*Expected Result:* `Ran 9 tests in ~5s | OK`

---

### 6.4 Java HMS System Integration Test Suite (7 Tests)
Validates database connectivity, DAO queries, JSON response parsing, and authorization roles.

```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
$env:HMS_DB_USER = "root"
$env:HMS_DB_PASSWORD = "YOUR_DATABASE_PASSWORD"
& "C:\Program Files\Common Files\Oracle\Java\javapath\java.exe" `
    -cp "build\classes;src\main\webapp\WEB-INF\lib\*" `
    com.hms.test.HMSSystemIntegrationTest
```
*Expected Result:* `Tests Run: 7 | Passed: 7 | Failed: 0`

---

## 7. Troubleshooting & Common Issues

### 7.1 Port 5000 or 8080 Already in Use
- **Symptom:** `Uvicorn failed to bind to 127.0.0.1:5000` or Tomcat reports `Address already in use: bind`.
- **Diagnosis:** Another process is occupying the required TCP port.
- **Solution:**
  ```powershell
  # Find process using port 5000 or 8080
  Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object OwningProcess

  # Terminate process by PID if appropriate
  Stop-Process -Id <PID> -Force
  ```

---

### 7.2 Database Connection Error (`[DBConnection] Database credentials not configured`)
- **Symptom:** Servlets throw `NullPointerException` on `prepareStatement()` or test suite reports missing credentials.
- **Diagnosis:** The environment variables `HMS_DB_USER` and `HMS_DB_PASSWORD` are not defined in the process executing the Java code.
- **Solution:**
  Set the variables in PowerShell before executing:
  ```powershell
  $env:HMS_DB_USER = "root"
  $env:HMS_DB_PASSWORD = "your_actual_password"
  ```
  Or add them to Tomcat's `bin/setenv.bat`:
  ```bat
  set HMS_DB_USER=root
  set HMS_DB_PASSWORD=your_actual_password
  ```

---

### 7.3 Python Microservice Authentication Error (`HTTP 401 Unauthorized`)
- **Symptom:** `CVDServlet` reports: `AI Microservice authentication failed (HTTP 401). Verify HMS_AI_API_KEY configuration.`
- **Diagnosis:** The Python service was started with a different `HMS_AI_API_KEY` than the Java client, or one side is unset.
- **Solution:** Ensure both environments share the identical key value, or restart both with matching configuration.

---

### 7.4 Model Weight Checkpoint Not Found (`FileNotFoundError: best_model.pt`)
- **Symptom:** Python service crashes on startup: `Model weight file not found at: ...\models\best_model.pt`.
- **Diagnosis:** Working directory is misaligned or checkpoint was moved.
- **Solution:**
  Ensure you launch Python from the project root:
  ```powershell
  cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
  & "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\api_server.py"
  ```
  Check that `cvd-ai-service/models/best_model.pt` exists (48.7 MB).

---

### 7.5 Missing Vessel Segmentation Columns in MySQL
- **Symptom:** Server console prints: `[CVD] Could not save vessel result (run db/add_vessel_columns.sql?)`.
- **Diagnosis:** The MySQL `cvd_screenings` table was created using an older schema without `vessel_overlay_path` and `vessel_density`.
- **Solution:**
  Run the migration script:
  ```powershell
  mysql -u root -p hospital < "db\add_vessel_columns.sql"
  ```

---

*End of Setup and Troubleshooting Guide.*
