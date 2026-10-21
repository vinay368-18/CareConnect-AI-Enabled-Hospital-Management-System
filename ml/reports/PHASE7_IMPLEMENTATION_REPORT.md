# CareConnect HMS + Retinal AI: Phase 7 Implementation Report

**Author:** Senior Java Full-Stack Developer & Machine Learning Integration Team  
**Date:** October 18, 2026  
**Status:** Completed, Verified, and Tested  
**Project Root:** `C:\Users\vinay\javacode\HospitalManagementSystem Project`  
**Execution Environment:** Java 21 LTS, Apache Tomcat 10.1 (Servlet 6.0), MySQL 8.4, Python 3.12 (PyTorch 2.14 CPU, FastAPI 0.142)

---

## 1. Executive Summary

Phase 7 successfully integrates the retrained **CareConnect Multi-Task Retinal AI model (Experiment B)** into the existing **CareConnect Hospital Management System (HMS)**. 

The integration preserves all existing working functionality of the Java/JSP application while establishing a secure, loosely coupled, microservice-based architecture between Java and Python. Clinicians can now upload a retinal fundus photograph directly within the patient workflow, initiate real-time AI inference, view multi-task screening predictions with validation-calibrated thresholds, and access persistent screening reports.

Crucially, in strict adherence to medical ethics and the Phase 6 held-out test evaluation findings, all outputs are framed with rigorous clinical boundaries:
1. **No Unsupported CVD Diagnostic Claims**: Cardiovascular disease predictions are explicitly labeled as **"Experimental Research Markers"** (reflecting held-out test ROC-AUC: **0.5202**; 95% CI: `[0.3936, 0.6416]`).
2. **Clear Ocular vs. Systemic Separation**: Diabetic Retinopathy classification is highlighted as an ocular microvascular finding (**76.99%** test accuracy) and is explicitly documented as **not** proving systemic cardiovascular disease accuracy.
3. **Mandatory Physician Correlation**: Every generated report advises comprehensive physician consultation, physical examination, sphygmomanometer blood pressure checks, fasting lipid profiles, and 12-lead electrocardiography (ECG).

---

## 2. Integrated System Architecture

```mermaid
flowchart TD
    subgraph Frontend ["Client Browser (Clinician / Staff)"]
        UI1["Patient List (patients.jsp)"] -->|Click 'Retinal AI Screen'| UI2["Upload Form (new-screening.jsp)"]
        UI2 -->|Submit Multipart Form| Servlet["Jakarta Servlet (CVDServlet)"]
        UI3["Report Viewer (cvd-report.jsp)"]
        UI4["Screenings Directory (cvd-screenings.jsp)"]
    end

    subgraph Backend ["Java 21 Application Layer (Tomcat 10.1)"]
        Servlet --> Auth["Session & Role Guard (ADMIN, DOCTOR, RECEPTIONIST)"]
        Auth --> FileCheck["File Validation (Format, Size <= 25MB, UUID)"]
        FileCheck --> JavaClient["HTTP Client Service (CVDClient.java)"]
        Servlet --> DB_DAO["CVDScreeningDAO.java / PatientDAO.java"]
    end

    subgraph Database ["MySQL 8.4 Database ('hospital')"]
        DB_DAO --> MySQL[("Table: cvd_screenings\nTable: patients\nTable: users")]
    end

    subgraph Microservice ["Python AI Microservice (Port 5000)"]
        JavaClient -->|POST /predict (Multipart)| FastAPIServer["api_server.py (FastAPI)"]
        FastAPIServer --> Predictor["inference.py (RetinalPredictor)"]
        Predictor --> Model["CareConnectMultiTaskNet (best_model.pt)"]
        FastAPIServer --> SegModel["Residual U-Net (vessel_segmentation.py)"]
    end
```

---

## 3. What Was Implemented

### A. Python AI Microservice (`cvd-ai-service/`)
1. **Experiment B Checkpoint Deployment**:
   - Installed verified Experiment B weights (`best_model.pt`, 48.7 MB) into `cvd-ai-service/models/`.
   - Safely preserved original baseline weights as `best_model_baseline_backup.pt`.
2. **Exact Preprocessing & Model Architecture**:
   - Reused training-time validation transforms in [`inference.py`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/cvd-ai-service/inference.py): bilinear resize to $224 \times 224$ (antialias enabled), conversion to PyTorch tensor, and ImageNet standardization.
   - Implemented `CareConnectMultiTaskNet` with state-dict compatibility handling both `head_vd` and `head_cvd` prefixes.
3. **Production FastAPI Service (`api_server.py`)**:
   - `GET /health`: Returns service health, model version (`2.0.0-experiment_b`), architecture, and task inventory.
   - `POST /predict`: Handles multipart file uploads in-memory (`io.BytesIO`); never permanently saves uploaded images on disk.
   - `POST /predict-base64`: Supports base64 JSON payloads.
   - `POST /segment`: Integrates optional Residual U-Net retinal vessel segmentation.
4. **Input Sanitization & Error Handling**:
   - Enforces 25 MB file size limit and minimum image resolution of $64 \times 64$ pixels.
   - Detects and rejects non-image extensions and corrupted bytes with clean HTTP 400 JSON responses (no internal stack traces or paths exposed).
   - Returns HTTP 503 if the model is uninitialized.

### B. Java / JSP Full-Stack Integration
1. **Authentication & Authorization Guard**:
   - Hardened [`CVDServlet.java`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/src/main/java/com/hms/controller/CVDServlet.java) with `checkAuthorized()`: requires active `HttpSession` and verified role (`ADMIN`, `DOCTOR`, or `RECEPTIONIST`). Unauthenticated requests are immediately redirected to `/login.jsp?error=unauthorized`.
2. **Patient Isolation & Linking**:
   - Validates that `patientId` corresponds to a real, existing patient record in `PatientDAO` before any file processing occurs.
   - Associates the logged-in doctor's ID automatically when a doctor performs the screening.
3. **HTTP Client Communication (`CVDClient.java`)**:
   - Connects to Python REST endpoints over HTTP/1.1 with connection and read timeouts.
   - Parses structured multi-task predictions, continuous probabilities, frozen thresholds, and clinical advice.
4. **Database Persistence**:
   - Persists all screening results, probabilities, and notes to the `cvd_screenings` table via parameterized queries in `CVDScreeningDAO.java`.
5. **Clinical Presentation Overhaul**:
   - [`cvd-report.jsp`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/src/main/webapp/cvd-report.jsp): Replaced misleading diagnostic risk categories with an assistive **"Research Assessment"** banner, individual finding cards showing both continuous probabilities and validation decision thresholds ($49.96\%$ for CVD, $42.88\%$ for HT), and a mandatory clinical disclaimer.
   - [`cvd-screenings.jsp`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/src/main/webapp/cvd-screenings.jsp): Updated table headers and metric cards to reflect research screening markers rather than definitive diagnostic claims.
   - [`new-screening.jsp`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/src/main/webapp/new-screening.jsp): Added specific alerts for invalid file types, corrupted images, invalid patients, and AI service unavailability.
   - [`patients.jsp`](file:///c:/Users/vinay/javacode/HospitalManagementSystem%20Project/src/main/webapp/patients.jsp): Added direct `🔬 Retinal AI Screen` action button on every patient row.

---

## 4. API Request & Response Specification

### `GET /health`
* **URL**: `http://127.0.0.1:5000/health`
* **Response**:
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

### `POST /predict`
* **URL**: `http://127.0.0.1:5000/predict`
* **Header**: `Content-Type: multipart/form-data`
* **Body Form Field**: `file: [binary image]`
* **Sample Live Response**:
```json
{
  "status": "success",
  "model_version": "2.0.0-experiment_b",
  "cvd_prediction": "Positive",
  "cvd_probability": 0.5907,
  "cvd_threshold": 0.4996,
  "hypertension_prediction": "Positive",
  "hypertension_probability": 0.4999,
  "hypertension_threshold": 0.4288,
  "dr_grade": "No DR",
  "dr_confidence": 0.6535,
  "dr_probabilities": {
    "No DR": 0.6535,
    "Mild": 0.1842,
    "Moderate": 0.1012,
    "Severe": 0.0411,
    "Proliferative": 0.0200
  },
  "risk_level": "Experimental Screening - Requires Clinical Review",
  "recommendation": "Experimental AI research output. Complete comprehensive cardiovascular risk assessment (blood pressure, fasting lipid panel, 12-lead ECG) by an attending physician is mandatory.",
  "reliability_badge": "Low reliability: image-only discriminative performance on systemic vascular disease is near chance (Test ROC-AUC: 0.5202). Not a diagnostic test.",
  "clinical_caveats": "Retinal image-only models exhibit weak discrimination for systemic vascular disease (Test ROC-AUC: 0.5202; 95% CI: 0.3936–0.6416). Diabetic Retinopathy accuracy (76.99%) reflects direct ocular pathology and does NOT indicate cardiovascular disease accuracy.",
  "experimental_flag": true
}
```

---

## 5. Verification & Test Execution Results

### A. Python AI Microservice Test Suite (`cvd-ai-service/test_ai_service.py`)
Executed on Python 3.12 (`cvd-env`):

| Test ID | Test Case | Target / Conditions | Outcome |
| :--- | :--- | :--- | :---: |
| `test_01` | Health Endpoint Verification | `GET /health` returns status healthy & model metadata | **PASS** |
| `test_02` | Valid Fundus Image Inference | `POST /predict` with sample image; verifies probability ranges & caveats | **PASS** |
| `test_03` | Base64 Image Inference | `POST /predict-base64` with valid base64 payload | **PASS** |
| `test_04` | Invalid File Extension Rejection | Non-image extension (`.pdf`) rejected with HTTP 400 | **PASS** |
| `test_05` | Corrupted Image Rejection | Random corrupted bytes rejected with HTTP 400 | **PASS** |
| `test_06` | Undersized Image Rejection | Image $< 64 \times 64$ pixels rejected with HTTP 400 | **PASS** |
| `test_07` | Missing Model Degradation | Uninitialized model returns HTTP 503 | **PASS** |
| `test_08` | Clinical Disclaimer Integrity | Asserts output contains physician consultation requirement and no diagnostic claims | **PASS** |

**Summary: 8 of 8 tests passed in 2.137 seconds.**

---

### B. Java HMS System Integration Tests (`HMSSystemIntegrationTest.java`)
Executed on JDK 21:

| Test ID | Test Description | Subsystem Verified | Outcome |
| :--- | :--- | :--- | :---: |
| `Test 01` | Database Connectivity | MySQL `hospital` active connection via `DBConnection.java` | **PASS** |
| `Test 02` | PatientDAO Retrieval | Querying all patients and fetching patient by ID | **PASS** |
| `Test 03` | UserDAO Authentication | Valid credentials authenticated; invalid rejected | **PASS** |
| `Test 04` | CVDScreeningDAO Operations | Screening counts and record listing queries | **PASS** |
| `Test 05` | CVDClient JSON Parsing Engine | Robust regex extraction of probabilities, grades, and clinical notes | **PASS** |
| `Test 06` | CVDScreening Model Invariants | Integer percentage conversions and getter/setter invariants | **PASS** |
| `Test 07` | Role Authorization Definitions | Role validation rules for `ADMIN`, `DOCTOR`, `RECEPTIONIST` | **PASS** |

**Summary: 7 of 7 tests passed with zero failures.**

---

### C. Live End-to-End Service Integration Test (`EndToEndServiceTest.java`)
Executed with live Python FastAPI service active on port 5000:
1. Java `CVDClient` queried `http://127.0.0.1:5000/health`: **ONLINE & HEALTHY**.
2. Sent 1.28 MB sample retinal image (`img00330.jpg`) via multipart HTTP POST.
3. Python service preprocessed tensor, executed forward pass, and returned full prediction JSON in **323 ms**.
4. Java `CVDClient` parsed results: CVD probability 59.07%, HT probability 49.99%, DR grade "No DR" (65.35% confidence).
5. Persisted screening to MySQL database (generated Screening ID #11).
6. Retrieved and validated Screening ID #11 from database.
7. Safely cleaned up test record #11 from database.

**Summary: Live End-to-End integration test completed successfully.**

---

## 6. Inventory of Changed & Created Files

| File Path | Status | Purpose / Modifications |
| :--- | :--- | :--- |
| `cvd-ai-service/api_server.py` | **Updated** | FastAPI endpoints, 25MB validation, error handling, responsible clinical assessment. |
| `cvd-ai-service/inference.py` | **Updated** | `CareConnectMultiTaskNet` architecture, validation transforms, frozen thresholds. |
| `cvd-ai-service/config.json` | **Updated** | Experiment B configuration, frozen thresholds (CVD 0.4996, HT 0.4288), safety disclaimers. |
| `cvd-ai-service/test_ai_service.py` | **Created** | Automated unit and integration test suite for the Python REST API. |
| `cvd-ai-service/README.md` | **Updated** | Complete service documentation, endpoint schemas, and Windows launch instructions. |
| `cvd-ai-service/models/best_model.pt` | **Updated** | Active verified Experiment B checkpoint (48.7 MB). |
| `cvd-ai-service/models/best_model_baseline_backup.pt` | **Created** | Preserved backup of original baseline checkpoint. |
| `src/main/java/com/hms/controller/CVDServlet.java` | **Updated** | Session authentication, role authorization, patient validation, file type checks. |
| `src/main/java/com/hms/test/HMSSystemIntegrationTest.java` | **Created** | Standalone Java regression and integration test runner. |
| `src/main/java/com/hms/test/EndToEndServiceTest.java` | **Created** | Live end-to-end integration test validating Java-to-Python communication and DB persistence. |
| `src/main/webapp/cvd-report.jsp` | **Updated** | Non-diagnostic clinical presentation, continuous scores, validation thresholds, caveats. |
| `src/main/webapp/cvd-screenings.jsp` | **Updated** | Updated metric cards, research pre-screening banner, sanitized table headers. |
| `src/main/webapp/new-screening.jsp` | **Updated** | Added error alerts for file type, corruption, and patient validation; size checks. |
| `src/main/webapp/patients.jsp` | **Updated** | Direct action button linking patient to Retinal AI screening workflow. |
| `ml/reports/PHASE7_INTEGRATION_PLAN.md` | **Created** | Full architectural integration plan and API specification. |
| `ml/reports/PHASE7_IMPLEMENTATION_REPORT.md` | **Created** | Comprehensive implementation, test execution, and deployment report. |

---

## 7. Exact Windows Run & Execution Commands

### Step 1: Ensure MySQL Database is Running
In PowerShell:
```powershell
Get-Service MySQL84
# If not running:
Start-Service MySQL84
```

### Step 2: Start the Python AI Microservice (Port 5000)
In a dedicated PowerShell window:
```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
& "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\api_server.py"
```

Verify the service is online by opening:  
`http://127.0.0.1:5000/health`

### Step 3: Compile and Deploy the Java Web Application
To compile all Java classes:
```powershell
cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
$cp = "C:/Users/vinay/javacode/libs/jakarta.servlet-api-6.0.0.jar;src/main/webapp/WEB-INF/lib/mysql-connector-j-26.7.0.jar"
$srcs = (Get-ChildItem -Path "src/main/java" -Filter "*.java" -Recurse).FullName
javac -cp $cp -d "src/main/webapp/WEB-INF/classes" $srcs
```

### Step 4: Start Apache Tomcat
To run the HMS on Tomcat 10.1:
```powershell
& "C:\Users\vinay\apache-tomcat-10.1.57-windows-x64\bin\startup.bat"
```
Access the Hospital Management System in your browser at:  
`http://localhost:8080/HospitalManagementSystem_Project/` (or configured Tomcat context path).

### Step 5: Run Automated Verification Tests
```powershell
# Run Python AI service tests (8 tests)
& "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\test_ai_service.py"

# Run Java integration tests (7 tests)
$cp = "C:/Users/vinay/javacode/libs/jakarta.servlet-api-6.0.0.jar;src/main/webapp/WEB-INF/lib/mysql-connector-j-26.7.0.jar;src/main/webapp/WEB-INF/classes"
java -cp $cp com.hms.test.HMSSystemIntegrationTest

# Run Live End-to-End communication test
java -cp $cp com.hms.test.EndToEndServiceTest
```

---

## 8. Remaining Limitations & Recommended Next Steps

1. **Cardiovascular Disease Image-Only Ceiling**:
   - As established in Phase 6, single 2D fundus photos from handheld non-mydriatic cameras (mBRSET) have limited physical information to resolve systemic coronary or vascular events without clinical history (ROC-AUC 0.5202).
   - *Recommendation*: For future research phases, evaluate multimodal models that ingest electronic health record (EHR) features (Age, Sex, systolic/diastolic blood pressure, lipid profile, smoking history) alongside retinal vessel caliber metrics.
2. **BRSET Dataset Recovery**:
   - Only Shard 6 (187 images) of BRSET is present locally; remaining shards (001–005) are currently unavailable. When acquired, they can expand the training cohort to over 16,000 images.
3. **Rollback Instructions**:
   - If needed, the system can be restored to the baseline model by setting `weights_file: "models/best_model_baseline_backup.pt"` in `cvd-ai-service/config.json`.
   - The Java HMS codebase has zero hard dependencies on the Python service; if the Python service is offline, the web application continues to operate normally with graceful `isAiOnline = false` degradation.
