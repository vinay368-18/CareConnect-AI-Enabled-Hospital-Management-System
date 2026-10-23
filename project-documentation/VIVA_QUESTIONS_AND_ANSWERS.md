# CareConnect HMS & Retinal AI: Viva & Presentation Preparation Guide

**Document ID:** `VIVA_QUESTIONS_AND_ANSWERS.md`  
**System:** CareConnect Hospital Management System with Retinal AI Screening  
**Academic / Viva Level:** Undergraduate & Master's Degree Examination Ready  
**Date:** October 2026  

---

## 1. One-Minute Elevator Pitch

> "CareConnect is an integrated hospital management and assistive clinical AI platform that merges full-stack hospital administration with deep learning retinal screening. 
> 
> The core hospital subsystem is built with Java 21, Jakarta Servlet 6.0, and MySQL, providing secure, role-based workflows for patient demographics, appointments, doctor scheduling, and billing, hardened against OWASP vulnerabilities with PBKDF2 password hashing, CSRF tokens, and atomic transactions. 
> 
> The retinal AI subsystem is an isolated Python FastAPI microservice running a multi-task deep neural network with an EfficientNet-B0 backbone and a Residual U-Net for retinal vessel segmentation. Clinicians upload a patient's retinal fundus photo directly within their clinical workflow to receive multi-task screening indicators for vascular disease, systemic hypertension, and diabetic retinopathy, backed by validation-calibrated decision thresholds. 
> 
> Importantly, our project adheres strictly to clinical ethics: we report that mobile retinal photos yield a held-out test ROC-AUC of 0.52 for systemic vascular disease, so we present our predictions as experimental screening markers rather than an automated diagnosis, always directing clinicians to standard ECG, lipid panels, and physical examinations."

---

## 2. Five-Minute Presentation Outline

### Minute 1: The Problem & Clinical Motivation
- **Clinical Need:** Cardiovascular disease (CVD) is the leading cause of global mortality. While high-end clinical diagnosis requires electrocardiograms, echocardiograms, and blood biomarkers, retinal microvasculature offers a non-invasive optical window into the body's vascular health.
- **The Gap:** Standard hospital management systems (HMS) store administrative records (patients, appointments, bills) completely disconnected from modern clinical AI decision-support tools.
- **Our Solution:** A unified system that integrates clinical record management with assistive deep learning retinal screening in a single workflow.

### Minute 2: Hybrid System Architecture
- **Loosely Coupled Microservices:** Rather than forcing Python and Java into an unstable monolithic wrapper, the application is divided into:
  1. A **Java 21 / Tomcat 10.1 EE Web Application** managing clinical administration, authentication, and report persistence.
  2. A **Python 3.12 / FastAPI Microservice** running deep learning inference on CPU via PyTorch.
- **Communication:** Synchronous HTTP/1.1 REST across localhost loopback with `X-API-Key` pre-shared secret authentication and per-IP rate limiting.

### Minute 3: Deep Learning Multi-Task Pipeline
- **Dataset:** mBRSET (Mobile Brazilian Retinal Dataset) collected via handheld smartphone attachments (Phelcom Eyer) on 1,289 patients.
- **Scientific Audit & Ground Truth Purity:** We eliminated a critical flaw present in prior work where acute myocardial infarction was erroneously conflated with vascular disease. We enforced strict patient-level partitioning ($N_{\text{train}}=889, N_{\text{val}}=190, N_{\text{test}}=191$) with zero data leakage.
- **Model Architecture:** `CareConnectMultiTaskNet` utilizing an EfficientNet-B0 backbone (1,280 features) coupled with three task heads:
  1. `head_vd`: Binary vascular disease screening.
  2. `head_ht`: Binary systemic hypertension marker.
  3. `head_dr`: 5-class Diabetic Retinopathy ICDR grading.
- **Vessel Segmentation:** A 4-stage Residual U-Net segmenting retinal blood vessels to compute vessel density percentage.

### Minute 4: Rigorous Scientific Evaluation & Honest Boundaries
- **Diabetic Retinopathy (Direct Ocular Finding):** **76.99% test accuracy**, **0.6918 Weighted F1**, demonstrating strong ability to detect visible ocular microaneurysms and hemorrhages.
- **Vascular Disease (Systemic Target):** **0.5202 held-out test ROC-AUC** (95% CI: `[0.3936, 0.6416]`). Retraining improved clinical sensitivity from 28.1% to 56.25% by handling class imbalance with positive weighting ($w=4.871$).
- **Ethical Presentation:** Because systemic vascular discrimination from smartphone fundus scans alone is near chance, our reports frame predictions honestly as **experimental research markers**, mandating physician review, 12-lead ECG, and lipid testing.

### Minute 5: Security Engineering, Enterprise Reliability & Conclusion
- **P0 Security Hardening:** Upgraded from plaintext passwords to PBKDF2 with HMAC-SHA256 (210,000 iterations); externalized credentials from code to environment variables; enforced session-bound CSRF validation; sanitized dynamic output against XSS; implemented atomic cascading deletions in MySQL.
- **Verification:** 100% pass rates across 17 Java security tests, 13 Python microservice tests, and 9 data pipeline tests.
- **Takeaway:** CareConnect demonstrates how to build an enterprise healthcare platform that combines robust full-stack engineering with honest, scientifically evaluated artificial intelligence.

---

## 3. Comprehensive Viva Questions and Project-Specific Answers

### Section A: System Architecture & Technologies

#### Q1. Why did you choose a hybrid Java + Python architecture instead of implementing everything in a single language?
**Answer:** Java with Jakarta EE / Tomcat is an industry standard for enterprise hospital management because of its strong type safety, mature servlet security filters, session handling, and robust JDBC relational database performance. On the other hand, the deep learning and computer vision ecosystem (PyTorch, Torchvision, CUDA, OpenCV) is predominantly built and maintained in Python. Attempting to run deep neural networks inside the Java Virtual Machine using JNI or Jython is brittle, poorly supported for modern PyTorch architectures, and risks bringing down the hospital application server during memory-intensive tensor operations. A loosely coupled microservice over local REST allows both languages to excel at their primary strengths while maintaining strict process isolation.

#### Q2. How do the Java application and Python AI service communicate?
**Answer:** The Java backend uses the standard Java 21 `java.net.http.HttpClient` implemented in `com.hms.service.CVDClient`. When a clinician uploads a fundus photograph, `CVDServlet` forwards the raw image bytes as a `multipart/form-data` payload over an HTTP/1.1 POST request to `http://127.0.0.1:5000/predict`. The client includes a pre-shared secret in the `X-API-Key` HTTP header. The Python FastAPI microservice validates the key, processes the image in memory using Pillow and PyTorch, and returns a structured JSON response containing predicted probabilities, classifications, frozen decision thresholds, and clinical disclaimers.

#### Q3. What happens if the Python AI microservice is offline or crashes?
**Answer:** The system handles this gracefully through fault-tolerant design:
1. `CVDClient.isServiceAvailable()` sends a lightweight `GET /health` request with a 4-second timeout.
2. In the web UI (`new-screening.jsp` and `cvd-screenings.jsp`), an active status badge alerts the clinician whether the AI microservice is `Online` or `Offline`.
3. If an upload is attempted while the service is down, `CVDServlet` intercepts the failure, logs the event, and redirects the user with an alert: `error=ai_offline`.
4. Core hospital functions (patient registration, doctor schedules, billing, and viewing prior persisted screening reports) continue operating with zero disruption because MySQL and Tomcat remain completely independent.

#### Q4. What versions of Java, Tomcat, and Python does the project use?
**Answer:**
- **Java:** Java 21 LTS (verified runtime: `build 21.0.12.1+1-LTS-4`).
- **Servlet Specification:** Jakarta Servlet 6.0 (`jakarta.servlet-api-6.0.0.jar`).
- **Application Server:** Apache Tomcat 10.1 (`10.1.57`).
- **Python:** Python 3.12 (in dedicated virtual environment `cvd-env`).
- **PyTorch:** PyTorch 2.14.1 with Torchvision 0.29.1.
- **Database:** MySQL 8.4 with MySQL Connector/J 26.7.0.

#### Q5. Why is Apache Tomcat 10.x used instead of Tomcat 9.x?
**Answer:** Tomcat 10.x implements the Jakarta EE specifications where the package namespace transitioned from legacy `javax.servlet.*` to modern `jakarta.servlet.*` (Jakarta Servlet 6.0). Our servlets, filters, and listeners use `jakarta.servlet.*`, which requires Tomcat 10 or later.

---

### Section B: Database & Relational Persistence

#### Q6. What is the relational schema of your hospital database?
**Answer:** The database consists of six core tables:
1. `users`: Stores user credentials (`user_id`, `username`, `password`, `role`, `doctor_id`).
2. `patients`: Stores patient demographics (`patient_id`, `name`, `age`, `gender`, `phone`, `address`).
3. `doctors`: Stores doctor profiles (`doctor_id`, `name`, `specialization`, `phone`, `email`, `experience`, `consultation_fee`).
4. `appointments`: Stores scheduled consultations (`appointment_id`, `patient_id`, `doctor_id`, `appointment_date`, `appointment_time`, `reason`, `status`).
5. `bills`: Stores financial invoices (`bill_id`, `patient_id`, `appointment_id`, `amount`, `payment_method`, `payment_status`, `bill_date`).
6. `cvd_screenings`: Stores AI screening records (`screening_id`, `patient_id`, `doctor_id`, `appointment_id`, `image_path`, `cvd_prediction`, `cvd_probability`, `hypertension_prediction`, `hypertension_probability`, `dr_grade`, `dr_confidence`, `risk_level`, `notes`, `screening_date`, `vessel_overlay_path`, `vessel_density`).

#### Q7. How did you handle referential integrity and avoid orphaned records when deleting a patient?
**Answer:** We implemented an atomic multi-table transaction inside `PatientDAO.deletePatient(int id)`. Deleting a patient with simple SQL would fail foreign key constraints or leave orphaned medical screenings. We set `con.setAutoCommit(false)` and within a single transaction sequentially delete associated records from `cvd_screenings`, `bills`, `billing`, and `appointments`, before deleting the record from `patients`. If any query fails, `con.rollback()` is triggered, guaranteeing that the database is never left in an inconsistent state.

#### Q8. Why does the code use `PreparedStatement` instead of standard `Statement`?
**Answer:** `PreparedStatement` pre-compiles SQL queries and binds user parameters separately from the command syntax using placeholders (`?`). This completely neutralizes SQL Injection (SQLi) attacks because user inputs are treated strictly as literal data rather than executable SQL syntax. Additionally, the database engine caches query execution plans, improving database performance.

---

### Section C: Machine Learning, Dataset & Clinical Reality

#### Q9. What dataset was used to train the retinal screening model?
**Answer:** The model was trained and evaluated on **mBRSET (Mobile Brazilian Retinal Dataset v1.0)**, comprising 4,002 verified retinal photographs from 1,289 patients collected across primary healthcare centers in Brazil. The photographs were captured using a portable smartphone attachment (Phelcom Eyer) on non-mydriatic (un-dilated) pupils. The dataset includes demographic information and clinical labels for vascular disease, systemic hypertension, and diabetic retinopathy.

#### Q10. What critical flaw was identified in prior baseline implementations regarding the target definition?
**Answer:** A forensic data audit revealed that the earlier baseline implementation improperly conflated two distinct diagnostic categories: `vascular_disease` and `acute_myocardial_infarction` (AMI). 232 records in `labels_mbrset.csv` had `vascular_disease == 0.0` but `acute_myocardial_infarction == 1.0`. Merging them created an artificial composite target that contaminated ground truth definitions and distorted the model's loss landscape. We corrected this by isolating pure `vascular_disease` as the primary target and retaining AMI solely in metadata for audit.

#### Q11. How did you prevent data leakage between training, validation, and test sets?
**Answer:** In medical imaging, data leakage occurs if multiple images of the same patient (e.g., left and right eye, or repeated scans) appear across both training and test partitions. The network can memorize patient-specific ocular features (such as retinal pigment or optic disc shape) rather than generalizable disease pathology. We enforced strict **patient-level partitioning** where all images belonging to a single patient ID reside exclusively in one partition ($\text{Train} \cap \text{Val} = \emptyset$, $\text{Train} \cap \text{Test} = \emptyset$, $\text{Val} \cap \text{Test} = \emptyset$). This invariant is verified by automated test `test_03_zero_patient_leakage` in `test_data_pipeline.py`.

#### Q12. Explain the architecture of `CareConnectMultiTaskNet`.
**Answer:** It is a multi-task deep convolutional neural network based on an **EfficientNet-B0** backbone. 
- Input: A $3 \times 224 \times 224$ normalized RGB retinal fundus tensor.
- Feature Extractor: The convolutional feature extractor maps the input into a 1,280-dimensional feature vector, pooled via adaptive average pooling and regularized with a dropout rate of $p=0.4$.
- Task Heads: Three parallel linear projection heads branch off the shared features:
  1. `head_vd`: Linear layer mapping $1,280 \to 1$ (raw logit for vascular disease).
  2. `head_ht`: Linear layer mapping $1,280 \to 1$ (raw logit for systemic hypertension).
  3. `head_dr`: Linear layer mapping $1,280 \to 5$ (logits for 5 ICDR Diabetic Retinopathy grades).

#### Q13. What is the Residual U-Net and what role does it play?
**Answer:** The Residual U-Net (`ResUNet`) is a 4-stage convolutional encoder-decoder network with residual skip connections (`ResBlock`) designed for semantic segmentation of retinal blood vessels. It operates on overlapping $256 \times 256$ patches with green channel extraction and Contrast Limited Adaptive Histogram Equalization (CLAHE). It outputs a transparent PNG mask highlighting the segmented vascular tree and calculates the **vessel density percentage** (ratio of vessel pixels to total retinal area). This visual overlay helps clinicians inspect microvascular structure directly on the screening report.

#### Q14. What are the held-out test results for systemic vascular disease, and what does an ROC-AUC of 0.52 mean?
**Answer:** On the strictly held-out patient test partition ($N=191$ patients, 32 positive cases), the image-only model achieved an **ROC-AUC of 0.5202** with a 95% bootstrap confidence interval of `[0.3936, 0.6416]`. 
An ROC-AUC of 0.50 represents random chance (equivalent to a coin flip). An ROC-AUC of 0.52 indicates that mobile smartphone fundus photographs alone exhibit weak discrimination for systemic cardiovascular disease. This is a critical scientific finding: systemic vascular disease manifests primarily through subtle microscopic microvascular shifts ($10\,\mu\text{m}$ caliber changes) that handheld smartphone camera lenses on un-dilated pupils cannot reliably resolve without clinical biomarkers.

#### Q15. Why does Diabetic Retinopathy perform with high accuracy (76.99%) while Vascular Disease performs near chance?
**Answer:** Diabetic Retinopathy is a **direct ocular pathology**: its manifestations (microaneurysms, hemorrhages, hard exudates, cotton-wool spots, and neovascularization) are physically located on the retina and clearly visible at 224x224 resolution. Therefore, the convolutional feature extractor successfully learns these patterns, achieving **76.99% test accuracy** and **0.6918 Weighted F1**. In contrast, systemic cardiovascular disease is an indirect systemic condition that only secondarily influences retinal microvessels. High DR accuracy proves the vision pipeline works, but it cannot be extrapolated as proof of CVD accuracy.

#### Q16. How did you choose decision thresholds for CVD and Hypertension?
**Answer:** Decision thresholds were optimized strictly on the **Validation cohort** ($N=190$ patients) using **Youden's $J$ statistic** ($J = \text{Sensitivity} + \text{Specificity} - 1$) and subsequently **frozen** before test evaluation. The frozen validation thresholds are **0.4996** for vascular disease and **0.4288** for systemic hypertension. Test data was never used for threshold tuning, which prevented threshold overfitting.

---

### Section D: Application Security & OWASP Remediation

#### Q17. How are user passwords stored and verified in the database?
**Answer:** Passwords are never stored in plaintext or with simple unsalted hashes (like MD5 or SHA-256). We implemented `PBKDF2WithHmacSHA256` in `PasswordUtil.java` using 210,000 iterations, a 16-byte cryptographically secure random salt (`SecureRandom`), and a 256-bit derived key. The stored format is `PBKDF2$210000$<salt_hex>$<hash_hex>`. Verification uses `MessageDigest.isEqual` to execute in constant time, preventing timing side-channel attacks.

#### Q18. How does the system handle legacy plaintext user accounts created before security remediation?
**Answer:** `UserDAO.login()` implements transparent on-the-fly migration. When an existing user logs in with a legacy plaintext password, the system verifies the credentials, immediately hashes the password with PBKDF2, and automatically updates the database (`UserDAO.updatePassword()`). This ensures zero user lockout while eliminating legacy plaintext credentials upon first login.

#### Q19. How did you protect against Cross-Site Request Forgery (CSRF)?
**Answer:** `CSRFUtil.java` generates a unique, cryptographically random UUID token stored in the user's `HttpSession`. Every state-modifying form (in `add-patient.jsp`, `edit-doctor.jsp`, `new-screening.jsp`, etc.) includes this token as a hidden input field. Upon form submission, the corresponding servlet calls `CSRFUtil.isValid(request)`, which validates the token using constant-time comparison before processing the request. Furthermore, state-modifying actions via GET requests (such as `?action=delete&id=X`) are strictly rejected.

#### Q20. How is Cross-Site Scripting (XSS) mitigated in JSP views?
**Answer:** Dynamic database outputs (such as patient names, contact numbers, and doctor specializations) are escaped using `HtmlUtil.escape()` before being interpolated into HTML. This converts sensitive characters (`<`, `>`, `&`, `"`, `'`, `/`) into their corresponding safe HTML entities, preventing stored XSS injection attacks.

#### Q21. How is the Python AI microservice secured against unauthorized requests?
**Answer:** The microservice enforces multiple layers of security:
1. **Network Binding:** Bound strictly to localhost `127.0.0.1:5000`, rejecting external network packets.
2. **Pre-Shared Secret:** Inference and segmentation endpoints require an `X-API-Key` HTTP header verified via `hmac.compare_digest`.
3. **Rate Limiting:** An in-memory rolling rate limiter limits callers to 60 requests per minute per IP to prevent resource exhaustion.
4. **Input Sanitization:** Uploaded files are verified to be $\le 25\text{ MB}$, verified via Pillow for image integrity, and validated for minimum ($64 \times 64$) and maximum ($10,000 \times 10,000$) dimensions.
5. **Path Leak Prevention:** The `/health` endpoint is stripped of physical server paths.

---

### Section E: Clinical Ethics, Limitations & Future Work

#### Q22. What makes this project clinically responsible compared to naive AI projects?
**Answer:** Naive AI projects often claim to "diagnose heart attacks and CVD from eye scans with 95% accuracy," which is scientifically untrue and clinically dangerous. CareConnect adheres strictly to medical ethics:
- We explicitly communicate the true held-out test ROC-AUC (0.52).
- We label vascular disease outputs as **"Experimental Research Markers"** rather than definitive diagnostic conclusions.
- Every generated screening report includes a mandatory clinical disclaimer advising attending physicians to perform standard physical examinations, sphygmomanometer blood pressure checks, fasting lipid profiles, and 12-lead ECGs.
- We clearly separate ocular disease findings (Diabetic Retinopathy) from systemic vascular indicators.

#### Q23. What are the current limitations of the system?
**Answer:**
1. **Image-Only Systemic Discrimination:** As proven by our experiments, predicting systemic cardiovascular disease from mobile fundus photos alone has low discrimination without systemic clinical biomarkers.
2. **CPU Inference Latency:** Running the deep neural network and Residual U-Net on CPU takes 4 to 8 seconds per image. A dedicated GPU server would reduce latency to under 300 ms.
3. **Database Migration Scripts:** Live schema initialization currently relies on manual SQL execution or standard DBA tools rather than an automated migration tool like Flyway or Liquibase.

#### Q24. How would you improve the system in future development?
**Answer:**
1. **Multimodal Clinical Fusion:** Integrate structured clinical features already present in electronic health records (age, sex, BMI, systolic/diastolic blood pressure, smoking history, HbA1c) alongside image embeddings using a cross-attention fusion network.
2. **Automated Database Migrations:** Integrate Flyway or Liquibase into the Java build lifecycle for version-controlled schema migrations.
3. **Containerized Deployment:** Package the Java Tomcat web application and Python FastAPI microservice into Docker containers managed with Docker Compose.
4. **Active Learning & Clinician Feedback Loop:** Allow attending ophthalmologists and cardiologists to submit confirmed clinical diagnoses back into the system to build an authenticated clinical ground-truth fine-tuning repository.

#### Q25. What were your key learnings from building and auditing this project?
**Answer:**
1. **Full-Stack Architecture:** Coordinating asynchronous multipart file transfers across independent runtimes (Java EE and Python FastAPI) with secure session handling and error resilience.
2. **Data Science Rigor:** The vital importance of forensic data audits—discovering how easy it is to introduce target conflation (VD vs. AMI) or patient-level data leakage that creates false illusions of high accuracy.
3. **Software Security:** Implementing defense-in-depth principles: externalizing credentials, securing sessions against fixation, neutralizing CSRF, escaping dynamic HTML against XSS, and protecting API endpoints with pre-shared secrets and rate limits.
4. **Clinical Humility:** Understanding that responsible medical AI requires honest reporting of negative or near-chance results rather than exaggerating capabilities.

---

*End of Viva & Presentation Preparation Guide.*
