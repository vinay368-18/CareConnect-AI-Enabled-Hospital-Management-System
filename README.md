# CareConnect — AI-Enabled Hospital Management System

A Java / Jakarta EE hospital management web application with a separate Python
deep-learning microservice that analyses retinal fundus photographs.

Staff log in by role and manage the day-to-day records of a small hospital —
patients, doctors, appointments and bills — with a reports dashboard on top. The
**CVD Diagnostics** module sends a retinal photograph to a PyTorch model, which returns
three indicators for that image (vascular disease, hypertension and a
diabetic-retinopathy grade), plus a blood-vessel segmentation overlay. The result is
stored as a screening record and shown as a printable report.

> **Research prototype — not a medical device.** The AI module is an experimental
> research prototype. It is not clinically validated and must not be used for
> diagnosis, triage or any medical decision. The measured performance below explains
> why: the cardiovascular indicator is no better than chance.

---

## Contents

- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
- [AI service API](#ai-service-api)
- [Web application routes](#web-application-routes)
- [The model and its measured performance](#the-model-and-its-measured-performance)
- [Security](#security)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Further documentation](#further-documentation)

---

## Architecture

The system runs as **three separate processes**, and all three must be running:

| Process | Technology | Address | Responsibility |
|---|---|---|---|
| Web application | Java 21 on Apache Tomcat 10.1 | `localhost:8080` | All pages, login and permissions, reads and writes the database, calls the AI service |
| AI microservice | Python, FastAPI, Uvicorn, PyTorch | `127.0.0.1:5000` | Holds the models in memory and answers image-analysis requests. Knows nothing about patients, logins or the database |
| Database | MySQL 8 | `localhost:3306` | Persistent storage in the `hospital` schema |

```
 Browser  ── plain HTML forms, full page loads (no AJAX)
    │  HTTP :8080
    ▼
 ┌──────────────────────── Tomcat 10.1 (Java 21) ────────────────────────┐
 │  AuthenticationFilter  (runs on every request: logged in? else login) │
 │            │                                                          │
 │            ▼                                                          │
 │  Servlets (controllers) ── role check · CSRF check · input validation │
 │            │                                   │                      │
 │            ▼                                   ▼                      │
 │  DAOs (all SQL, PreparedStatement only)    CVDClient (HTTP client)    │
 │            │                                   │                      │
 │            ▼                                   │                      │
 │  JSP views (server-side rendered)              │                      │
 └────────────┼───────────────────────────────────┼──────────────────────┘
              │ JDBC :3306                         │ HTTP :5000, X-API-Key
              ▼                                    ▼
 ┌────────── MySQL 8 ──────────┐    ┌──── FastAPI + PyTorch (CPU) ─────────┐
 │ schema: hospital            │    │ EfficientNet-B0, three heads          │
 │ users  patients  doctors    │    │   → vascular disease / hypertension   │
 │ appointments  bills         │    │   → DR grade (5 ICDR classes)         │
 │ cvd_screenings              │    │ Residual U-Net vessel segmentation    │
 └─────────────────────────────┘    └───────────────────────────────────────┘
```

**Why the AI is a separate service:** the model ecosystem (PyTorch, torchvision,
Pillow, OpenCV) is Python. The checkpoints (about 48 MB and 32 MB) load once at startup
and stay in memory. The hospital app keeps working when the AI service is down; only
new screenings are blocked, behind an "AI Microservice Offline" message. The model
can also be retrained and restarted without redeploying the web app.

### A screening, end to end

1. The filter checks the session; `CVDServlet` checks the role and the CSRF token.
2. The patient is verified against the database. If the user is a doctor, the doctor
   is forced to the logged-in user, so attribution cannot be spoofed.
3. The image is taken from an upload or a bundled sample, its extension is checked, and
   it is saved under a randomised name `fundus_<uuid>_<ms>`.
4. `CVDClient` probes `GET /health`, then sends a multipart `POST /predict` with the API key.
5. Python re-validates the image, resizes it to 224×224, normalises it, runs the three
   heads and applies the frozen thresholds.
6. The JSON response is parsed, `CVDScreeningDAO.saveScreening()` stores it and returns
   the new ID, and the browser is redirected to the report.
7. `POST /segment` draws the vessel overlay. This step is best-effort: if it fails, the
   screening is still saved.

---

## Technology stack

| Layer | Technology |
|---|---|
| Language / runtime | Java 21 |
| Web container | Apache Tomcat 10.1 (Jakarta Servlet 6.0; **Tomcat 9 will not work**) |
| Views | JSP (server-side rendering) |
| Data access | Raw JDBC with `PreparedStatement` — no ORM |
| Database | MySQL 8, Connector/J 26.7.0 (bundled) |
| JSON | Hand-written `SimpleJsonParser` (no external library) |
| HTTP client | `java.net.http.HttpClient` |
| AI service | Python 3.10–3.12, FastAPI, Uvicorn, Pydantic |
| Deep learning | PyTorch, torchvision (CPU inference) |
| Image processing | Pillow, OpenCV (CLAHE) |
| Research UI | Gradio (`cvd-ai-service/app.py`, separate from the web app) |
| IDE / build | Eclipse Dynamic Web Project (no Maven or Gradle) |

---

## Repository layout

```
src/main/java/com/hms/
  controller/   9 servlets: Login, Logout, Register, Patient, Doctor,
                Appointment, Billing, Report, CVD
  dao/          7 DAOs: User, Patient, Doctor, Appointment, Billing, Report, CVDScreening
  model/        plain data classes (Patient, Doctor, CVDScreening, ...)
  service/      CVDClient: the only class that talks to the Python service
  filter/       AuthenticationFilter: the login gate for every request
  util/         DBConnection, PasswordUtil, CSRFUtil, HtmlUtil, AdminProvisioner
src/main/webapp/
  *.jsp         21 pages (login, dashboard, patients, doctors, appointments,
                billing, reports, CVD screening list / new screening / report, ...)
  WEB-INF/      web.xml and the two bundled JARs (servlet API, MySQL driver)
cvd-ai-service/
  api_server.py           FastAPI service: the one the web app uses
  inference.py            multi-task model loading, preprocessing and prediction
  vessel_segmentation.py  Residual U-Net vessel segmentation
  app.py                  standalone Gradio research UI (not used by the web app)
  config.json             runtime model configuration and frozen thresholds
  models/                 served checkpoints: best_model.pt, residual_unet_best.pt
  evaluation/             held-out test metrics for the served model
  test_ai_service.py      13 service checks
db/
  01_core_schema.sql        database + users, patients, doctors, appointments, bills
  cvd_screenings_schema.sql the screenings table (re-runnable)
  add_vessel_columns.sql    migration for older databases
ml/                       training code, configs, experiment metrics and reports
project-documentation/    architecture, setup, file-by-file guide, project report
.env.example              template for every environment variable
start_cvd_ai_service.bat  starts the AI service on Windows
```

---

## Getting started

### 1. Prerequisites

| Component | Version |
|---|---|
| Java JDK | 21 |
| Apache Tomcat | 10.1.x |
| MySQL Server | 8.x |
| Python | 3.10 – 3.12 |
| Eclipse IDE for Enterprise Java (recommended) | any recent release |

The two Java dependencies ship in `src/main/webapp/WEB-INF/lib/`, so nothing needs
downloading.

### 2. Create the database

Run the two scripts **in this order**:

```bash
mysql -u root -p < db/01_core_schema.sql
mysql -u root -p hospital < db/cvd_screenings_schema.sql
```

Check it worked:

```bash
mysql -u root -p -e "USE hospital; SHOW TABLES;"
# users, patients, doctors, appointments, bills, cvd_screenings
```

It's best to create a dedicated MySQL user for the app rather than using `root`.

### 3. Set the environment variables

Every credential is read from the environment. Nothing is hard-coded. Copy
`.env.example` and fill it in:

| Variable | Used by | Required | Purpose |
|---|---|---|---|
| `HMS_DB_USER` | Java | **Yes** | MySQL username |
| `HMS_DB_PASSWORD` | Java | **Yes** | MySQL password (an empty value is accepted for a passwordless local MySQL) |
| `HMS_AI_API_KEY` | Java **and** Python | **Yes** | Shared secret. **It must be the same in both processes** |
| `HMS_DB_URL` | Java | No | Defaults to `jdbc:mysql://localhost:3306/hospital` |
| `HMS_AI_API_URL` | Java | No | Defaults to `http://127.0.0.1:5000` |
| `HMS_CORS_ORIGINS` | Python | No | Defaults to `http://localhost:8080,http://127.0.0.1:8080` |

Java also accepts the system properties `hms.db.url`, `hms.db.user`,
`hms.db.password`, `hms.ai.api.url` and `hms.ai.api.key` as `-D` flags. The order of
precedence is environment variable, then system property, then default.

Make sure Tomcat can actually see these variables. A variable set in one terminal is
invisible to a Tomcat started from Eclipse or as a Windows service. Use one of:

- `<tomcat>/bin/setenv.bat`, which Tomcat reads on startup
- Windows user environment variables, then restart Tomcat
- the **Environment** tab of the server launch configuration in Eclipse

Generate a strong API key with, for example:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Start the AI service

```bash
cd cvd-ai-service
python -m venv .venv
.venv\Scripts\activate            # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt

set HMS_AI_API_KEY=<same value as Tomcat>
python api_server.py
```

`start_cvd_ai_service.bat` does the same, but it points at a machine-specific virtual
environment. Edit the Python path in it before using it.

When both models have loaded, the log ends with:

```
INFO:cvd-api:[CVD API] PyTorch model loaded successfully on CPU.
INFO:cvd-api:[CVD API] Residual U-Net vessel segmentation model loaded.
INFO:     Uvicorn running on http://127.0.0.1:5000
```

Confirm it independently:

```bash
curl http://127.0.0.1:5000/health
# expect "status":"healthy", "model_loaded":true, "vessel_model_loaded":true
```

A `"degraded"` status means the prediction model did not load, which usually means
`models/best_model.pt` is missing.

> Run `api_server.py`, **not** `app.py`. `app.py` (`run_app.bat`) is the separate
> Gradio research UI and does not serve the web application.

### 5. Start the web application

**Eclipse (recommended):**

1. **File → Import → Existing Projects into Workspace**, and select this folder.
2. Add an **Apache Tomcat v10.1** runtime under *Window → Preferences → Server → Runtime Environments*.
3. If Eclipse reports unresolved classpath entries, re-point them at the two JARs in
   `src/main/webapp/WEB-INF/lib/`. The committed `.classpath` uses absolute paths from
   the original development machine.
4. Set the environment variables on the server launch configuration.
5. Right-click the project → **Run As → Run on Server**.

The app is then at `http://localhost:8080/HospitalManagementSystem/`, or at
`http://localhost:8080/` if deployed as the root context.

### 6. Create the first admin account

There is no public sign-up, and registering staff requires an existing admin, so the
first account is created from the command line. Set `HMS_DB_USER` and
`HMS_DB_PASSWORD` in the same shell, then run:

```bash
java -cp "build\classes;src\main\webapp\WEB-INF\lib\*" ^
     com.hms.util.AdminProvisioner provision admin <YourStrongPassword>

# to reset the password later:
java -cp "build\classes;src\main\webapp\WEB-INF\lib\*" ^
     com.hms.util.AdminProvisioner rotate-password admin <NewPassword>
```

Passwords must be at least 8 characters, and `provision` refuses to run if an admin
already exists. Further staff accounts (admin, receptionist, doctor) are created
in-app from **Staff Provisioning** on the dashboard.

### 7. Check it end to end

1. Log in as the admin.
2. Open **CVD Diagnostics**. The badge should read **AI ONLINE**.
3. Click **New Screening**, pick a patient, choose an image and run the analysis.
4. A report should appear with three result cards and a vessel overlay.

The new-screening page offers bundled sample images from
`src/main/webapp/uploads/fundus/samples/`. That folder is excluded from Git because
`uploads/` holds patient data. To use the samples on a fresh clone, place your own
fundus images (`.jpg` or `.png`) in it, or upload an image instead.

---

## AI service API

Base URL `http://127.0.0.1:5000`. The service binds to localhost only, so it is not
reachable from the network.

| Method | Route | Auth | Input | Output |
|---|---|---|---|---|
| `GET` | `/health` | none | — | Liveness, plus whether each model loaded |
| `POST` | `/predict` | `X-API-Key` | multipart `file` (+ optional model name) | JSON: three predictions, probabilities, DR grade, thresholds |
| `POST` | `/predict-base64` | `X-API-Key` | JSON with a base64 image | Same as `/predict` (not used by the Java app) |
| `POST` | `/segment` | `X-API-Key` | multipart `file` | PNG vessel overlay; density in the `X-Vessel-Density` header |

- **Authentication:** `X-API-Key`, compared in constant time (`hmac.compare_digest`).
  If the server has no key configured, every request is rejected.
- **Rate limit:** 60 requests per minute per client IP.
- **Errors:** `400` invalid image, `401` wrong or missing key, `429` rate limited,
  `503` model not loaded or key not configured.

---

## Web application routes

Each servlet handles one entity and dispatches on an `action` request parameter
(`list`, `add`, `edit`, `update`, `delete`, `view`, ...).

| Route | Purpose | Roles |
|---|---|---|
| `/LoginServlet` | Sign in (POST) | public |
| `/LogoutServlet` | Sign out | any |
| `/RegisterServlet` | Create staff accounts | ADMIN |
| `/PatientServlet` | Patient records | role-based |
| `/DoctorServlet` | Doctor records | role-based |
| `/AppointmentServlet` | Appointments | role-based |
| `/BillingServlet` | Bills and payments | role-based |
| `/ReportServlet` | Totals and revenue report | role-based |
| `/CVDServlet` | Screening list, new screening, report, delete | role-based |

Every state-changing request is a CSRF-protected `POST`. `action=delete` is refused on `GET`.

---

## The model and its measured performance

**`CareConnectMultiTaskNet`** is one EfficientNet-B0 backbone producing 1,280 image
features, followed by Dropout 0.4 and three heads:

| Head | Output | Task |
|---|---|---|
| `head_vd` | sigmoid | Vascular disease (CVD) — yes / no |
| `head_ht` | sigmoid | Systemic hypertension — yes / no |
| `head_dr` | softmax | Diabetic-retinopathy grade, 5 ICDR classes |

Input is a single RGB image, resized to 224×224 and given ImageNet normalisation,
run on the CPU. The decision thresholds were tuned with **Youden's J on the validation
split and frozen before the test set was evaluated**: VD **0.4996** and HT **0.4288**
(in `cvd-ai-service/config.json`).

A second model, a **Residual U-Net**, segments the retinal blood vessels. It uses the
green channel with CLAHE contrast enhancement, 256-pixel tiles at stride 128 and a
field-of-view mask, and reports vessel density as a percentage.

### Held-out test results (Experiment B: the served model)

Dataset: mBRSET (Mobile Brazilian Retinal Dataset). The test split is
**patient-level and stratified, with no patient in more than one split**.

| Task | Level | Result | 95% CI |
|---|---|---|---|
| Vascular disease (CVD) | 191 patients, 32 positive | ROC-AUC **0.5202** | 0.3936 – 0.6416 |
| Systemic hypertension | 191 patients, 135 positive | ROC-AUC **0.4679** | 0.3705 – 0.5655 |
| Diabetic retinopathy | 578 images, 5 classes | Accuracy **76.99%** · weighted F1 0.6918 · macro F1 0.289 | — |

Source: `ml/metrics/experiment_b_efficientnet_b0_metrics.json`.

### What the numbers mean

- **CVD and hypertension are indistinguishable from chance.** Both confidence intervals
  include 0.5. A single retinal photograph carried almost no cardiovascular signal in
  this cohort.
- **Diabetic retinopathy is the head that works.** DR is visible in the retina; heart
  disease is not. The low macro F1 shows the rare grades are seldom predicted correctly,
  so the overall accuracy is carried by the dominant "No DR" class.
- **Other architectures and inputs did not change the conclusion:**

  | Experiment | CVD ROC-AUC | 95% CI |
  |---|---|---|
  | A — baseline | 0.5554 | 0.438 – 0.668 |
  | **B — EfficientNet-B0 (served)** | **0.5202** | 0.394 – 0.642 |
  | D — image + demographics fused | 0.5010 | 0.393 – 0.624 |
  | D — demographics only | 0.4583 | 0.357 – 0.576 |

  All the intervals overlap and all include 0.5. Experiment B stays served. Swapping in
  whichever checkpoint has the best *test* AUC would overfit the test set.

The report page states the measured CVD AUC and its confidence interval, and labels the
feature experimental.

---

## Security

| Threat | Defence |
|---|---|
| SQL injection | Every query is a `PreparedStatement`; all SQL lives in the DAOs |
| Password theft | PBKDF2-HMAC-SHA256, 210,000 iterations, 16-byte random salt per user |
| CSRF | 32 random bytes per session, compared in constant time, required on every POST |
| XSS | `HtmlUtil.escapeHtml()` on all user-supplied text |
| Session fixation | The old session is invalidated on login |
| Privilege escalation | Role whitelist on registration |
| IDOR | A doctor may delete only their own screenings |
| Destructive GET | `action=delete` refused on GET everywhere |
| Unauthorised image access | Patient images under `/uploads/` require a logged-in session |
| AI service abuse | API key (constant-time compare), localhost binding, rate limiting |
| Secrets in source | All credentials come from environment variables or `-D` properties |

---

## Known limitations

These are honest gaps in the current version:

- **No build tool.** There is no Maven or Gradle, so builds rely on Eclipse, and
  `.classpath` contains absolute paths from the development machine.
- **No automated test framework.** Java tests are `main()` programs under
  `com.hms.test`; the AI service has 13 checks in `test_ai_service.py`.
- **No connection pool.** Each query opens a fresh `DriverManager` connection, which is
  fine at this scale. HikariCP or a JNDI `DataSource` would be the fix.
- **The model selector is a placeholder.** The segmentation-model dropdown is stored and
  shown on the report, but only the Residual U-Net weights exist, so the choice does not
  change the computation.
- **The DR low-confidence badge is computed but not shown.** `inference.py` computes it,
  but it is not passed through to the report.
- **The dashboard calls DAOs directly from the JSP.** This is the one place the MVC
  layering breaks; a `DashboardServlet` would fix it.
- **Error pages mask errors.** `web.xml` maps 404, 403 and 500 to the login page, so a
  real error can look like a logout. Check the Tomcat console.
- **The AI is not clinically validated.** It uses a single-source cohort (mBRSET), one
  camera model (Phelcom Eyer) and historical rather than prospective labels.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Badge shows "AI Offline" | Service not running, or `/health` reports `degraded` (weights missing) | `curl http://127.0.0.1:5000/health` |
| Every AI request returns 401 | `HMS_AI_API_KEY` differs between Tomcat and Python | Set the identical value in both |
| Every AI request returns 503 | `HMS_AI_API_KEY` not set for Python | Set it in the shell before `python api_server.py` |
| All lists are empty, no error | DB credentials not visible to Tomcat | Look for `[DBConnection] Error` in the Tomcat log |
| `?error=save_failed` after an analysis | `cvd_screenings` is missing columns | Re-run `db/cvd_screenings_schema.sql` (it adds them) |
| Everything redirects to login | No session, or a real error masked by `web.xml` | Check the Tomcat console |
| All servlets 404 after deploy | Running on Tomcat 9 or earlier | Use Tomcat 10.1+ (Jakarta namespace) |
| `ModuleNotFoundError: fastapi` | Old environment | `pip install -r cvd-ai-service/requirements.txt` |
| Report results are all Negative / No DR | The AI response could not be parsed | Look for `[CVDClient] JSON parsing fallback` in the log |

---

## Further documentation

`project-documentation/` contains:

- `PROJECT_ARCHITECTURE.md`
- `SETUP_AND_TROUBLESHOOTING.md`
- `FILE_BY_FILE_GUIDE.md`
- `COMPLETE_PROJECT_REPORT.pdf`

The AI service also has its own `cvd-ai-service/README.md`.
