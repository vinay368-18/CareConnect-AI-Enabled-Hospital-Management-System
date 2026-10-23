# CareConnect HMS & Retinal AI: System Architecture Documentation

**Document:** System Architecture Specification  
**System Name:** CareConnect Hospital Management System with Deep Learning Retinal Screening  
**Version:** 2.0.0-integrated  
**Date:** October 2026  
**Security Classification:** Standard Academic & Clinical Research  

---

## 1. High-Level System Overview

The **CareConnect Hospital Management System (HMS)** is a hybrid, multi-tier enterprise healthcare platform that merges traditional hospital clinical administration with deep learning computer vision. 

The architecture is deliberately divided into two loosely coupled subsystems:
1. **The Core Hospital Administration Subsystem (Java/Jakarta EE Web Application)**: Manages patient demographics, doctor directories, appointment scheduling, billing invoices, role-based access control (RBAC), and persistent screening reports.
2. **The Retinal AI Screening Subsystem (Python FastAPI & PyTorch Microservice)**: An isolated inference microservice that receives retinal fundus photographs, executes computer vision transforms, evaluates a multi-task deep neural network (`CareConnectMultiTaskNet` with an `EfficientNet-B0` backbone), runs optional Residual U-Net retinal vessel segmentation, and returns structured probability predictions with clinical disclaimers.

The two subsystems communicate strictly across a localhost loopback boundary via an authenticated HTTP/1.1 REST API, eliminating monolithic coupling and ensuring that machine learning execution cannot destabilize core hospital record-keeping.

---

## 2. Global Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientTier ["Client Tier (Web Browser)"]
        Browser["Desktop / Tablet Web Browser\n(Clinicians, Doctors, Receptionists, Admins)"]
    end

    subgraph PresentationTier ["Presentation & Web Tier (Apache Tomcat 10.1 / Servlet 6.0)"]
        direction TB
        JSP["JSP Views (JavaServer Pages)\n• login.jsp, dashboard.jsp\n• patients.jsp, add-patient.jsp\n• doctors.jsp, appointments.jsp\n• billing.jsp, reports.jsp\n• new-screening.jsp, cvd-screenings.jsp\n• cvd-report.jsp (Printable Clinical Report)"]
        Static["Static Assets\n• /css/style.css\n• /uploads/fundus/samples/"]
    end

    subgraph SecurityTier ["Security & Gateway Layer"]
        AuthFilter["AuthenticationFilter (/*)\n• Whitelist-based Public Gate\n• Session Fixation Prevention\n• Role Verification (ADMIN, DOCTOR, RECEPTIONIST)"]
        CSRF["CSRFUtil\n• Session-bound Cryptographic Tokens"]
        HtmlEscape["HtmlUtil\n• Context-aware XSS Sanitization"]
    end

    subgraph ControllerTier ["Application Controller Tier (Jakarta Servlets)"]
        LoginS["LoginServlet (/LoginServlet)"]
        LogoutS["LogoutServlet (/LogoutServlet)"]
        RegS["RegisterServlet (/RegisterServlet - Admin Only)"]
        PatS["PatientServlet (/PatientServlet)"]
        DocS["DoctorServlet (/DoctorServlet)"]
        ApptS["AppointmentServlet (/AppointmentServlet)"]
        BillS["BillingServlet (/BillingServlet)"]
        RepS["ReportServlet (/ReportServlet)"]
        CVDS["CVDServlet (/CVDServlet - Multipart Form Handler)"]
    end

    subgraph ServiceTier ["Integration & Service Layer"]
        CVDClient["CVDClient.java (java.net.http.HttpClient)\n• Connection & Read Timeouts (10s / 45s / 120s)\n• X-API-Key Header Injection\n• Multipart Form Encoder\n• Native Regex JSON Response Parser"]
    end

    subgraph DataAccessTier ["Data Access Tier (JDBC DAO Layer)"]
        DBConn["DBConnection.java\n• Env & System Property Resolution\n• Safe Fallback (jdbc:mysql://localhost:3306/hospital)\n• Credentials Concealment"]
        UserDAO["UserDAO.java (PBKDF2 Hashing)"]
        PatDAO["PatientDAO.java (Atomic Cascade Deletions)"]
        DocDAO["DoctorDAO.java"]
        ApptDAO["AppointmentDAO.java"]
        BillDAO["BillingDAO.java"]
        RepDAO["ReportDAO.java"]
        CVDDAO["CVDScreeningDAO.java"]
    end

    subgraph DatabaseTier ["Persistence Tier (MySQL 8.4)"]
        MySQL[("MySQL Relational Database ('hospital')\n• users\n• patients\n• doctors\n• appointments\n• bills\n• cvd_screenings")]
    end

    subgraph AIMicroserviceTier ["AI Inference Microservice (Python 3.12 / FastAPI :5000)"]
        FastAPI["FastAPI REST API (api_server.py)\n• Loopback Binding (127.0.0.1:5000)\n• Constant-time API Key Auth (HMS_AI_API_KEY)\n• In-Memory Per-IP Rate Limiting (60 req/min)\n• Image Stream Validation & Pillow Decoding"]
        
        Predictor["RetinalPredictor (inference.py)\n• Deterministic Bilinear Resize (224x224, antialias)\n• ImageNet Standardization ([0.485, 0.456, 0.406])\n• CareConnectMultiTaskNet (EfficientNet-B0)\n• Frozen Validation Decision Thresholds"]

        VesselSeg["VesselSegmenter (vessel_segmentation.py)\n• Residual U-Net (ResUNet 4-stage)\n• Green Channel + CLAHE Normalization\n• 256x256 Patch Overlap (Stride 128)\n• Vessel Density Calculation"]

        Checkpoints["Checkpoint Weights\n• best_model.pt (MultiTaskNet Experiment B, 48.7 MB)\n• residual_unet_best.pt (ResUNet, 32.7 MB)"]
    end

    %% Communication Connections
    Browser <-->|HTTP / HTTPS| PresentationTier
    PresentationTier --> SecurityTier
    SecurityTier --> ControllerTier
    ControllerTier --> DataAccessTier
    DataAccessTier --> DBConn
    DBConn <-->|JDBC TCP/3306| MySQL
    
    %% AI Screening Bridge
    CVDS -->|Image Bytes + Metadata| CVDClient
    CVDClient <-->|REST HTTP/1.1 POST /predict & /segment\nX-API-Key Header| FastAPI
    FastAPI --> Predictor
    FastAPI --> VesselSeg
    Predictor --> Checkpoints
    VesselSeg --> Checkpoints
    CVDClient -->|CVDScreening Model Object| CVDS
    CVDS -->|Save Record| CVDDAO
    CVDDAO --> MySQL
```

---

## 3. Detailed Component Interaction Flows

### 3.1 Core Hospital Management Workflow (CRUD & Database)

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Hospital Staff / Receptionist
    participant Browser as Web Browser
    participant Filter as AuthenticationFilter
    participant Servlet as PatientServlet
    participant DAO as PatientDAO
    participant DB as MySQL Database

    Staff->>Browser: Fill "Add Patient" form and click Save
    Browser->>Filter: HTTP POST /PatientServlet (action=insert)
    Filter->>Filter: Verify session != null and role in [ADMIN, DOCTOR, RECEPTIONIST]
    Filter->>Servlet: Forward valid authenticated request
    Servlet->>Servlet: Validate fields (Name, Age, Gender, Phone, Address)
    Servlet->>DAO: addPatient(patientObject)
    DAO->>DB: INSERT INTO patients (name, age, gender, phone, address) VALUES (?, ?, ?, ?, ?)
    DB-->>DAO: 1 Row Affected (Generated ID)
    DAO-->>Servlet: return true
    Servlet-->>Browser: HTTP 302 Redirect to /PatientServlet?action=list&msg=added
    Browser->>Staff: Render updated Patient Directory with success alert
```

---

### 3.2 Retinal Screening & AI Inference End-to-End Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Doctor as Doctor / Clinician
    participant UI as new-screening.jsp
    participant CVDServ as CVDServlet
    participant Client as CVDClient.java
    participant API as FastAPI (api_server.py)
    participant Model as EfficientNet-B0 (inference.py)
    participant UNet as Residual U-Net (vessel_segmentation.py)
    participant DAO as CVDScreeningDAO
    participant DB as MySQL Database
    participant Report as cvd-report.jsp

    Doctor->>UI: Select Patient #101, attach fundus photograph, click "Run Screening"
    UI->>CVDServ: HTTP POST /CVDServlet (action=analyze, multipart/form-data)
    
    rect rgb(240, 248, 255)
        note over CVDServ: Validation & Security Gate
        CVDServ->>CVDServ: Validate CSRF Token via CSRFUtil
        CVDServ->>CVDServ: Verify Session Role (ADMIN or DOCTOR)
        CVDServ->>CVDServ: Validate File (Extension in [.jpg, .jpeg, .png], Size <= 25MB)
        CVDServ->>CVDServ: Save image to /uploads/fundus/fundus_{uuid}.jpg
    end

    CVDServ->>Client: analyzeImage(imageBytes, filename)
    Client->>Client: Encode multipart body & attach X-API-Key header
    Client->>API: HTTP POST http://127.0.0.1:5000/predict
    
    rect rgb(245, 255, 250)
        note over API,Model: Python AI Inference Microservice
        API->>API: Constant-time verify X-API-Key
        API->>API: Verify rate limiter (< 60 req/min for IP)
        API->>API: Pillow verify & convert to RGB (>= 64x64, <= 10000x10000)
        API->>Model: predict(image)
        Model->>Model: Resize (224x224 bilinear antialias) + Normalize (ImageNet)
        Model->>Model: Forward pass through features (1280 dim) + 3 Task Heads
        Model->>Model: Sigmoid (VD, HT) & Softmax (DR 5-class)
        Model->>Model: Compare against frozen validation thresholds (VD: 0.4996, HT: 0.4288)
        Model-->>API: Return prediction dict + research disclaimers
        API-->>Client: HTTP 200 JSON Response
    end

    Client-->>CVDServ: Return populated CVDScreening object

    rect rgb(255, 250, 240)
        note over CVDServ,UNet: Optional Residual U-Net Vessel Segmentation
        CVDServ->>Client: segmentVessels(imageBytes, filename)
        Client->>API: HTTP POST http://127.0.0.1:5000/segment
        API->>UNet: segment_vessels(image)
        UNet->>UNet: Overlapping tile inference (256x256 patch, stride 128)
        UNet-->>API: Binary PNG mask + X-Vessel-Density header
        API-->>Client: HTTP 200 PNG bytes + Header
        Client-->>CVDServ: Return VesselResult (overlay bytes + density %)
        CVDServ->>CVDServ: Save overlay to /uploads/fundus/vessel_{uuid}.png
    end

    CVDServ->>DAO: saveScreening(screeningRecord)
    DAO->>DB: INSERT INTO cvd_screenings (...) VALUES (...)
    DB-->>DAO: Generated screening_id (#42)
    CVDServ->>DAO: updateVesselResult(42, "uploads/fundus/vessel_...", densityPercent)
    DAO->>DB: UPDATE cvd_screenings SET vessel_overlay_path=?, vessel_density=? WHERE screening_id=42
    
    CVDServ-->>Doctor: HTTP 302 Redirect to /CVDServlet?action=view&id=42&msg=analyzed
    Doctor->>Report: Render cvd-report.jsp (Continuous probabilities, thresholds, vessel overlay, print view)
```

---

## 4. Subsystem Breakdown and Boundaries

### 4.1 Java Application Layer
- **Runtime Environment:** Java 21 LTS (tested with build `21.0.12.1+1-LTS-4`).
- **Servlet Specification:** Jakarta Servlet 6.0 (`jakarta.servlet-api-6.0.0.jar`).
- **Application Server:** Apache Tomcat 10.1 (`apache-tomcat-10.1.57`).
- **Database Driver:** MySQL Connector/J 26.7.0 (`com.mysql.cj.jdbc.Driver`).
- **Package Architecture:**
  - `com.hms.controller`: HTTP request routing, session validation, form extraction, view forwarding.
  - `com.hms.filter`: Global URL pattern filtering (`/*`) ensuring no unauthenticated visitor accesses internal JSPs or servlets.
  - `com.hms.model`: Plain Old Java Objects (POJOs) representing domain entities (`User`, `Patient`, `Doctor`, `Appointment`, `Bill`, `CVDScreening`).
  - `com.hms.dao`: Direct JDBC Data Access Objects with `PreparedStatement` parameterized queries.
  - `com.hms.service`: Inter-process communication client (`CVDClient`) managing HTTP REST interactions with the Python microservice.
  - `com.hms.util`: Cross-cutting utilities for cryptography (`PasswordUtil`), database lifecycle (`DBConnection`), CSRF protection (`CSRFUtil`), XSS output sanitization (`HtmlUtil`), and administrator bootstrapping (`AdminProvisioner`).
  - `com.hms.test`: Automated regression and security verification suites (`SecurityRemediationTest`, `HMSSystemIntegrationTest`, `EndToEndServiceTest`).

### 4.2 Python AI Microservice Layer
- **Runtime Environment:** Python 3.12 within isolated virtual environment `C:\Users\vinay\cvd-env`.
- **Framework:** FastAPI 0.142+ powered by Uvicorn ASGI server.
- **Deep Learning Framework:** PyTorch 2.14.1 (CPU execution) with Torchvision 0.29.1.
- **Image Processing:** Pillow 12.3.0 and OpenCV (`opencv-python-headless` >= 4.9).
- **Service Security:**
  - Bound exclusively to localhost loopback `127.0.0.1:5000` (refuses remote network traffic).
  - Pre-shared secret header authentication via `X-API-Key` using constant-time digest comparison (`hmac.compare_digest`).
  - Per-IP rolling rate limiter enforcing 60 requests per minute to prevent resource starvation.
  - Sanitized health endpoint that conceals physical filesystem paths from callers.
- **Model Checkpoints:**
  - `best_model.pt` (48.7 MB): Verified Experiment B weights (`CareConnectMultiTaskNet`).
  - `residual_unet_best.pt` (32.7 MB): Verified weights for Residual U-Net retinal vessel segmentation.

### 4.3 Database Layer (MySQL 8.4)
- **Database Name:** `hospital` (configurable via `HMS_DB_URL`).
- **Tables:** `users`, `patients`, `doctors`, `appointments`, `bills`, `cvd_screenings`.
- **Integrity Constraints:** Foreign key references enforcing patient and doctor associations; atomic multi-table transaction blocks in `PatientDAO` ensuring zero orphaned screening records.

---

## 5. Network & Security Perimeter

| Perimeter Zone | Component | Protocol / Port | Access Rule | Authentication / Protection |
| :--- | :--- | :--- | :--- | :--- |
| **Public / LAN Client** | Web Browser | HTTP / 8080 | Allowed | Session Cookie (`HttpOnly`), `AuthenticationFilter` gate |
| **Web Container** | Tomcat 10.1 | TCP / 8080 | Inbound from Client | Role-Based Access Control (`ADMIN`, `DOCTOR`, `RECEPTIONIST`) |
| **Database Server** | MySQL 8.4 | TCP / 3306 | Localhost Only | Parametric JDBC connection (`PreparedStatement`), external credentials |
| **AI Microservice** | FastAPI / Uvicorn | TCP / 5000 | `127.0.0.1` Only | `X-API-Key` pre-shared secret, per-IP rate limit, CORS origin whitelist |

---

*End of Architecture Documentation.*
