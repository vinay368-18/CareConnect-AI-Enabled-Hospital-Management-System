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

The system is made of three processes. You start it with **one command**
(`.\run.bat`): Tomcat runs the web application, and the web application starts the
AI service itself and stops it when Tomcat stops. MySQL runs as its usual Windows
service.

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

**Why the AI is a separate process:** the model ecosystem (PyTorch, torchvision,
Pillow, OpenCV) is Python. The checkpoints (about 48 MB and 32 MB) load once at startup
and stay in memory. The hospital app keeps working when the AI service is down; only
new screenings are blocked, behind an "AI Microservice Offline" message. The model
can also be retrained and restarted without redeploying the web app.

**How they run as one application:** `AiServiceLauncher`, a `ServletContextListener`
registered in `web.xml`, runs `python api_server.py` when the web application
starts. It does not hold up Tomcat's startup: the models load in the background
(about 10–30 seconds), and the CVD pages show "AI offline" until the service reports
healthy. When the web application or Tomcat stops, the launcher stops the AI
service. If an AI service is already running on the configured address, the launcher
uses it and leaves it alone.

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
  util/         AppConfig (settings lookup), DBConnection, PasswordUtil, CSRFUtil,
                HtmlUtil, AdminProvisioner
src/main/webapp/
  *.jsp         22 pages (login, dashboard, patients, doctors, appointments,
                billing, reports, CVD screening list / new screening / report,
                error page, ...)
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
run.bat                   ONE COMMAND: build, deploy and run everything on Tomcat
scripts/
  setup-config.bat          one-time: writes the local settings file
  run-web.ps1               what run.bat runs (scripts\run-web.bat is the same)
  run-ai.bat                optional: start the AI service on its own
.env.example              template for every setting
start_cvd_ai_service.bat  optional: same as scripts\run-ai.bat
```

---

## Getting started

**Quick start** (after the one-time steps 1–3 below):

```bat
.\run.bat
```

Then open `http://localhost:8080/HospitalManagementSystem/`. One window runs
everything; **Ctrl+C** stops Tomcat and the AI service together.

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

### 3. Configure the settings

Nothing is hard-coded. The easiest way is to run the one-time setup script, which
asks for your MySQL username and password and generates a fresh API key:

```bat
scripts\setup-config.bat
```

It writes `%USERPROFILE%\.careconnect\careconnect.env`, **outside the project
folder**, so credentials can never be committed. The web app and the AI service
both read this file, so they always share the same API key, however Tomcat is
started (terminal, Eclipse or the VS Code server connector). You can also write the
file by hand: it uses the same `KEY=VALUE` format as `.env.example`.

Each setting is resolved in this order, and the first match wins:

1. an environment variable (for example `HMS_DB_USER`)
2. a Java system property (for example `-Dhms.db.user=...`), for the web app only
3. the `careconnect.env` file, looked for at `HMS_CONFIG_FILE` if set, then
   `<tomcat>/conf/careconnect.env` (web app only), then
   `%USERPROFILE%\.careconnect\careconnect.env`

The settings:

| Variable | Used by | Required | Purpose |
|---|---|---|---|
| `HMS_DB_USER` | Java | **Yes** | MySQL username |
| `HMS_DB_PASSWORD` | Java | **Yes** | MySQL password (an empty value is accepted for a passwordless local MySQL) |
| `HMS_AI_API_KEY` | Java **and** Python | **Yes** | Shared secret. **It must be the same in both processes** |
| `HMS_DB_URL` | Java | No | Defaults to `jdbc:mysql://localhost:3306/hospital` |
| `HMS_AI_API_URL` | Java | No | Defaults to `http://127.0.0.1:5000` |
| `HMS_CORS_ORIGINS` | Python | No | Defaults to `http://localhost:8080,http://127.0.0.1:8080` |
| `HMS_AI_SERVICE_DIR` | Java | No | Folder containing `api_server.py`. `.\run.bat` fills this in |
| `HMS_AI_PYTHON` | Java | No | Python used for the AI service. `.\run.bat` fills this in |
| `HMS_AI_AUTOSTART` | Java | No | `false` stops the web app from starting the AI service. Default `true` |

The equivalent Java system properties are `hms.db.url`, `hms.db.user`,
`hms.db.password`, `hms.ai.api.url`, `hms.ai.api.key`, `hms.ai.service.dir`,
`hms.ai.python` and `hms.ai.autostart`. The AI service listens on the port in
`HMS_AI_API_URL`, so the two always agree.

> **Why a file?** A variable set in one terminal is invisible to a Tomcat started
> from Eclipse, from the VS Code server connector or as a Windows service. The
> connector also launches Java directly, so `bin\setenv.bat` is not read either. The
> config file works in every case. If you see `Database credentials not configured`
> in the Tomcat log, the file is missing or in the wrong place; the message lists the
> exact paths that were searched.

To write the file by hand, generate an API key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run everything

From the project folder (Command Prompt, PowerShell or the VS Code terminal):

```bat
.\run.bat
```

In one window, it:

1. checks the settings file, and runs the one-time setup if there is none
2. finds the AI service's Python (`cvd-ai-service\.venv`, then `%USERPROFILE%\cvd-env`,
   otherwise it creates `cvd-ai-service\.venv`) and installs any missing packages
   from `requirements.txt`. The first install downloads PyTorch and can take several
   minutes; later runs skip it
3. compiles the Java sources into `build\classes`
4. copies the app into `<tomcat>\webapps\HospitalManagementSystem`
5. starts Tomcat. The web app then starts the AI service, whose log appears in the
   same window

Wait for these lines:

```
INFO: Server startup in [...] milliseconds
[AI Service] Ready at http://127.0.0.1:5000
```

Then open `http://localhost:8080/HospitalManagementSystem/`. **Ctrl+C** stops
everything.

`.\run.bat` finds Tomcat through `CATALINA_HOME`, or by searching your user folder for
`apache-tomcat-10.*`. To point at it explicitly:
`.\run.bat -TomcatHome "C:\path\to\apache-tomcat-10.1.57"`. It refuses to start a
second Tomcat when port 8080 is already taken.

**Using the VS Code server connector or Eclipse instead:** Tomcat started from those
also starts the AI service, because the web app does it. Run `.\run.bat -NoStart` once
first, which sets everything up and deploys without starting Tomcat. Then start the
server from the IDE as usual.

**Running the AI service on its own (optional):** set `HMS_AI_AUTOSTART=false` in
`careconnect.env`, then use `scripts\run-ai.bat`. To check the service directly:

```bash
curl http://127.0.0.1:5000/health
# expect "status":"healthy", "model_loaded":true, "vessel_model_loaded":true
```

A `"degraded"` status means the prediction model did not load, which usually means
`models/best_model.pt` is missing.

> The AI service is `api_server.py`, **not** `app.py`. `app.py` (`run_app.bat`) is
> the separate Gradio research UI and does not serve the web application.

### 5. Create the first admin account

There is no public sign-up, and registering staff requires an existing admin, so the
first account is created from the command line. Run `.\run.bat` once first (it
produces `build\classes`). The tool reads the database settings from
`careconnect.env`, so no extra setup is needed:

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

### 6. Check it end to end

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
| `/LogoutServlet` | Sign out | public |
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
| Secrets in source | Credentials come from environment variables, `-D` properties or a settings file outside the project |
| Information leakage | 403, 404 and 500 show a plain error page; no stack traces reach the browser |

---

## Known limitations

These are honest gaps in the current version:

- **No build tool.** There is no Maven or Gradle; `.\run.bat` and Eclipse stand in for
  one.
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
- **The AI is not clinically validated.** It uses a single-source cohort (mBRSET), one
  camera model (Phelcom Eyer) and historical rather than prospective labels.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Login page says "Sign-in is unavailable … cannot reach its database" | Settings not found, wrong password, or MySQL not running | Run `scripts\setup-config.bat`; read the `[DBConnection]` line in the Tomcat log, which lists the paths searched |
| Badge shows "AI Offline" | Service not running, or `/health` reports `degraded` (weights missing) | `curl http://127.0.0.1:5000/health` |
| Every AI request returns 401 | An environment variable overrides the shared key on one side only | Remove the stray `HMS_AI_API_KEY` variable, or set it identically for both |
| Every AI request returns 503 | No API key configured for the Python service | Run `scripts\setup-config.bat`, then `.\run.bat` again |
| `[AI Service] Exited early with code …` | Missing Python packages, port 5000 in use, or missing model files | Read the Python lines just above it; `.\run.bat` reinstalls missing packages |
| `[AI Service] Not started: could not find the cvd-ai-service folder` | Tomcat was started without running `.\run.bat` first | Run `.\run.bat -NoStart` once; it records the folder in `careconnect.env` |
| `ERROR: Port 8080 is already in use` | Another Tomcat is running, for example the VS Code connector's | Stop it, or use `.\run.bat -NoStart` to redeploy into it |
| `?error=save_failed` after an analysis | `cvd_screenings` is missing columns | Re-run `db/cvd_screenings_schema.sql` (it adds them) |
| "Something went wrong" (500) page | An unexpected server error | The cause is in the Tomcat console or `logs\catalina.*.log` |
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
