# CareConnect Retinal AI: Final Data & Training Strategy Report

**Document ID:** `ml/reports/FINAL_TRAINING_STRATEGY.md`  
**Phase:** Phase 3 — Data Strategy & Experimental Blueprint  
**Date:** October 18, 2026  
**Authors:** Senior ML Engineer, Computer Vision Researcher, Full-Stack Integration Engineer  
**Status:** Approved for Implementation (Phase 4 Pipeline)

---

## 1. Target Definition & Clinical Ground Truth

### 1.1 Primary Supervised Target: Pure `vascular_disease`
- **Definition:** The primary screening target is strictly defined as `vascular_disease` from the multimodal Brazilian retinal dataset (**mBRSET**).
- **Label Values:**
  - Positive ($Y = 1$): Patient diagnosed with vascular disease (`vascular_disease == 1.0`).
  - Negative ($Y = 0$): Patient without vascular disease (`vascular_disease == 0.0`).
  - Excluded ($Y = -1$): Missing, unrecorded, or NaN entries (`vascular_disease.isna()`).

### 1.2 Separation from Acute Myocardial Infarction (`acute_myocardial_infarction`)
- **Strict Disambiguation:** Under no circumstances shall `vascular_disease` be combined with `acute_myocardial_infarction` into a composite binary target.
- **Audit Grounding:** Forensic cross-tabulation in Phase 2 revealed that 232 image records in `labels_mbrset.csv` had `vascular_disease == 0.0` but `acute_myocardial_infarction == 1.0`. Combining these two distinct diagnostic codes in the prior pipeline contaminated the ground truth, inflated the positive class count from 675 to 853 images, and confused the model's loss landscape.
- **Decision:** `acute_myocardial_infarction` will be retained in metadata for audit and secondary exploratory tasks, but it is strictly excluded from the primary `vascular_disease` loss calculation.

### 1.3 Secondary Multi-Task Targets
1. **Systemic Hypertension (`systemic_hypertension`):** Binary classification ($0/1$). 11 missing records masked out during loss computation.
2. **Diabetic Retinopathy (`final_icdr`):** 5-grade ICDR classification ($0 = \text{No DR}, 1 = \text{Mild}, 2 = \text{Moderate}, 3 = \text{Severe}, 4 = \text{Proliferative}$). Missing grades masked out.

---

## 2. Dataset Reconciliation & Inclusion / Exclusion Criteria

### 2.1 Reconciled Dataset Inventory
Across the 4,002 physically verified images on disk:
- **Total Physical Images on Disk:** 4,002 (1,289 patients)
- **Images with Valid `vascular_disease` (0 or 1):** 3,933 images (1,268 patients)
- **Positive Images (`vascular_disease == 1`):** 675 images (217 patients, prevalence 17.1%)
- **Negative Images (`vascular_disease == 0`):** 3,258 images (1,051 patients, prevalence 82.9%)
- **Excluded Images (NaN `vascular_disease`):** 69 images (21 patients)
- **Excluded Images (Missing from disk):** 1,162 records in metadata CSV where JPEG files are absent from storage.

### 2.2 Formal Inclusion / Exclusion Policy
Every record processed by the pipeline is cataloged in `audit_exclusions.csv` with an explicit reason:

| Code | Reason | Count (Images) | Action |
| :--- | :--- | :---: | :--- |
| `INCL_VALID` | Valid retinal photograph with confirmed `vascular_disease` label | 3,933 | Included in train/val/test splits |
| `EXCL_NO_FILE` | Metadata row references image file not present on disk | 1,162 | Documented in `audit_exclusions.csv`, dropped |
| `EXCL_NO_LABEL`| Image exists on disk, but `vascular_disease` is NaN / unrecorded | 69 | Documented in `audit_exclusions.csv`, dropped |
| `EXCL_NO_PATIENT`| Patient has 0 images on disk | 2 patients | Documented in `audit_exclusions.csv`, dropped |

---

## 3. Split Policy & Patient-Level Leakage Prevention

### 3.1 Patient-Level Partitioning
- **Strict Invariant:** Zero patient leakage across splits ($\text{Train} \cap \text{Val} = \emptyset$, $\text{Train} \cap \text{Test} = \emptyset$, $\text{Val} \cap \text{Test} = \emptyset$). All images belonging to a single patient must reside within the exact same partition.
- **Preservation of Benchmark Split:**
  - The existing patient partitions from `CVD Project/data/splits/` contain 887 training patients, 190 validation patients, and 191 test patients.
  - Zero patient overlap exists between these partitions.
  - **Correction Applied:** We preserve these exact patient partition boundaries to allow direct comparison with the baseline evaluation, but we **replace the flawed composite `CVD` target column with pure `vascular_disease`**.
  
### 3.2 Partition Demographics (Pure `vascular_disease`)
| Partition | Patients (Total) | Positive Patients | Negative Patients | Images (Total) | Positive Images | Negative Images |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train (70%)** | 887 | 158 (17.8%) | 729 (82.2%) | 2,749 | 496 (18.0%) | 2,253 (82.0%) |
| **Validation (15%)**| 190 | 27 (14.2%) | 163 (85.8%) | 591 | 83 (14.0%) | 508 (86.0%) |
| **Held-Out Test (15%)**| 191 | 32 (16.8%) | 159 (83.2%) | 593 | 96 (16.2%) | 497 (83.8%) |
| **Total** | **1,268** | **217 (17.1%)** | **1,051 (82.9%)**| **3,933** | **675 (17.2%)** | **3,258 (82.8%)**|

---

## 4. Multi-Dataset Integration Strategy

### 4.1 BRSET Status (Incomplete Shard)
- **Audit Findings:** 16,266 records exist in `label_brset.csv`, but only 187 images exist on disk (Shard 6 only).
- **Strategy:** Treat BRSET raw images as unavailable for training until shards 001–005 are obtained. No synthetic interpolation or extrapolation shall be performed.

### 4.2 ODIR-5K Status (Ocular Pretraining Candidate)
- **Audit Findings:** 6,392 images fully verified with ocular disease labels (`N, D, G, C, A, H, M, O`). Column `H` is Hypertensive Retinopathy (ocular damage), not systemic cardiovascular disease.
- **Strategy:** ODIR-5K labels must **never** be converted into CVD ground truth. However, ODIR-5K's 6,392 diverse retinal fundus images provide an ideal domain for **retinal representation pretraining** (domain-specific feature extraction) before fine-tuning on mBRSET.

---

## 5. Clinical Feature Fusion Review & Inference Feasibility

### 5.1 Tabular Features in mBRSET
mBRSET contains 15 clinical columns: `age`, `sex`, `dm_time`, `insulin`, `insulin_time`, `oraltreatment_dm`, `systemic_hypertension`, `smoking`, `obesity`, `alcohol_consumption`, `nephropathy`, `neuropathy`, `diabetic_foot`, `educational_level`, `insurance`.

### 5.2 Missingness Analysis
- `age` and `sex`: 0.0% missing (complete).
- `dm_time`, `insulin`, `oraltreatment_dm`, `smoking`, `obesity`, `alcohol_consumption`, `nephropathy`, `neuropathy`: 0.9% to 2.1% missing.
- `insulin_time`: 80.3% missing (unusable).

### 5.3 Leakage Risk Analysis
- `systemic_hypertension` is both an input candidate and a multi-task prediction target. Using it as a tabular input feature to predict `vascular_disease` would create a circular dependency and target leakage if hypertension is also a model output. It must be excluded from input features.

### 5.4 Inference-Time Reality in CareConnect HMS
- In the CareConnect HMS web application (`new-screening.jsp`), clinicians upload a retinal image for an existing hospital patient.
- The `patients` database table stores: `patient_id`, `name`, `age`, `gender`, `phone`, `address`.
- The HMS does **not** routinely store or collect `dm_time`, `insulin_time`, `educational_level`, or `oraltreatment_dm`.
- **Architectural Requirement:**
  1. The primary production model **must be fully functional with image-only input** (retinal fundus scan).
  2. A secondary multi-modal model may accept `age` and `gender` (features always available from the HMS patient record).
  3. Full 12-feature clinical fusion will be maintained as an experimental research benchmark, but not as a hard requirement for HMS deployment.

---

## 6. Experimental Matrix

| Experiment | Backbone | Input Modality | Target | Loss & Optimization | Training Scope |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Exp A: Baseline Replication** | EfficientNet-B0 | Image only ($224 \times 224$) | CVD (Composite), HT, DR | BCE (pos_weight=3.59), 5 epochs | Evaluated on frozen test split |
| **Exp B1: Supervised Image Baseline (Corrected Target)** | EfficientNet-B0 | Image only ($224 \times 224$) | Pure `vascular_disease` | Normalized balanced BCE, Cosine decay, 25 epochs | mBRSET train set only |
| **Exp B2: Supervised Multi-Task (Balanced)** | EfficientNet-B0 | Image only ($224 \times 224$) | Pure `vascular_disease`, HT, DR | Multi-task loss with calibrated task weights ($1.0, 0.5, 0.5$) | mBRSET train set only |
| **Exp C: ODIR-5K Pretraining + mBRSET Fine-Tuning** | EfficientNet-B0 | Image only ($224 \times 224$) | Pretrain: ODIR ocular heads -> Fine-tune: mBRSET `vascular_disease` | Two-stage transfer learning | ODIR-5K -> mBRSET |
| **Exp D: HMS-Feasible Multi-Modal Fusion** | EfficientNet-B0 + MLP | Image + (`age`, `gender`) | Pure `vascular_disease`, HT, DR | Joint image-tabular embedding | mBRSET train set |

---

## 7. Rigorous Evaluation Protocol

1. **Held-Out Test Set Freezing:**
   - The test set ($N = 191$ patients, 593 images) remains strictly held-out. It shall never be used for gradient updates, hyperparameter search, or threshold tuning.
2. **Threshold Optimization:**
   - All decision thresholds are optimized strictly on the **Validation set** ($N = 190$ patients, 591 images) using F1-score maximization or cost-sensitive clinical bounds, then frozen before test evaluation.
3. **Mandatory Reporting Metrics:**
   - Patient-level ROC-AUC with 95% Bootstrap Confidence Intervals ($B = 1,000$).
   - Patient-level PR-AUC with 95% Bootstrap Confidence Intervals.
   - Sensitivity (Recall) and Specificity.
   - Precision and F1-score.
   - Brier Score (calibration measure).
   - Full confusion matrix (`TP, FP, TN, FN`).
   - ROC curves and Precision-Recall curves.

---
*End of Strategy Report. Approved for Phase 4 implementation.*
