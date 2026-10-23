# CareConnect Retinal AI: Google Colab GPU Training Workflow

Comprehensive guide and executable assets for training and improving the **CareConnect Retinal Cardiovascular Disease (CVD) AI model** using **Google Colab GPUs** (NVIDIA T4, V100, or A100).

---

## 1. Directory Inventory

This directory (`colab-cvd-training/`) contains all required assets for cloud GPU training:

```
colab-cvd-training/
├── CVD_AUC_Improvement_Colab.ipynb  # Master Google Colab executable Jupyter Notebook
├── README.md                        # Step-by-step operational instructions (this file)
├── requirements-colab.txt           # Pinned dependencies for Google Colab environment
├── COLAB_EXPERIMENT_PLAN.md         # Scientific experiment design & evaluation methodology
└── train_colab.py                   # Standalone Python CLI script for terminal/cloud training
```

---

## 2. Quick-Start Checklist: What Requires Your Action

Follow these 5 simple steps to run your experiments on Google Colab:

### Step 1: Prepare & Upload Your Datasets to Google Drive
From your Windows machine, upload your local datasets to your Google Drive under a dedicated folder: `careconnect_cvd/`.

Recommended Google Drive folder layout:
```
My Drive/
└── careconnect_cvd/
    ├── data/
    │   ├── mbrset/
    │   │   └── images/              # All 4,002 mBRSET fundus JPEG images
    │   ├── splits/
    │   │   ├── train.csv            # 2,783 images (889 patients)
    │   │   ├── val.csv              # 579 images (190 patients)
    │   │   └── test.csv             # 578 images (191 patients)
    │   └── odir/                    # (Optional) For ODIR-5K representation transfer
    │       ├── full_df.csv
    │       └── preprocessed_images/ # 6,392 ODIR fundus images
    └── experiments_output/          # Auto-created by Colab for checkpoints and metrics
```

> [!TIP]
> **Fast Upload Option via Zip:**  
> On Windows, compress `images` into `mbrset_images.zip`. Upload `mbrset_images.zip` to Google Drive, and in Colab run:  
> `!unzip -q /content/drive/MyDrive/careconnect_cvd/data/mbrset/mbrset_images.zip -d /content/drive/MyDrive/careconnect_cvd/data/mbrset/images/`

---

### Step 2: Open the Notebook in Google Colab
1. Open your web browser and navigate to [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select `CVD_AUC_Improvement_Colab.ipynb` from:  
   `C:\Users\vinay\javacode\HospitalManagementSystem Project\colab-cvd-training\CVD_AUC_Improvement_Colab.ipynb`.

---

### Step 3: Select a GPU Hardware Accelerator
1. In the Colab top menu, click **Runtime** $\to$ **Change runtime type**.
2. Under **Hardware accelerator**, select **T4 GPU** (available on free tier) or **A100 GPU** (if on Colab Pro).
3. Click **Save**.

---

### Step 4: Mount Google Drive & Run the Notebook
1. Execute **Section A** to confirm your GPU is active and has VRAM allocated.
2. Execute **Section B** to mount Google Drive (`drive.mount('/content/drive')`).
3. Check the configured folder paths in Section B:
   ```python
   DRIVE_BASE = Path('/content/drive/MyDrive/careconnect_cvd')
   MBRSET_IMAGES_DIR = DRIVE_BASE / 'data' / 'mbrset' / 'images'
   SPLITS_DIR = DRIVE_BASE / 'data' / 'splits'
   ODIR_DIR = DRIVE_BASE / 'data' / 'odir'
   OUTPUT_DIR = DRIVE_BASE / 'experiments_output'
   ```
4. Run through the sections sequentially. Training progress, validation curves, and checkpoints will be saved continuously to your Google Drive, surviving session disconnects.

---

### Step 5: Export Candidate Model Back to Your Windows Project
Once Colab finishes:
1. Navigate in Google Drive to: `careconnect_cvd/experiments_output/candidate_deployment_package/`.
2. Download `candidate_model.pt` and `config_candidate.json` to your local computer.
3. Test locally before replacing production weights (instructions in Section 5 below).

---

## 3. Notebook Structure Overview

| Section | Title | Primary Responsibility |
| :---: | :--- | :--- |
| **Section A** | **GPU Setup & Verification** | Detects CUDA GPU, prints VRAM and driver version, checks PyTorch compatibility. Halts if GPU is not selected. |
| **Section B** | **Dataset Access & Paths** | Mounts Google Drive, verifies image readability, checks file presence, avoids hardcoded Windows paths. |
| **Section C** | **Data & Leakage Audit** | Validates target purity (pure `vascular_disease`), verifies zero patient leakage ($\text{Train} \cap \text{Val} = \emptyset$), checks class distributions. |
| **Section D** | **Model Architecture & DataLoaders** | Defines `CareConnectMultiTaskNet` (EfficientNet-B0 backbone), transforms, and PyTorch datasets. |
| **Section E** | **Controlled GPU Experiments** | Evaluates differential learning rates ($10^{-5}$ vs $10^{-4}$), frozen backbone (linear probing), multi-task focal loss ($\gamma = 2.0$), and conservative medical augmentations. |
| **Section F** | **ODIR-5K Representation Pretraining** | Pretrains EfficientNet-B0 on 8 ODIR-5K ocular classes, extracts encoder weights, and fine-tunes on mBRSET training cohort. |
| **Section G** | **Execution Engine** | Trains the experimental matrix with Cosine Annealing, FP16 mixed precision (`autocast`), and early stopping. |
| **Section H** | **Results Dashboard & Curves** | Compares all experiments in a ranked summary table; plots training/validation loss and patient-level ROC-AUC curves. |
| **Section I** | **Final Test Evaluation & Export** | Evaluates the single best validation-selected model on the held-out test cohort ($N=191$ patients); exports candidate weights and configuration. |

---

## 4. Alternative: Non-Interactive CLI Training via `train_colab.py`

If you prefer running a single script in the Google Colab terminal or on a remote cloud GPU server (AWS EC2, Lambda Labs, RunPod, or local Linux GPU):

```bash
# 1. Install dependencies
pip install -r requirements-colab.txt

# 2. Run all experiments with GPU acceleration
python train_colab.py \
    --mbrset_root "/content/drive/MyDrive/careconnect_cvd/data/mbrset/images" \
    --splits_dir "/content/drive/MyDrive/careconnect_cvd/data/splits" \
    --odir_root "/content/drive/MyDrive/careconnect_cvd/data/odir" \
    --output_root "/content/drive/MyDrive/careconnect_cvd/experiments_output" \
    --epochs 10 \
    --batch_size 32 \
    --experiment all \
    --eval_test
```

### Command Options:
- `--experiment exp1`: Run baseline replication only.
- `--experiment exp3`: Run gradual fine-tuning with differential learning rates.
- `--experiment exp4`: Run multi-task focal loss.
- `--experiment exp7`: Run ODIR-5K transfer learning.
- `--batch_size 16`: Reduce batch size if GPU memory is constrained.

---

## 5. Integrating Candidate Checkpoints into CareConnect HMS

To maintain clinical reliability and prevent regressions, **never overwrite the active production model without local verification**.

Follow this verified procedure:

1. **Copy the Candidate Checkpoint to Local AI Service:**
   Copy `candidate_model.pt` from Google Drive into:
   `C:\Users\vinay\javacode\HospitalManagementSystem Project\cvd-ai-service\models\candidate_model.pt`

2. **Test Locally with the Automated Test Suite:**
   Open PowerShell in the project directory:
   ```powershell
   cd "C:\Users\vinay\javacode\HospitalManagementSystem Project"
   & "C:\Users\vinay\cvd-env\Scripts\python.exe" "cvd-ai-service\test_ai_service.py"
   ```
   Ensure all 13 unit, security, and inference tests pass cleanly.

3. **Deploy Candidate Model:**
   When satisfied with local test results, update `cvd-ai-service/config.json`:
   ```json
   {
     "model": {
       "weights_file": "models/candidate_model.pt"
     },
     "thresholds": {
       "vascular_disease": {
         "value": 0.4996  // Update to the optimal threshold from config_candidate.json
       }
     }
   }
   ```
   The existing production model is preserved as `models/best_model_experiment_b.pt` and `models/best_model_baseline_backup.pt` for instant rollback.

---

## 6. Clinical & Research Ethics Reminder

- **Assistive Screening Only:** Predictions are computational assistive markers, not medical diagnoses.
- **Ocular vs. Systemic Reality:** High accuracy on Diabetic Retinopathy reflects directly visible retinal damage and does **not** prove systemic cardiovascular disease status.
- **Mandatory Physician Review:** All reports generated by CareConnect must be clinically correlated by an attending physician with standard blood pressure measurement, fasting lipid panels, and 12-lead ECG.

---

*End of Colab Training Workflow Documentation.*
