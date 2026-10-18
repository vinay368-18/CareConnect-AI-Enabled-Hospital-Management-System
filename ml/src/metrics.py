"""
CareConnect Retinal AI: Metrics & Evaluation Utilities
======================================================
- Patient-level prediction aggregation (mean pooling over left/right eye scans).
- Decision threshold optimization strictly on validation data.
- Full metric suite: ROC-AUC, PR-AUC, Sensitivity, Specificity, Precision, F1, Brier Score.
- 95% Bootstrap Confidence Intervals.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def aggregate_patient_predictions(
    df_eval: pd.DataFrame,
    prob_col: str,
    target_col: str,
    patient_col: str = "patient",
    agg_method: str = "mean",
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Aggregate multiple image-level predictions per patient to a single patient-level probability.
    """
    valid = df_eval[df_eval[target_col].isin([0, 1])].copy()
    if len(valid) == 0:
        return np.array([]), np.array([]), pd.DataFrame()

    if agg_method == "mean":
        grouped = valid.groupby(patient_col).agg(
            prob=(prob_col, "mean"),
            true=(target_col, "first"),
            n_images=(prob_col, "count"),
        )
    elif agg_method == "max":
        grouped = valid.groupby(patient_col).agg(
            prob=(prob_col, "max"),
            true=(target_col, "first"),
            n_images=(prob_col, "count"),
        )
    else:
        raise ValueError(f"Unsupported aggregation method: {agg_method}")

    return grouped["true"].values, grouped["prob"].values, grouped


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    method: str = "youden",
) -> float:
    """
    Find optimal classification threshold strictly on VALIDATION data.
    Methods: 'youden' (Sensitivity + Specificity - 1) or 'f1' (F1 maximization).
    """
    if len(np.unique(y_true)) < 2:
        return 0.5

    if method == "youden":
        fpr, tpr, thresholds = roc_curve(y_true, y_prob)
        j_scores = tpr - fpr
        best_idx = int(np.argmax(j_scores))
        best_threshold = float(thresholds[best_idx])
    elif method == "f1":
        candidate_thresholds = np.linspace(0.10, 0.90, 81)
        best_f1 = -1.0
        best_threshold = 0.5
        for t in candidate_thresholds:
            preds = (y_prob >= t).astype(int)
            score = f1_score(y_true, preds, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_threshold = float(t)
    else:
        raise ValueError(f"Unknown threshold optimization method: {method}")

    return float(np.clip(best_threshold, 0.05, 0.95))


def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn: Any,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> Tuple[float, float]:
    """Calculate 95% bootstrap confidence interval."""
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n = len(y_true)
    if n < 5 or len(np.unique(y_true)) < 2:
        return (np.nan, np.nan)

    rng = np.random.RandomState(seed)
    scores = []
    for _ in range(n_bootstraps):
        boot_idx = rng.randint(0, n, size=n)
        yt_s = y_true[boot_idx]
        yp_s = y_prob[boot_idx]
        if len(np.unique(yt_s)) < 2:
            continue
        try:
            val = metric_fn(yt_s, yp_s)
            if not np.isnan(val):
                scores.append(val)
        except Exception:
            continue

    if len(scores) < 10:
        return (np.nan, np.nan)
    return tuple(np.percentile(scores, [2.5, 97.5]))


def compute_binary_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: Optional[float] = None,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Compute comprehensive binary classification evaluation metrics."""
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    if len(y_true) == 0:
        return {}

    has_both = len(np.unique(y_true)) == 2

    # ROC-AUC
    roc_auc = float(roc_auc_score(y_true, y_prob)) if has_both else np.nan
    auc_ci = bootstrap_ci(y_true, y_prob, roc_auc_score, n_bootstraps=n_bootstraps, seed=seed) if has_both else (np.nan, np.nan)

    # PR-AUC
    pr_auc = float(average_precision_score(y_true, y_prob)) if has_both else np.nan
    pr_ci = bootstrap_ci(y_true, y_prob, average_precision_score, n_bootstraps=n_bootstraps, seed=seed) if has_both else (np.nan, np.nan)

    # Calibration Brier score
    brier = float(brier_score_loss(y_true, y_prob))

    # Threshold metrics
    thresh = threshold if threshold is not None else 0.5
    y_pred = (y_prob >= thresh).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    if has_both:
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    else:
        tn = fp = fn = tp = 0
        spec = 0.0

    return {
        "n_samples": int(len(y_true)),
        "n_positives": int((y_true == 1).sum()),
        "prevalence": float(round((y_true == 1).mean(), 4)),
        "roc_auc": float(round(roc_auc, 4)) if not np.isnan(roc_auc) else None,
        "roc_auc_ci_95": [float(round(auc_ci[0], 4)), float(round(auc_ci[1], 4))] if not np.isnan(auc_ci[0]) else None,
        "pr_auc": float(round(pr_auc, 4)) if not np.isnan(pr_auc) else None,
        "pr_auc_ci_95": [float(round(pr_ci[0], 4)), float(round(pr_ci[1], 4))] if not np.isnan(pr_ci[0]) else None,
        "brier_score": float(round(brier, 4)),
        "threshold": float(round(thresh, 4)),
        "accuracy": float(round(acc, 4)),
        "sensitivity": float(round(rec, 4)),
        "specificity": float(round(spec, 4)),
        "precision": float(round(prec, 4)),
        "recall": float(round(rec, 4)),
        "f1_score": float(round(f1, 4)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def compute_dr_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Any]:
    """Compute multi-class metrics for Diabetic Retinopathy."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    valid_mask = np.isin(y_true, [0, 1, 2, 3, 4])
    y_t = y_true[valid_mask]
    y_p = y_pred[valid_mask]

    if len(y_t) == 0:
        return {}

    acc = float(accuracy_score(y_t, y_p))
    macro_f1 = float(f1_score(y_t, y_p, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_t, y_p, average="weighted", zero_division=0))
    cm = confusion_matrix(y_t, y_p, labels=[0, 1, 2, 3, 4]).tolist()

    return {
        "n_samples": int(len(y_t)),
        "accuracy": float(round(acc, 4)),
        "macro_f1": float(round(macro_f1, 4)),
        "weighted_f1": float(round(weighted_f1, 4)),
        "confusion_matrix": cm,
    }
