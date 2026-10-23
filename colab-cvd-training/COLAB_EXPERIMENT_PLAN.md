# CareConnect Retinal AI: Google Colab GPU Research Experiment Plan

**Document ID:** `colab-cvd-training/COLAB_EXPERIMENT_PLAN.md`  
**System:** CareConnect Hospital Management System & Retinal Screening AI  
**Author:** AI Research & Computer Vision Team  
**Date:** October 2026  
**Status:** Approved for Google Colab GPU Execution  

---

## 1. Executive Summary & Clinical Context

In the CareConnect Hospital Management System, the retinal screening microservice assists clinicians by evaluating multi-task deep learning predictions on retinal fundus photographs. 

In our Phase 6 held-out test evaluation ($N = 191$ patients, $578$ retinal images):
- **Diabetic Retinopathy (DR)** achieved **76.99% test accuracy** and **0.6918 Weighted F1**, demonstrating robust capability to detect visible ocular microvascular pathology (microaneurysms, blot hemorrhages, hard exudates).
- **Vascular Disease (CVD)** achieved a patient-level test **ROC-AUC of 0.5202** (95% CI: `[0.3936, 0.6416]`), indicating near-chance discrimination when attempting to predict systemic cardiovascular disease from mobile smartphone fundus photographs alone.

### Core Scientific Questions
1. Can architectural and optimization refinements (gradual backbone unfreezing, differential learning rates, focal loss, and cosine learning rate schedules) improve discrimination for `vascular_disease` without compromising Diabetic Retinopathy performance?
2. Does pretraining an EfficientNet-B0 encoder on diverse retinal ocular diseases (**ODIR-5K**, $N = 6,392$ fundus images) provide superior domain-specific representations compared to generic ImageNet weights when fine-tuned on mBRSET?
3. What is the empirical upper bound of retinal image-only discrimination for systemic vascular disease, and how much can be gained by integrating non-invasive patient clinical priors (age and sex)?

---

## 2. Dataset Forensic Audit & Baseline Inventory

### 2.1 mBRSET (Primary Screening Dataset)
- **Origin:** Mobile Brazilian Retinal Dataset v1.0, captured using handheld smartphone attachments (Phelcom Eyer) on un-dilated pupils in primary healthcare centers in Brazil.
- **Physical Images on Disk:** 4,002 images from 1,289 patients.
- **Valid `vascular_disease` Records:** 3,933 images from 1,268 patients (675 positive, 3,258 negative; prevalence = 17.1%).
- **Primary Target Definition:** Strictly pure `vascular_disease` ($0$ or $1$).
  > **Target Purity Rule:** Conflating `vascular_disease` with `acute_myocardial_infarction` (AMI) is strictly prohibited. Forensic audit revealed 232 cases in mBRSET where `vascular_disease == 0.0` but `acute_myocardial_infarction == 1.0`. Merging them contaminates the ground truth.
- **Patient-Level Partitions:**
  - **Train (70%):** 889 patients, 2,783 images (474 positive, 2,309 negative).
  - **Validation (15%):** 190 patients, 579 images (106 positive, 473 negative).
  - **Held-Out Test (15%):** 191 patients, 578 images (95 positive, 483 negative; 32 positive patients).

### 2.2 ODIR-5K (Ocular Disease Transfer Learning Dataset)
- **Origin:** Ocular Disease Intelligent Recognition (ODIR-5K), Peking University.
- **Physical Images on Disk:** 6,392 preprocessed color fundus images ($N=6,392$).
- **Labels Available:** Multi-label binary classification across 8 ocular conditions:
  - `N`: Normal
  - `D`: Diabetes / Diabetic Retinopathy
  - `G`: Glaucoma
  - `C`: Cataract
  - `A`: Age-related Macular Degeneration (AMD)
  - `H`: Hypertensive Retinopathy (ocular damage)
  - `M`: Pathological Myopia
  - `O`: Other diseases / abnormalities
- **Boundary Invariant:** ODIR ocular labels must **never** be relabeled or combined into a CVD ground truth. ODIR-5K is used strictly for **retinal representation pretraining**.

---

## 3. Strict Methodological Safeguards

To ensure that results are scientifically valid and trustworthy:

1. **Held-Out Test Set Freezing:**
   - The test set ($N=191$ patients) is **strictly frozen**. It will **never** be used for gradient updates, hyperparameter selection, epoch selection, or threshold tuning.
   - Experiments will be evaluated and selected strictly based on **Validation ROC-AUC**.
   - Only the final selected candidate model will be evaluated once on the test set for final reporting.
2. **Patient-Level Zero-Leakage Guarantee:**
   - All partitions are grouped strictly by `patient` ID. No patient or eye scan appears across both training and validation/test splits ($\text{Train} \cap \text{Val} = \emptyset$).
3. **Validation-Optimized Decision Thresholds:**
   - Classification thresholds are optimized solely on the validation partition using **Youden's $J$ statistic** ($J = \text{Sensitivity} + \text{Specificity} - 1$) and frozen before test evaluation.
4. **Patient-Level Metric Aggregation:**
   - Predictions from multiple images per patient (e.g. left and right eye) are aggregated to a patient-level probability using mean pooling before computing ROC-AUC and PR-AUC.
5. **Bootstrap 95% Confidence Intervals:**
   - Primary metrics are reported with 95% bootstrap confidence intervals ($B = 1,000$ resamples) on patient-level predictions.

---

## 4. Controlled Experiment Matrix

We design 8 controlled experiments to systematically test each optimization component:

| Exp ID | Experiment Name | Backbone Initialization | Training Strategy | Loss Function | Learning Rate & Schedule | Primary Hypothesis Tested |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Exp 1** | **Baseline Replication** | ImageNet (Pretrained) | Full fine-tune from epoch 1 | Balanced Multi-Task BCE ($w_{\text{pos}}=4.871$) | $1 \times 10^{-4}$ (AdamW), StepLR | Establish exact reproduction of the deployed baseline on Colab GPU. |
| **Exp 2** | **Frozen Backbone (Linear Probing)** | ImageNet (Pretrained) | Freeze EfficientNet-B0 features; train task heads only | Balanced Multi-Task BCE ($w_{\text{pos}}=4.871$) | $3 \times 10^{-4}$ (AdamW), Cosine Annealing | Test if freezing features prevents overfitting on small medical datasets. |
| **Exp 3** | **Differential LR / Gradual Unfreezing** | ImageNet (Pretrained) | 2-stage unfreezing: Stage 1 heads only (2 epochs); Stage 2 backbone at $10^{-5}$ and heads at $10^{-4}$ | Balanced Multi-Task BCE ($w_{\text{pos}}=4.871$) | Differential LRs ($10^{-5} / 10^{-4}$), Cosine Annealing | Test if gentle fine-tuning preserves general visual priors while adapting task heads. |
| **Exp 4** | **Focal Loss vs. Weighted BCE** | ImageNet (Pretrained) | Differential fine-tuning | Multi-Task Focal Loss ($\gamma = 2.0$, $\alpha$-balanced) | Differential LRs, Cosine Annealing | Test if down-weighting easy negative background fundus pixels sharpens gradient signal on subtle microaneurysms. |
| **Exp 5** | **Learning Rate Grid ($1\text{e-}5$ vs $3\text{e-}5$)** | ImageNet (Pretrained) | Differential fine-tuning | Best loss from Exp 4 | Compare $1 \times 10^{-5}$ vs $3 \times 10^{-5}$ backbone rate | Find the optimal learning rate basin for convergence without catastrophic forgetting. |
| **Exp 6** | **Conservative Retinal Augmentation & Resolution** | ImageNet (Pretrained) | Differential fine-tuning + enhanced transforms | Best loss from Exp 4 | Best LR from Exp 5 | Test if CLAHE contrast enhancement and resolution ($256 \times 256$) improve microvascular feature extraction. |
| **Exp 7** | **ODIR-5K Transfer Learning** | **ODIR-5K Ocular Pretrained** | Pretrain 8-head ocular classifier on ODIR $\to$ Transfer encoder $\to$ Fine-tune on mBRSET | Best loss from Exp 4 | Differential LRs, Cosine Annealing | Test if domain-specific retinal feature representations outperform generic ImageNet weights. |
| **Exp 8** | **Multimodal Fusion Baseline** | Best vision backbone + MLP | Late-fusion: retinal embedding + normalized Age & Sex | Best loss from Exp 4 | Differential LRs, Cosine Annealing | Measure the discriminative gain when combining fundus pixels with demographic priors available in HMS. |

---

## 5. Mathematical Formulations

### 5.1 Multi-Task Loss with Class Imbalance Weighting
For each sample $i$, the total loss is a weighted sum over the three tasks:
$$\mathcal{L}_{\text{total}} = \lambda_{\text{VD}} \mathcal{L}_{\text{VD}} + \lambda_{\text{HT}} \mathcal{L}_{\text{HT}} + \lambda_{\text{DR}} \mathcal{L}_{\text{DR}}$$
Where default task weights are $\lambda_{\text{VD}} = 1.0$, $\lambda_{\text{HT}} = 0.5$, $\lambda_{\text{DR}} = 0.5$.

For binary vascular disease ($y_i \in \{0, 1\}$), the weighted binary cross-entropy is:
$$\mathcal{L}_{\text{VD}} = - \left[ w_{\text{pos}} y_i \log \sigma(z_i) + (1 - y_i) \log (1 - \sigma(z_i)) \right]$$
Where $w_{\text{pos}} = \frac{N_{\text{neg}}}{N_{\text{pos}}} = \frac{2309}{474} \approx 4.871$ (calculated strictly from the training partition).

### 5.2 Focal Loss Formulation
To focus training on hard, borderline vascular examples and prevent easy negatives from dominating the gradient:
$$\text{FL}(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$
Where:
- $p_t = \sigma(z)$ if $y = 1$, else $1 - \sigma(z)$.
- Focusing parameter $\gamma = 2.0$.
- Class balancing parameter $\alpha = \frac{N_{\text{neg}}}{N_{\text{pos}} + N_{\text{neg}}}$.

### 5.3 ODIR-5K Multi-Label Pretraining Objective
For the 8-class ocular disease recognition on ODIR-5K:
$$\mathcal{L}_{\text{ODIR}} = \frac{1}{8} \sum_{c=1}^{8} \text{BCEWithLogits}(z_c, y_c)$$
Evaluated across Normal, Diabetes, Glaucoma, Cataract, AMD, Hypertension Retinopathy, Myopia, and Other.

---

## 6. Model Selection & Export Criteria

1. **Validation Criterion:**
   - The primary selection metric across all experiments is **Validation Patient-Level ROC-AUC** for `vascular_disease`.
   - Secondary selection guardrail: Validation Diabetic Retinopathy accuracy must not degrade by more than 3.0 percentage points compared to baseline (maintaining ocular clinical utility).
2. **Early Stopping:**
   - Patience = 4 epochs without improvement in validation ROC-AUC.
   - The model checkpoint with the highest validation ROC-AUC is restored.
3. **Candidate Export Format:**
   - The best checkpoint will be exported as `best_candidate_model.pt` accompanied by an updated `config.json` specifying:
     - Exact state dict keys (`head_vd`, `head_ht`, `head_dr`).
     - Frozen validation decision thresholds ($t_{\text{VD}}, t_{\text{HT}}$).
     - Full evaluation report and model card.
   - The candidate model is exported separately to persistent Google Drive storage. It will **not** overwrite the production `cvd-ai-service/models/best_model.pt` automatically.

---

## 7. Results Recording Template

When running experiments in Google Colab, record the results in this standardized table:

| Exp ID | Experiment Description | Validation VD ROC-AUC | Validation VD PR-AUC | Validation DR Accuracy | Held-Out Test VD ROC-AUC | 95% Bootstrap CI | Test Sensitivity | Test Specificity | Test DR Accuracy |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Exp 1** | Baseline Replication | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* |
| **Exp 2** | Frozen Backbone (Linear Probing) | *[Colab]* | *[Colab]* | *[Colab]* | — | — | — | — | — |
| **Exp 3** | Gradual Unfreezing / Diff LR | *[Colab]* | *[Colab]* | *[Colab]* | — | — | — | — | — |
| **Exp 4** | Focal Loss ($\gamma = 2.0$) | *[Colab]* | *[Colab]* | *[Colab]* | — | — | — | — | — |
| **Exp 5** | LR Grid ($1\text{e-}5$ vs $3\text{e-}5$) | *[Colab]* | *[Colab]* | *[Colab]* | — | — | — | — | — |
| **Exp 6** | Medical Augmentation + Res 256 | *[Colab]* | *[Colab]* | *[Colab]* | — | — | — | — | — |
| **Exp 7** | ODIR-5K Pretraining $\to$ mBRSET | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* |
| **Exp 8** | Multimodal Demographics Prior | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* | *[Colab]* |

*(Note: Dashes `—` indicate experiments not selected for final test set evaluation, preserving test set freezing).*

---

*End of Experiment Plan.*
