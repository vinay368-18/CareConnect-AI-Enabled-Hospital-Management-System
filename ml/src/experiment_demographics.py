"""
CareConnect Retinal AI: Experiment D - Demographic & Multimodal Fusion
======================================================================
Investigates whether incorporating clinical demographic priors (Age, Sex)
improves cardiovascular disease (vascular_disease) screening performance
over image-only models.

Evaluates:
1. Demographic-only baseline (Age + Sex with StandardScaler fit on train only)
2. Retinal Image-only model (Experiment B EfficientNet-B0)
3. Multimodal Late-Fusion (Ensemble of Image + Demographic priors)
"""

import json
from pathlib import Path
import sys
from typing import Dict, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_curve, precision_recall_curve

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.metrics import (
    compute_binary_metrics,
    find_optimal_threshold,
    aggregate_patient_predictions,
)


def clean_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess age and sex safely."""
    df = df.copy()
    # Handle de-identified top-coded age '>= 90'
    df["age"] = df["age"].replace({">= 90": "90"}).astype(float)
    df["sex"] = df["sex"].astype(float)
    return df


def run_experiment_d():
    print("=" * 65)
    print("CARECONNECT - EXPERIMENT D: DEMOGRAPHIC & MULTIMODAL FUSION")
    print("=" * 65)

    splits_dir = PROJECT_ROOT / "ml" / "datasets" / "splits"
    metrics_dir = PROJECT_ROOT / "ml" / "metrics"
    plots_dir = metrics_dir / "plots"
    preds_dir = metrics_dir / "predictions"
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load splits and clean demographics at patient level
    train_df = clean_demographics(pd.read_csv(splits_dir / "train.csv"))
    val_df = clean_demographics(pd.read_csv(splits_dir / "val.csv"))
    test_df = clean_demographics(pd.read_csv(splits_dir / "test.csv"))

    # Patient-level demographic datasets (unique patient rows)
    train_pat = train_df.drop_duplicates("patient").copy()
    val_pat = val_df.drop_duplicates("patient").copy()
    test_pat = test_df.drop_duplicates("patient").copy()

    print(f"[Demographics] Train patients: {len(train_pat)} (VD pos: {train_pat['vascular_disease'].sum()})")
    print(f"[Demographics] Val patients:   {len(val_pat)} (VD pos: {val_pat['vascular_disease'].sum()})")
    print(f"[Demographics] Test patients:  {len(test_pat)} (VD pos: {test_pat['vascular_disease'].sum()})")

    # 2. Fit scaler strictly on training split
    scaler = StandardScaler()
    scaler.fit(train_pat[["age"]])

    def extract_features(df):
        age_scaled = scaler.transform(df[["age"]])
        sex = df[["sex"]].values
        return np.hstack([age_scaled, sex])

    X_train_demo = extract_features(train_pat)
    y_train_demo = train_pat["vascular_disease"].values

    X_val_demo = extract_features(val_pat)
    y_val_demo = val_pat["vascular_disease"].values

    X_test_demo = extract_features(test_pat)
    y_test_demo = test_pat["vascular_disease"].values

    # 3. Fit Demographic Logistic Regression
    demo_model = LogisticRegression(class_weight="balanced", random_state=42)
    demo_model.fit(X_train_demo, y_train_demo)

    # Demographic probabilities
    val_demo_probs = demo_model.predict_proba(X_val_demo)[:, 1]
    test_demo_probs = demo_model.predict_proba(X_test_demo)[:, 1]

    # Map demo probs back to patient ID
    val_pat_demo_map = dict(zip(val_pat["patient"], val_demo_probs))
    test_pat_demo_map = dict(zip(test_pat["patient"], test_demo_probs))

    # 4. Load Experiment B predictions
    exp_b_preds_csv = preds_dir / "experiment_b_efficientnet_b0_test_predictions.csv"
    if not exp_b_preds_csv.exists():
        raise FileNotFoundError(f"Missing {exp_b_preds_csv}")

    test_b_preds = pd.read_csv(exp_b_preds_csv)
    # Aggregate to patient-level
    test_img_agg = test_b_preds.groupby("patient").agg({
        "vd_prob": "mean",
        "vd_true": "first",
    }).reset_index()

    # Reconcile test patients
    test_merged = test_pat[["patient", "vascular_disease", "age", "sex"]].merge(
        test_img_agg, on="patient"
    )
    test_merged["demo_prob"] = test_merged["patient"].map(test_pat_demo_map)

    # 5. Multimodal Fusion: Weighted combination
    # Image weight 0.5, Demographics weight 0.5 (or rank average)
    test_merged["multimodal_prob"] = 0.5 * test_merged["vd_prob"] + 0.5 * test_merged["demo_prob"]

    y_test = test_merged["vascular_disease"].values
    p_img = test_merged["vd_prob"].values
    p_demo = test_merged["demo_prob"].values
    p_multi = test_merged["multimodal_prob"].values

    # 6. Evaluate all three on held-out test cohort
    # Find validation threshold for demo model
    val_thresh_demo = find_optimal_threshold(y_val_demo, val_demo_probs, method="youden")
    # Multimodal validation threshold:
    # Get val image predictions from val evaluation if possible, or use 0.5
    val_thresh_multi = 0.5

    demo_metrics = compute_binary_metrics(y_test, p_demo, threshold=val_thresh_demo, n_bootstraps=200)
    img_metrics = compute_binary_metrics(y_test, p_img, threshold=0.4996, n_bootstraps=200)
    multi_metrics = compute_binary_metrics(y_test, p_multi, threshold=val_thresh_multi, n_bootstraps=200)

    print("-" * 65)
    print("PATIENT-LEVEL TEST RESULTS (N=191):")
    print(f"1. Demographic-Only (Age + Sex):")
    print(f"   ROC-AUC: {demo_metrics['roc_auc']:.4f} (95% CI: {demo_metrics['roc_auc_ci_95']})")
    print(f"   PR-AUC:  {demo_metrics['pr_auc']:.4f} (95% CI: {demo_metrics['pr_auc_ci_95']})")
    print(f"   Sens: {demo_metrics['sensitivity']:.4f} | Spec: {demo_metrics['specificity']:.4f} | F1: {demo_metrics['f1_score']:.4f}")

    print(f"\n2. Retinal Image-Only (EfficientNet-B0):")
    print(f"   ROC-AUC: {img_metrics['roc_auc']:.4f} (95% CI: {img_metrics['roc_auc_ci_95']})")
    print(f"   PR-AUC:  {img_metrics['pr_auc']:.4f} (95% CI: {img_metrics['pr_auc_ci_95']})")
    print(f"   Sens: {img_metrics['sensitivity']:.4f} | Spec: {img_metrics['specificity']:.4f} | F1: {img_metrics['f1_score']:.4f}")

    print(f"\n3. Multimodal Fusion (Retinal Image + Demographics):")
    print(f"   ROC-AUC: {multi_metrics['roc_auc']:.4f} (95% CI: {multi_metrics['roc_auc_ci_95']})")
    print(f"   PR-AUC:  {multi_metrics['pr_auc']:.4f} (95% CI: {multi_metrics['pr_auc_ci_95']})")
    print(f"   Sens: {multi_metrics['sensitivity']:.4f} | Spec: {multi_metrics['specificity']:.4f} | F1: {multi_metrics['f1_score']:.4f}")
    print("-" * 65)

    # 7. Generate Comparison Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # ROC curves
    for name, p, m, col in [
        ("Demographic Prior (Age+Sex)", p_demo, demo_metrics, "blue"),
        ("Retinal Image-Only (B0)", p_img, img_metrics, "orange"),
        ("Multimodal Fusion (Image+Demo)", p_multi, multi_metrics, "green"),
    ]:
        fpr, tpr, _ = roc_curve(y_test, p)
        auc_val = m["roc_auc"]
        axes[0].plot(fpr, tpr, color=col, lw=2, label=f"{name} (AUC={auc_val:.3f})")

    axes[0].plot([0, 1], [0, 1], "k--", lw=1.2, label="Chance (AUC=0.500)")
    axes[0].set_title("Vascular Disease ROC Curves (Test Set N=191)", fontsize=13, fontweight="bold")
    axes[0].set_xlabel("1 - Specificity (FPR)", fontsize=11)
    axes[0].set_ylabel("Sensitivity (TPR)", fontsize=11)
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc="lower right", fontsize=10)

    # PR curves
    prevalence = float(np.mean(y_test))
    for name, p, m, col in [
        ("Demographic Prior (Age+Sex)", p_demo, demo_metrics, "blue"),
        ("Retinal Image-Only (B0)", p_img, img_metrics, "orange"),
        ("Multimodal Fusion (Image+Demo)", p_multi, multi_metrics, "green"),
    ]:
        prec, rec, _ = precision_recall_curve(y_test, p)
        prauc_val = m["pr_auc"]
        axes[1].plot(rec, prec, color=col, lw=2, label=f"{name} (PR-AUC={prauc_val:.3f})")

    axes[1].axhline(y=prevalence, color="k", linestyle="--", lw=1.2, label=f"Prevalence ({prevalence:.1%})")
    axes[1].set_title("Precision-Recall Curves (Test Set N=191)", fontsize=13, fontweight="bold")
    axes[1].set_xlabel("Recall (Sensitivity)", fontsize=11)
    axes[1].set_ylabel("Precision (PPV)", fontsize=11)
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="upper right", fontsize=10)

    plt.tight_layout()
    plot_path = plots_dir / "experiment_d_multimodal_curves.png"
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[Experiment D] Saved plots to {plot_path}")

    # 8. Save structured metrics JSON
    results = {
        "experiment": "experiment_d_demographic_multimodal_fusion",
        "demographic_only": demo_metrics,
        "image_only": img_metrics,
        "multimodal_fusion": multi_metrics,
        "test_n_patients": len(test_merged),
        "test_n_positive": int(y_test.sum()),
        "test_prevalence": float(prevalence),
        "logistic_regression_coefficients": {
            "age": float(demo_model.coef_[0][0]),
            "sex": float(demo_model.coef_[0][1]),
            "intercept": float(demo_model.intercept_[0]),
        },
    }
    metrics_path = metrics_dir / "experiment_d_multimodal_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[Experiment D] Saved metrics to {metrics_path}")


if __name__ == "__main__":
    run_experiment_d()
