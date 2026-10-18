"""
CareConnect Retinal AI: Comprehensive Evaluation Pipeline
=========================================================
- Evaluates any checkpoint on held-out test split.
- Determines optimal decision thresholds STRICTLY on validation data, then freezes them.
- Computes patient-level and image-level metrics with 95% bootstrap confidence intervals.
- Generates ROC & PR curve plots.
- Saves structured JSON metrics and CSV predictions.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve
import torch
from torch.utils.data import DataLoader

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.dataset import CareConnectFundusDataset, get_inference_transforms
from ml.src.metrics import (
    aggregate_patient_predictions,
    compute_binary_metrics,
    compute_dr_metrics,
    find_optimal_threshold,
)
from ml.src.models import CareConnectMultiTaskNet, DR_CLASSES


def resolve_image_dir(data_root: Optional[Path]) -> Path:
    if data_root and (data_root / "images").exists():
        return data_root / "images"

    candidates = [
        Path(r"C:\Users\vinay\CVD Project\mbrset-a-mobile-brazilian-retinal-dataset-1.0-20261001T140750Z-1-001\mbrset-a-mobile-brazilian-retinal-dataset-1.0\images"),
        PROJECT_ROOT / "ml" / "datasets" / "images",
    ]
    for c in candidates:
        if c.exists():
            return c

    found = list(Path(r"C:\Users\vinay").rglob("labels_mbrset.csv"))
    if found:
        img_p = found[0].parent / "images"
        if img_p.exists():
            return img_p

    raise FileNotFoundError("Could not locate images directory.")


def load_model_for_evaluation(
    checkpoint_path: Path,
    device: torch.device,
) -> CareConnectMultiTaskNet:
    model = CareConnectMultiTaskNet(pretrained=False).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    state_dict = ckpt.get("model_state_dict", ckpt)

    cleaned_state = {}
    for k, v in state_dict.items():
        clean_k = k.replace("module.", "")
        if clean_k == "head_cvd.weight":
            clean_k = "head_vd.weight"
        elif clean_k == "head_cvd.bias":
            clean_k = "head_vd.bias"
        cleaned_state[clean_k] = v

    model.load_state_dict(cleaned_state, strict=False)
    model.eval()
    return model


@torch.no_grad()
def run_forward_evaluation(
    model: torch.nn.Module,
    dataset: CareConnectFundusDataset,
    device: torch.device,
    batch_size: int = 16,
) -> pd.DataFrame:
    model.eval()
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    all_vd_p, all_ht_p, all_dr_pred = [], [], []
    all_vd_y, all_ht_y, all_dr_y = [], [], []
    all_pats, all_files = [], []

    for batch in loader:
        imgs = batch["image"].to(device)
        targets = batch["targets"]

        logits = model(imgs)

        vd_p = torch.sigmoid(logits["vascular_disease"]).cpu().numpy()
        ht_p = torch.sigmoid(logits["systemic_hypertension"]).cpu().numpy()
        dr_pred = logits["dr_grade"].argmax(dim=-1).cpu().numpy()

        all_vd_p.extend(vd_p.tolist() if vd_p.ndim > 0 else [float(vd_p)])
        all_ht_p.extend(ht_p.tolist() if ht_p.ndim > 0 else [float(ht_p)])
        all_dr_pred.extend(dr_pred.tolist() if dr_pred.ndim > 0 else [int(dr_pred)])

        all_vd_y.extend(targets["vascular_disease"].numpy().tolist())
        all_ht_y.extend(targets["systemic_hypertension"].numpy().tolist())
        all_dr_y.extend(targets["dr_grade"].numpy().tolist())

        p_list = batch["metadata"]["patient"]
        all_pats.extend([int(p.item()) if isinstance(p, torch.Tensor) else int(p) for p in p_list])
        all_files.extend(batch["metadata"]["file"])

    return pd.DataFrame({
        "patient": all_pats,
        "file": all_files,
        "vd_prob": all_vd_p,
        "vd_true": all_vd_y,
        "ht_prob": all_ht_p,
        "ht_true": all_ht_y,
        "dr_pred": all_dr_pred,
        "dr_true": all_dr_y,
    })


def evaluate_checkpoint(
    checkpoint_path: Path,
    val_csv: Path,
    test_csv: Path,
    experiment_name: str,
    data_root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    images_dir = resolve_image_dir(data_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Evaluate] Checkpoint:      {checkpoint_path}")
    print(f"[Evaluate] Device:          {device.type.upper()}")
    print(f"[Evaluate] Experiment Name: {experiment_name}")

    if output_dir is None:
        output_dir = PROJECT_ROOT / "ml" / "metrics"
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    preds_dir = output_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)

    val_df = pd.read_csv(val_csv)
    test_df = pd.read_csv(test_csv)

    val_ds = CareConnectFundusDataset(val_df, images_dir=images_dir, is_training=False)
    test_ds = CareConnectFundusDataset(test_df, images_dir=images_dir, is_training=False)

    print(f"[Evaluate] Val Cohort:  {val_df['patient'].nunique()} patients ({len(val_df)} images)")
    print(f"[Evaluate] Test Cohort: {test_df['patient'].nunique()} patients ({len(test_df)} images)")

    # 1. Load model
    model = load_model_for_evaluation(checkpoint_path, device)

    # 2. Threshold determination on VALIDATION set ONLY
    print("[Evaluate] Optimizing decision threshold strictly on VALIDATION split using Youden's J...")
    val_preds_df = run_forward_evaluation(model, val_ds, device)
    y_vd_val_t, y_vd_val_p, _ = aggregate_patient_predictions(val_preds_df, "vd_prob", "vd_true")
    vd_threshold = find_optimal_threshold(y_vd_val_t, y_vd_val_p, method="youden")

    y_ht_val_t, y_ht_val_p, _ = aggregate_patient_predictions(val_preds_df, "ht_prob", "ht_true")
    ht_threshold = find_optimal_threshold(y_ht_val_t, y_ht_val_p, method="youden")

    print(f"[Evaluate] Validation Frozen VD Threshold: {vd_threshold:.4f}")
    print(f"[Evaluate] Validation Frozen HT Threshold: {ht_threshold:.4f}")

    # 3. Evaluate on TEST set
    print("[Evaluate] Evaluating on held-out TEST cohort with frozen thresholds...")
    test_preds_df = run_forward_evaluation(model, test_ds, device)

    # Save test predictions
    test_preds_path = preds_dir / f"{experiment_name}_test_predictions.csv"
    test_preds_df.to_csv(test_preds_path, index=False)
    print(f"[Evaluate] Saved test predictions: {test_preds_path}")

    # Patient-level metrics for vascular disease
    y_vd_test_t, y_vd_test_p, vd_summary = aggregate_patient_predictions(test_preds_df, "vd_prob", "vd_true")
    vd_patient_metrics = compute_binary_metrics(y_vd_test_t, y_vd_test_p, threshold=vd_threshold, n_bootstraps=1000)

    # Image-level metrics for vascular disease
    vd_image_metrics = compute_binary_metrics(test_preds_df["vd_true"].values, test_preds_df["vd_prob"].values, threshold=vd_threshold, n_bootstraps=1000)

    # Patient-level metrics for hypertension
    y_ht_test_t, y_ht_test_p, ht_summary = aggregate_patient_predictions(test_preds_df, "ht_prob", "ht_true")
    ht_patient_metrics = compute_binary_metrics(y_ht_test_t, y_ht_test_p, threshold=ht_threshold, n_bootstraps=1000)

    # Image-level DR metrics
    dr_image_metrics = compute_dr_metrics(test_preds_df["dr_true"].values, test_preds_df["dr_pred"].values)

    # Report results
    print("=" * 60)
    print(f"HELD-OUT TEST RESULTS: {experiment_name.upper()}")
    print("=" * 60)
    print(f"Vascular Disease (Patient-Level, N={vd_patient_metrics.get('n_samples')}):")
    print(f"  ROC-AUC:     {vd_patient_metrics.get('roc_auc')} (95% CI: {vd_patient_metrics.get('roc_auc_ci_95')})")
    print(f"  PR-AUC:      {vd_patient_metrics.get('pr_auc')} (95% CI: {vd_patient_metrics.get('pr_auc_ci_95')})")
    print(f"  Sensitivity: {vd_patient_metrics.get('sensitivity')}")
    print(f"  Specificity: {vd_patient_metrics.get('specificity')}")
    print(f"  F1 Score:    {vd_patient_metrics.get('f1_score')}")
    print(f"  Accuracy:    {vd_patient_metrics.get('accuracy')}")
    print(f"  Confusion:   {vd_patient_metrics.get('confusion_matrix')}")
    print(f"  Threshold:   {vd_patient_metrics.get('threshold')} (frozen from validation)")

    print("-" * 50)
    print(f"Systemic Hypertension (Patient-Level, N={ht_patient_metrics.get('n_samples')}):")
    print(f"  ROC-AUC:     {ht_patient_metrics.get('roc_auc')} (95% CI: {ht_patient_metrics.get('roc_auc_ci_95')})")
    print(f"  PR-AUC:      {ht_patient_metrics.get('pr_auc')} (95% CI: {ht_patient_metrics.get('pr_auc_ci_95')})")
    print(f"  Sensitivity: {ht_patient_metrics.get('sensitivity')}")
    print(f"  Specificity: {ht_patient_metrics.get('specificity')}")
    print(f"  F1 Score:    {ht_patient_metrics.get('f1_score')}")

    print("-" * 50)
    print(f"Diabetic Retinopathy (Image-Level, N={dr_image_metrics.get('n_samples')}):")
    print(f"  Accuracy:    {dr_image_metrics.get('accuracy')}")
    print(f"  Weighted F1: {dr_image_metrics.get('weighted_f1')}")
    print("=" * 60)

    # 4. Generate ROC & PR Curves Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    if len(np.unique(y_vd_test_t)) == 2:
        fpr_v, tpr_v, _ = roc_curve(y_vd_test_t, y_vd_test_p)
        ax1.plot(fpr_v, tpr_v, "b-", lw=2, label=f"Vascular Disease (AUC = {vd_patient_metrics.get('roc_auc', 0):.3f})")
    if len(np.unique(y_ht_test_t)) == 2:
        fpr_h, tpr_h, _ = roc_curve(y_ht_test_t, y_ht_test_p)
        ax1.plot(fpr_h, tpr_h, "r--", lw=2, label=f"Hypertension (AUC = {ht_patient_metrics.get('roc_auc', 0):.3f})")
    ax1.plot([0, 1], [0, 1], "k:", alpha=0.5)
    ax1.set_title(f"Test ROC Curves — {experiment_name}")
    ax1.set_xlabel("False Positive Rate")
    ax1.set_ylabel("True Positive Rate")
    ax1.legend(loc="lower right")
    ax1.grid(alpha=0.3)

    if len(np.unique(y_vd_test_t)) == 2:
        pr_v, rec_v, _ = precision_recall_curve(y_vd_test_t, y_vd_test_p)
        ax2.plot(rec_v, pr_v, "b-", lw=2, label=f"Vascular Disease (PR-AUC = {vd_patient_metrics.get('pr_auc', 0):.3f})")
    if len(np.unique(y_ht_test_t)) == 2:
        pr_h, rec_h, _ = precision_recall_curve(y_ht_test_t, y_ht_test_p)
        ax2.plot(rec_h, pr_h, "r--", lw=2, label=f"Hypertension (PR-AUC = {ht_patient_metrics.get('pr_auc', 0):.3f})")
    ax2.set_title(f"Test Precision-Recall Curves — {experiment_name}")
    ax2.set_xlabel("Recall")
    ax2.set_ylabel("Precision")
    ax2.legend(loc="lower left")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plot_path = plots_dir / f"{experiment_name}_evaluation_curves.png"
    plt.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"[Evaluate] Saved evaluation plots: {plot_path}")

    # 5. Save structured JSON
    results_json = {
        "experiment_name": experiment_name,
        "checkpoint": str(checkpoint_path),
        "validation_thresholds": {
            "vascular_disease": vd_threshold,
            "systemic_hypertension": ht_threshold,
            "method": "Youden's J optimized on validation cohort",
        },
        "test_metrics_patient_level": {
            "vascular_disease": vd_patient_metrics,
            "systemic_hypertension": ht_patient_metrics,
        },
        "test_metrics_image_level": {
            "vascular_disease": vd_image_metrics,
            "diabetic_retinopathy": dr_image_metrics,
        },
    }

    metrics_json_path = output_dir / f"{experiment_name}_metrics.json"
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(results_json, f, indent=2)
    print(f"[Evaluate] Saved metrics JSON: {metrics_json_path}")

    return results_json


def main():
    parser = argparse.ArgumentParser(description="Evaluate CareConnect Checkpoint")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to checkpoint .pt file")
    parser.add_argument("--val-split", type=str, default="ml/datasets/splits/val.csv", help="Path to val split CSV")
    parser.add_argument("--test-split", type=str, default="ml/datasets/splits/test.csv", help="Path to test split CSV")
    parser.add_argument("--experiment-name", type=str, default="evaluation", help="Identifier for experiment outputs")
    parser.add_argument("--data-root", type=str, default=None, help="Optional data root")
    args = parser.parse_args()

    ckpt_path = Path(args.checkpoint)
    val_path = PROJECT_ROOT / args.val_split if not Path(args.val_split).is_absolute() else Path(args.val_split)
    test_path = PROJECT_ROOT / args.test_split if not Path(args.test_split).is_absolute() else Path(args.test_split)

    evaluate_checkpoint(
        checkpoint_path=ckpt_path,
        val_csv=val_path,
        test_csv=test_path,
        experiment_name=args.experiment_name,
        data_root=Path(args.data_root) if args.data_root else None,
    )


if __name__ == "__main__":
    main()
