# Retinal Fundus Multi-Task Research Application

A lightweight, self-contained research application for multi-task assessment of **Systemic Hypertension (HT)**, **Cardiovascular Disease (CVD)**, and **Diabetic Retinopathy (DR)** from a single retinal fundus photograph.

> **IMPORTANT CLINICAL & RESEARCH NOTICE**  
> - **Research Prototype Only**: Predictions are model-generated estimates intended solely for research and methodology demonstration. This tool is **NOT** a certified medical device and must **NOT** be used for clinical diagnosis, patient management, or medical decision-making.  
> - **Diabetes Disclaimer**: **Diabetes status is NOT predicted by this system.** Diabetic Retinopathy (DR) grading reflects microvascular retinal findings, not a systemic diabetes diagnosis.  
> - **CVD Low Reliability**: Image-only cardiovascular disease prediction yields an internal validation ROC-AUC near chance (~0.55–0.60). Fundus images alone without systemic biomarkers have limited discriminatory power for acute CVD events.

---

## 1. Quick Start (Setup in 4 Commands)

Open a terminal (PowerShell, Command Prompt, or bash) in the project directory:

```bash
# 1. Create a virtual environment (Python 3.10 - 3.12 recommended)
python -m venv venv

# 2. Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
python app.py
```

Alternatively, on Windows you can double-click `run_app.bat`, or on Linux/macOS execute `bash run_app.sh`.

Once launched, open your web browser at:
```
http://127.0.0.1:7860
```

---

## 2. Directory Structure

```
CVD_Retinal_App/
│
├── app.py                     # Gradio UI application entry point
├── inference.py               # Self-contained model architecture, preprocessing & prediction
├── config.json                # Model config, image preprocessing parameters & decision thresholds
├── requirements.txt           # Pinned dependencies
├── run_app.bat                # Windows quick-launch script
├── run_app.sh                 # Linux/macOS quick-launch script
├── README.md                  # This documentation
│
├── models/
│   ├── best_model.pt          # Trained PyTorch weights (MultiTaskEfficientNetB0)
│   └── model_card.json        # Model details, provenance, metrics & ethical considerations
│
└── evaluation/
    ├── metrics.json           # Held-out patient-split test set metrics & sanity check records
    └── test_evaluation_curves.png # ROC and Precision-Recall curves from test evaluation
```

---

## 3. Understanding the Outputs

### A. Systemic Hypertension (HT)
- **Output**: Predicted probability ($[0.0, 1.0]$) and binary prediction (`Positive` / `Negative`).
- **Threshold**: `0.5165` (derived by maximizing Youden's $J$ statistic on validation data).
- **Interpretation**: Indicates the model's assessed likelihood of systemic hypertension based on retinal arteriolar narrowing and microvascular changes.

### B. Cardiovascular Disease (CVD)
- **Output**: Predicted probability ($[0.0, 1.0]$), binary prediction (`Positive` / `Negative`), and a permanent **Low reliability** indicator.
- **Threshold**: `0.3238` (derived by maximizing Youden's $J$ statistic on validation data).
- **Reliability Note**: Internal validation and held-out test ROC-AUC are ~0.55–0.60. Retinal image features alone without clinical metadata (blood pressure, lipid panel, smoking status) are insufficient for reliable CVD prediction.

### C. Diabetic Retinopathy (DR / ICDR Grade)
- **Output**: Predicted International Clinical Diabetic Retinopathy (ICDR) grade (0 to 4) and Top-Class Confidence.
- **Grades**:
  - `Grade 0`: No apparent retinopathy (No DR)
  - `Grade 1`: Mild non-proliferative DR (Microaneurysms only)
  - `Grade 2`: Moderate non-proliferative DR
  - `Grade 3`: Severe non-proliferative DR
  - `Grade 4`: Proliferative diabetic retinopathy (PDR)
- **Confidence Badges**: A **Low confidence** badge is shown if the top-class probability is below 50% or if the difference between the top two class probabilities is less than 15%.
- **Grade Distribution**: A 5-bar visualization displaying the exact probability distribution across all 5 ICDR classes.

---

## 4. Model Architecture & Training Summary

- **Backbone**: `EfficientNet-B0` (3-channel RGB fundus input, resized to $224 \times 224$, normalized using ImageNet mean and std).
- **Multi-Task Heads**:
  - `head_ht`: Linear layer $(1280 \to 1)$ with sigmoid activation for systemic hypertension.
  - `head_cvd`: Linear layer $(1280 \to 1)$ with sigmoid activation for cardiovascular disease.
  - `head_dr`: Linear layer $(1280 \to 5)$ with softmax activation for ICDR grade.
- **Training Strategy**: Multi-task learning with composite loss:
  $$\mathcal{L} = \mathcal{L}_{\text{BCE, HT}} + 2.0 \cdot \mathcal{L}_{\text{BCE, CVD}} + \mathcal{L}_{\text{CE, DR}}$$
- **Dataset**: Trained on the mBRSET (Multimodal Brazilian Retinal Fundus Study) dataset using patient-level stratified splitting to ensure zero patient leakage across train, validation, and test sets.

---

## 5. Performance Summary (Held-Out Test Set)

Evaluated on the patient-stratified held-out test partition ($n = 328$ patients, $n = 649$ images):

| Condition | ROC-AUC (95% CI) | PR-AUC (95% CI) | Sensitivity | Specificity | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Systemic Hypertension** | **0.672** (0.631–0.713) | **0.781** (0.741–0.819) | 0.655 | 0.596 | 0.697 |
| **Cardiovascular Disease** | **0.556** (0.505–0.608) | **0.407** (0.347–0.472) | 0.498 | 0.627 | 0.428 |
| **Diabetic Retinopathy** | N/A (5 classes) | N/A (5 classes) | Weighted F1: **0.767** | — | Accuracy: **78.4%** |

*Full metrics and confusion matrix data are accessible directly in the "Model Evaluation" tab of the web application.*

---

## 6. Data-Use and Distribution Policy

- **No Dataset Included**: In compliance with PhysioNet Credentialed Health Data Use Agreements and ODIR data licensing, no raw fundus images, patient records, clinical CSVs, or intermediate cache files are included in this distribution.
- **Model Weights**: Only the trained weight file (`models/best_model.pt`) and evaluation summaries are provided.
