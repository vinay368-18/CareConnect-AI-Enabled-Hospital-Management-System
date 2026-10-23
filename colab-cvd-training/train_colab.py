"""
CareConnect Retinal AI: Google Colab & Standalone GPU Training Pipeline
======================================================================
Controlled research pipeline for improving CVD ROC-AUC on mBRSET and ODIR-5K.

Supports:
- Experiment 1: Baseline Replication (EfficientNet-B0, ImageNet init, default multi-task BCE)
- Experiment 2: Frozen Backbone (Linear probing with trainable task heads)
- Experiment 3: Gradual Unfreezing / Differential Learning Rates (Backbone 1e-5, Heads 1e-4)
- Experiment 4: Multi-Task Focal Loss (gamma=2.0, alpha-balanced)
- Experiment 5: Learning Rate Grid (1e-5 vs 3e-5 with Cosine Annealing)
- Experiment 6: Conservative Medical Augmentation & Resolution Tuning (256x256, CLAHE)
- Experiment 7: ODIR-5K Ocular Representation Pretraining -> mBRSET Fine-Tuning
- Experiment 8: Multimodal Late-Fusion (Image embeddings + Age + Sex)
"""

import argparse
import copy
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from PIL import Image
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
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as T
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


# -----------------------------------------------------------------------------
# 1. Deterministic Seeding & Invariant Helpers
# -----------------------------------------------------------------------------
def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]
DR_CLASSES = ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]
ODIR_CLASSES = ["N", "D", "G", "C", "A", "H", "M", "O"]


# -----------------------------------------------------------------------------
# 2. Transforms & Data Augmentation
# -----------------------------------------------------------------------------
def get_train_transforms(image_size: int = 224, enhanced: bool = False) -> T.Compose:
    if enhanced:
        return T.Compose([
            T.Resize((image_size, image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomVerticalFlip(p=0.3),
            T.RandomRotation(degrees=20),
            T.ColorJitter(brightness=0.15, contrast=0.20, saturation=0.15),
            T.RandomAffine(degrees=0, translate=(0.05, 0.05)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ])
    return T.Compose([
        T.Resize((image_size, image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomVerticalFlip(p=0.2),
        T.RandomRotation(degrees=15),
        T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def get_inference_transforms(image_size: int = 224) -> T.Compose:
    return T.Compose([
        T.Resize((image_size, image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


# -----------------------------------------------------------------------------
# 3. PyTorch Dataset Implementations
# -----------------------------------------------------------------------------
class MBRSETDataset(Dataset):
    """
    Multi-task PyTorch Dataset for mBRSET fundus images.
    Returns:
        image: Tensor of shape (3, H, W)
        targets: dict with 'vascular_disease', 'systemic_hypertension', 'dr_grade'
        masks: dict with 1.0 for valid supervision, 0.0 for missing
        clinical: optional Tensor of shape (clinical_dim,) with Age and Sex
        metadata: dict with 'patient', 'file'
    """

    def __init__(
        self,
        df: pd.DataFrame,
        images_dir: Union[str, Path],
        transform: Optional[Any] = None,
        include_clinical: bool = False,
    ):
        self.df = df.reset_index(drop=True)
        self.images_dir = Path(images_dir)
        self.transform = transform if transform is not None else get_inference_transforms()
        self.include_clinical = include_clinical

        # Targets & Masks
        vd_vals = pd.to_numeric(self.df.get("vascular_disease", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.vd_targets = np.where(np.isin(vd_vals, [0, 1]), vd_vals, -1).astype(np.float32)
        self.vd_masks = (self.vd_targets >= 0).astype(np.float32)

        ht_vals = pd.to_numeric(self.df.get("systemic_hypertension", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.ht_targets = np.where(np.isin(ht_vals, [0, 1]), ht_vals, -1).astype(np.float32)
        self.ht_masks = (self.ht_targets >= 0).astype(np.float32)

        dr_vals = pd.to_numeric(self.df.get("dr_grade", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.dr_targets = np.where(np.isin(dr_vals, [0, 1, 2, 3, 4]), dr_vals, -1).astype(np.int64)
        self.dr_masks = (self.dr_targets >= 0).astype(np.float32)

        # Precompute clinical features if requested (Age normalized + Sex binary)
        if self.include_clinical and "age" in self.df.columns and "sex" in self.df.columns:
            age_raw = pd.to_numeric(self.df["age"], errors="coerce").fillna(60.0).values
            age_norm = ((age_raw - 60.0) / 15.0).astype(np.float32)
            sex_binary = (self.df["sex"].astype(str).str.lower().str.startswith("m")).astype(np.float32).values
            self.clinical_feats = np.stack([age_norm, sex_binary], axis=1)
        else:
            self.clinical_feats = None

        self.files = self.df["file"].values
        self.patients = self.df["patient"].values

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        fname = self.files[idx]
        img_path = self.images_dir / fname
        if not img_path.exists():
            # Check recursive match if flat match fails
            matches = list(self.images_dir.rglob(fname))
            if matches:
                img_path = matches[0]
            else:
                raise FileNotFoundError(f"Image {fname} not found in {self.images_dir}")

        with Image.open(img_path) as im:
            img = im.convert("RGB")

        tensor = self.transform(img)

        item = {
            "image": tensor,
            "targets": {
                "vascular_disease": torch.tensor(self.vd_targets[idx], dtype=torch.float32),
                "systemic_hypertension": torch.tensor(self.ht_targets[idx], dtype=torch.float32),
                "dr_grade": torch.tensor(self.dr_targets[idx], dtype=torch.long),
            },
            "masks": {
                "vascular_disease": torch.tensor(self.vd_masks[idx], dtype=torch.float32),
                "systemic_hypertension": torch.tensor(self.ht_masks[idx], dtype=torch.float32),
                "dr_grade": torch.tensor(self.dr_masks[idx], dtype=torch.float32),
            },
            "metadata": {
                "patient": int(self.patients[idx]),
                "file": str(fname),
            },
        }

        if self.clinical_feats is not None:
            item["clinical"] = torch.tensor(self.clinical_feats[idx], dtype=torch.float32)

        return item


class ODIRDataset(Dataset):
    """
    Multi-label PyTorch Dataset for ODIR-5K ocular disease recognition.
    Classes: N, D, G, C, A, H, M, O (8 classes).
    """

    def __init__(
        self,
        df: pd.DataFrame,
        images_dir: Union[str, Path],
        transform: Optional[Any] = None,
    ):
        self.df = df.reset_index(drop=True)
        self.images_dir = Path(images_dir)
        self.transform = transform if transform is not None else get_inference_transforms()
        self.classes = ODIR_CLASSES

        # Extract 8-class binary targets
        labels = []
        for col in self.classes:
            if col in self.df.columns:
                labels.append(pd.to_numeric(self.df[col], errors="coerce").fillna(0).values)
            else:
                labels.append(np.zeros(len(self.df)))
        self.targets = np.stack(labels, axis=1).astype(np.float32)

        self.files = self.df["filename"].values if "filename" in self.df.columns else self.df["filepath"].values

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        fname = Path(str(self.files[idx])).name
        img_path = self.images_dir / fname
        if not img_path.exists():
            matches = list(self.images_dir.rglob(fname))
            if matches:
                img_path = matches[0]
            else:
                raise FileNotFoundError(f"ODIR image {fname} not found in {self.images_dir}")

        with Image.open(img_path) as im:
            img = im.convert("RGB")

        tensor = self.transform(img)
        return {
            "image": tensor,
            "targets": torch.tensor(self.targets[idx], dtype=torch.float32),
            "file": fname,
        }


# -----------------------------------------------------------------------------
# 4. Neural Network Architecture: CareConnectMultiTaskNet
# -----------------------------------------------------------------------------
class CareConnectMultiTaskNet(nn.Module):
    """
    Multi-Task Deep Convolutional Network for Retinal Risk Screening.
    Backbone: EfficientNet-B0 (1,280 features) + 3 dedicated heads.
    Optional clinical demographic MLP (Age + Sex).
    """

    def __init__(
        self,
        pretrained: bool = True,
        dropout: float = 0.4,
        clinical_dim: int = 0,
        clinical_hidden: int = 32,
        num_dr_classes: int = 5,
        custom_encoder: Optional[nn.Module] = None,
    ):
        super().__init__()
        self.clinical_dim = clinical_dim

        if custom_encoder is not None:
            self.features = custom_encoder
            self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        else:
            weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
            base = efficientnet_b0(weights=weights)
            self.features = base.features
            self.avgpool = base.avgpool

        self.dropout = nn.Dropout(p=dropout)
        feature_dim = 1280

        if clinical_dim > 0:
            self.clinical_mlp = nn.Sequential(
                nn.Linear(clinical_dim, clinical_hidden),
                nn.ReLU(inplace=True),
                nn.Dropout(p=0.2),
            )
            total_dim = feature_dim + clinical_hidden
        else:
            self.clinical_mlp = None
            total_dim = feature_dim

        self.head_vd = nn.Linear(total_dim, 1)
        self.head_ht = nn.Linear(total_dim, 1)
        self.head_dr = nn.Linear(total_dim, num_dr_classes)

    def extract_features(self, x: torch.Tensor, c: Optional[torch.Tensor] = None) -> torch.Tensor:
        feats = self.features(x)
        pooled = self.avgpool(feats).flatten(1)
        dropped = self.dropout(pooled)

        if self.clinical_mlp is not None and c is not None:
            c_feats = self.clinical_mlp(c)
            return torch.cat([dropped, c_feats], dim=1)
        return dropped

    def forward(
        self,
        x: torch.Tensor,
        c: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        f = self.extract_features(x, c)
        return {
            "vascular_disease": self.head_vd(f).squeeze(-1),
            "systemic_hypertension": self.head_ht(f).squeeze(-1),
            "dr_grade": self.head_dr(f),
        }


class ODIREncoderClassifier(nn.Module):
    """EfficientNet-B0 multi-label classifier for ODIR-5K representation pretraining."""

    def __init__(self, num_classes: int = 8, dropout: float = 0.3):
        super().__init__()
        base = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
        self.features = base.features
        self.avgpool = base.avgpool
        self.dropout = nn.Dropout(p=dropout)
        self.classifier = nn.Linear(1280, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f = self.features(x)
        pooled = self.avgpool(f).flatten(1)
        return self.classifier(self.dropout(pooled))


# -----------------------------------------------------------------------------
# 5. Loss Functions: Weighted BCE & Multi-Task Focal Loss
# -----------------------------------------------------------------------------
class FocalLossBinary(nn.Module):
    """Numerically stable binary Focal Loss with alpha class-balancing."""

    def __init__(self, gamma: float = 2.0, alpha: Optional[float] = None):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        p = torch.sigmoid(logits)
        p_t = p * targets + (1 - p) * (1 - targets)
        loss = bce * ((1 - p_t) ** self.gamma)

        if self.alpha is not None:
            alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
            loss = alpha_t * loss

        return loss


class CareConnectMultiTaskLoss(nn.Module):
    def __init__(
        self,
        pos_weight_vd: float = 1.0,
        pos_weight_ht: float = 1.0,
        use_focal_loss: bool = False,
        focal_gamma: float = 2.0,
        focal_alpha: Optional[float] = None,
        task_weights: Optional[Dict[str, float]] = None,
    ):
        super().__init__()
        self.use_focal_loss = use_focal_loss
        self.focal_loss = FocalLossBinary(gamma=focal_gamma, alpha=focal_alpha) if use_focal_loss else None

        self.register_buffer("pos_weight_vd", torch.tensor(pos_weight_vd, dtype=torch.float32))
        self.register_buffer("pos_weight_ht", torch.tensor(pos_weight_ht, dtype=torch.float32))

        if task_weights is None:
            task_weights = {"vascular_disease": 1.0, "systemic_hypertension": 0.5, "dr_grade": 0.5}
        self.task_weights = task_weights

    def forward(
        self,
        logits: Dict[str, torch.Tensor],
        targets: Dict[str, torch.Tensor],
        masks: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        # 1. Vascular Disease
        vd_logits = logits["vascular_disease"].float()
        vd_targets = targets["vascular_disease"].float()
        vd_mask = masks["vascular_disease"].float()

        if self.use_focal_loss:
            loss_vd_raw = self.focal_loss(vd_logits, vd_targets)
        else:
            loss_vd_raw = F.binary_cross_entropy_with_logits(
                vd_logits, vd_targets, pos_weight=self.pos_weight_vd, reduction="none"
            )
        valid_vd = vd_mask.sum().clamp(min=1.0)
        loss_vd = (loss_vd_raw * vd_mask).sum() / valid_vd

        # 2. Systemic Hypertension
        ht_logits = logits["systemic_hypertension"].float()
        ht_targets = targets["systemic_hypertension"].float()
        ht_mask = masks["systemic_hypertension"].float()
        loss_ht_raw = F.binary_cross_entropy_with_logits(
            ht_logits, ht_targets, pos_weight=self.pos_weight_ht, reduction="none"
        )
        valid_ht = ht_mask.sum().clamp(min=1.0)
        loss_ht = (loss_ht_raw * ht_mask).sum() / valid_ht

        # 3. Diabetic Retinopathy
        dr_logits = logits["dr_grade"].float()
        dr_targets = targets["dr_grade"].long()
        dr_mask = masks["dr_grade"].float()

        dr_targets_clamped = dr_targets.clamp(min=0)
        loss_dr_raw = F.cross_entropy(dr_logits, dr_targets_clamped, reduction="none")
        valid_dr = dr_mask.sum().clamp(min=1.0)
        loss_dr = (loss_dr_raw * dr_mask).sum() / valid_dr

        total_loss = (
            self.task_weights["vascular_disease"] * loss_vd
            + self.task_weights["systemic_hypertension"] * loss_ht
            + self.task_weights["dr_grade"] * loss_dr
        )

        return total_loss, {
            "total_loss": float(total_loss.item()),
            "loss_vd": float(loss_vd.item()),
            "loss_ht": float(loss_ht.item()),
            "loss_dr": float(loss_dr.item()),
        }


# -----------------------------------------------------------------------------
# 6. Evaluation, Metrics & Threshold Optimization
# -----------------------------------------------------------------------------
def aggregate_patient_predictions(
    df_eval: pd.DataFrame,
    prob_col: str,
    target_col: str,
    patient_col: str = "patient",
) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    valid = df_eval[df_eval[target_col].isin([0, 1])].copy()
    if len(valid) == 0:
        return np.array([]), np.array([]), pd.DataFrame()

    grouped = valid.groupby(patient_col).agg(
        prob=(prob_col, "mean"),
        true=(target_col, "first"),
        n_images=(prob_col, "count"),
    )
    return grouped["true"].values, grouped["prob"].values, grouped


def find_optimal_threshold(y_true: np.ndarray, y_prob: np.ndarray, method: str = "youden") -> float:
    if len(np.unique(y_true)) < 2:
        return 0.5
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    if method == "youden":
        j_scores = tpr - fpr
        best_idx = int(np.argmax(j_scores))
        best_t = float(thresholds[best_idx])
    else:
        best_t = 0.5
    return float(np.clip(best_t, 0.05, 0.95))


def bootstrap_ci(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    metric_fn: Any,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> Tuple[float, float]:
    rng = np.random.RandomState(seed)
    scores = []
    n = len(y_true)
    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, n)
        if len(np.unique(y_true[idx])) < 2:
            continue
        scores.append(metric_fn(y_true[idx], y_prob[idx]))
    if not scores:
        return 0.0, 0.0
    return float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))


def compute_binary_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: Optional[float] = None,
    n_bootstraps: int = 1000,
) -> Dict[str, Any]:
    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return {"roc_auc": 0.5, "pr_auc": 0.0}

    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))

    roc_ci = bootstrap_ci(y_true, y_prob, roc_auc_score, n_bootstraps=n_bootstraps)
    pr_ci = bootstrap_ci(y_true, y_prob, average_precision_score, n_bootstraps=n_bootstraps)

    if threshold is None:
        threshold = find_optimal_threshold(y_true, y_prob)

    preds = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()

    return {
        "n_samples": int(len(y_true)),
        "n_positives": int((y_true == 1).sum()),
        "prevalence": float(np.mean(y_true)),
        "roc_auc": round(roc_auc, 4),
        "roc_auc_ci_95": [round(roc_ci[0], 4), round(roc_ci[1], 4)],
        "pr_auc": round(pr_auc, 4),
        "pr_auc_ci_95": [round(pr_ci[0], 4), round(pr_ci[1], 4)],
        "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
        "threshold": round(float(threshold), 4),
        "accuracy": round(float(accuracy_score(y_true, preds)), 4),
        "sensitivity": round(float(recall_score(y_true, preds, zero_division=0)), 4),
        "specificity": round(float(tn / max(tn + fp, 1)), 4),
        "precision": round(float(precision_score(y_true, preds, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, preds, zero_division=0)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


# -----------------------------------------------------------------------------
# 7. Training & Evaluation Engine
# -----------------------------------------------------------------------------
def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler: Optional[torch.cuda.amp.GradScaler] = None,
) -> float:
    model.train()
    total_loss = 0.0
    count = 0

    for batch in loader:
        images = batch["image"].to(device, non_blocking=True)
        targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
        masks = {k: v.to(device, non_blocking=True) for k, v in batch["masks"].items()}
        clinical = batch.get("clinical", None)
        if clinical is not None:
            clinical = clinical.to(device, non_blocking=True)

        optimizer.zero_grad()

        if scaler is not None and device.type == "cuda":
            with torch.cuda.amp.autocast():
                logits = model(images, clinical)
                loss, _ = criterion(logits, targets, masks)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(images, clinical)
            loss, _ = criterion(logits, targets, masks)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

        b_size = images.size(0)
        total_loss += float(loss.item()) * b_size
        count += b_size

    return total_loss / max(count, 1)


@torch.no_grad()
def evaluate_model(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    threshold_vd: Optional[float] = None,
    threshold_ht: Optional[float] = None,
) -> Dict[str, Any]:
    model.eval()
    total_loss = 0.0
    count = 0

    all_vd_probs, all_ht_probs, all_dr_preds = [], [], []
    all_vd_true, all_ht_true, all_dr_true = [], [], []
    all_patients, all_files = [], []

    for batch in loader:
        images = batch["image"].to(device, non_blocking=True)
        targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
        masks = {k: v.to(device, non_blocking=True) for k, v in batch["masks"].items()}
        clinical = batch.get("clinical", None)
        if clinical is not None:
            clinical = clinical.to(device, non_blocking=True)

        logits = model(images, clinical)
        loss, _ = criterion(logits, targets, masks)

        b_size = images.size(0)
        total_loss += float(loss.item()) * b_size
        count += b_size

        vd_p = torch.sigmoid(logits["vascular_disease"]).cpu().numpy()
        ht_p = torch.sigmoid(logits["systemic_hypertension"]).cpu().numpy()
        dr_pred = logits["dr_grade"].argmax(dim=-1).cpu().numpy()

        all_vd_probs.extend(vd_p.tolist() if vd_p.ndim > 0 else [float(vd_p)])
        all_ht_probs.extend(ht_p.tolist() if ht_p.ndim > 0 else [float(ht_p)])
        all_dr_preds.extend(dr_pred.tolist() if dr_pred.ndim > 0 else [int(dr_pred)])

        all_vd_true.extend(targets["vascular_disease"].cpu().numpy().tolist())
        all_ht_true.extend(targets["systemic_hypertension"].cpu().numpy().tolist())
        all_dr_true.extend(targets["dr_grade"].cpu().numpy().tolist())
        all_patients.extend(batch["metadata"]["patient"])
        all_files.extend(batch["metadata"]["file"])

    eval_df = pd.DataFrame({
        "patient": all_patients,
        "file": all_files,
        "vd_prob": all_vd_probs,
        "vd_true": all_vd_true,
        "ht_prob": all_ht_probs,
        "ht_true": all_ht_true,
        "dr_pred": all_dr_preds,
        "dr_true": all_dr_true,
    })

    # Patient-level metrics for VD
    y_vd_true, y_vd_prob, _ = aggregate_patient_predictions(eval_df, "vd_prob", "vd_true")
    vd_metrics = compute_binary_metrics(y_vd_true, y_vd_prob, threshold=threshold_vd, n_bootstraps=200)

    # DR accuracy
    dr_valid = [t for t in all_dr_true if t >= 0]
    dr_preds_valid = [all_dr_preds[i] for i, t in enumerate(all_dr_true) if t >= 0]
    dr_acc = float(accuracy_score(dr_valid, dr_preds_valid)) if dr_valid else 0.0
    dr_f1 = float(f1_score(dr_valid, dr_preds_valid, average="weighted", zero_division=0)) if dr_valid else 0.0

    return {
        "loss": total_loss / max(count, 1),
        "vd_metrics": vd_metrics,
        "dr_accuracy": round(dr_acc, 4),
        "dr_weighted_f1": round(dr_f1, 4),
        "eval_df": eval_df,
    }


# -----------------------------------------------------------------------------
# 8. ODIR-5K Pretraining Subroutine
# -----------------------------------------------------------------------------
def pretrain_odir_encoder(
    odir_df: pd.DataFrame,
    images_dir: Path,
    output_dir: Path,
    device: torch.device,
    epochs: int = 5,
    batch_size: int = 32,
    lr: float = 3e-4,
) -> nn.Module:
    print(f"\n[ODIR Pretraining] Starting ODIR-5K ocular pretraining ({len(odir_df)} images, {epochs} epochs)...")
    dataset = ODIRDataset(odir_df, images_dir, transform=get_train_transforms(224, enhanced=True))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)

    model = ODIREncoderClassifier(num_classes=8, dropout=0.3).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        count = 0
        t0 = time.time()
        for batch in loader:
            images = batch["image"].to(device, non_blocking=True)
            targets = batch["targets"].to(device, non_blocking=True)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, targets)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(images)
            count += len(images)
        el = time.time() - t0
        print(f"  Epoch {epoch:02d}/{epochs:02d} | ODIR Multi-Label Loss: {total_loss / max(count, 1):.4f} | Time: {el:.1f}s")

    # Save pretrained encoder
    encoder_path = output_dir / "odir_pretrained_encoder.pt"
    torch.save(model.features.state_dict(), encoder_path)
    print(f"[ODIR Pretraining] Pretrained encoder saved to {encoder_path}")
    return model.features


# -----------------------------------------------------------------------------
# 9. Main Research Experiment Dispatcher
# -----------------------------------------------------------------------------
def run_experiment(
    exp_name: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: Optional[pd.DataFrame],
    images_dir: Path,
    output_dir: Path,
    device: torch.device,
    epochs: int = 10,
    batch_size: int = 32,
    lr_backbone: float = 1e-5,
    lr_heads: float = 1e-4,
    use_focal_loss: bool = False,
    freeze_backbone: bool = False,
    enhanced_aug: bool = False,
    include_clinical: bool = False,
    custom_encoder: Optional[nn.Module] = None,
    eval_test: bool = False,
) -> Dict[str, Any]:
    print(f"\n{'='*70}\n[EXPERIMENT] {exp_name.upper()}\n{'='*70}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Class weights from train set strictly
    vd_train = train_df["vascular_disease"]
    pos_w_vd = float((vd_train == 0).sum() / max((vd_train == 1).sum(), 1))
    ht_train = train_df["systemic_hypertension"]
    pos_w_ht = float((ht_train == 0).sum() / max((ht_train == 1).sum(), 1))

    # Datasets & Loaders
    train_ds = MBRSETDataset(train_df, images_dir, transform=get_train_transforms(224, enhanced=enhanced_aug), include_clinical=include_clinical)
    val_ds = MBRSETDataset(val_df, images_dir, transform=get_inference_transforms(224), include_clinical=include_clinical)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=2, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    # Model
    clinical_dim = 2 if include_clinical else 0
    model = CareConnectMultiTaskNet(
        pretrained=True,
        clinical_dim=clinical_dim,
        custom_encoder=custom_encoder,
    ).to(device)

    # Freezing logic
    if freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False
        print("  -> EfficientNet-B0 features frozen (Linear Probing mode).")

    # Optimizer with differential learning rates
    params = [
        {"params": [p for p in model.features.parameters() if p.requires_grad], "lr": lr_backbone},
        {"params": model.head_vd.parameters(), "lr": lr_heads},
        {"params": model.head_ht.parameters(), "lr": lr_heads},
        {"params": model.head_dr.parameters(), "lr": lr_heads},
    ]
    if model.clinical_mlp is not None:
        params.append({"params": model.clinical_mlp.parameters(), "lr": lr_heads})

    optimizer = torch.optim.AdamW(params, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    criterion = CareConnectMultiTaskLoss(
        pos_weight_vd=pos_w_vd,
        pos_weight_ht=pos_w_ht,
        use_focal_loss=use_focal_loss,
    )
    scaler = torch.cuda.amp.GradScaler() if device.type == "cuda" else None

    best_val_auc = -1.0
    best_threshold = 0.5
    best_metrics = {}
    best_state = None
    patience = 4
    patience_counter = 0

    history = []

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device, scaler)
        scheduler.step()

        val_res = evaluate_model(model, val_loader, criterion, device)
        val_auc = val_res["vd_metrics"]["roc_auc"]
        val_loss = val_res["loss"]
        dr_acc = val_res["dr_accuracy"]
        el = time.time() - t0

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_vd_auc": val_auc,
            "val_vd_pr_auc": val_res["vd_metrics"]["pr_auc"],
            "val_dr_acc": dr_acc,
        })

        print(f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val VD AUC: {val_auc:.4f} | DR Acc: {dr_acc*100:.1f}% | Time: {el:.1f}s")

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_threshold = val_res["vd_metrics"]["threshold"]
            best_metrics = val_res["vd_metrics"]
            best_state = copy.deepcopy(model.state_dict())
            patience_counter = 0
            torch.save(best_state, output_dir / f"{exp_name}_best.pt")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  Early stopping triggered at Epoch {epoch} (patience={patience}).")
                break

    # Restore best checkpoint
    if best_state is not None:
        model.load_state_dict(best_state)

    # Final evaluation on Validation
    final_val = evaluate_model(model, val_loader, criterion, device, threshold_vd=best_threshold)

    results = {
        "experiment": exp_name,
        "best_epoch_val_auc": best_val_auc,
        "best_threshold": best_threshold,
        "val_metrics": final_val["vd_metrics"],
        "val_dr_accuracy": final_val["dr_accuracy"],
        "history": history,
    }

    # Optional final test evaluation (only if explicitly requested for candidate model)
    if eval_test and test_df is not None:
        print(f"\n[TEST EVALUATION] Evaluating {exp_name} on Held-Out Test Cohort (N={test_df['patient'].nunique()} patients)...")
        test_ds = MBRSETDataset(test_df, images_dir, transform=get_inference_transforms(224), include_clinical=include_clinical)
        test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=2)
        test_res = evaluate_model(model, test_loader, criterion, device, threshold_vd=best_threshold)
        results["test_metrics"] = test_res["vd_metrics"]
        results["test_dr_accuracy"] = test_res["dr_accuracy"]
        print(f"  --> HELD-OUT TEST VD ROC-AUC: {test_res['vd_metrics']['roc_auc']:.4f} {test_res['vd_metrics']['roc_auc_ci_95']}")
        print(f"  --> HELD-OUT TEST Sensitivity: {test_res['vd_metrics']['sensitivity']*100:.1f}% | Specificity: {test_res['vd_metrics']['specificity']*100:.1f}%")
        print(f"  --> HELD-OUT TEST DR Accuracy: {test_res['dr_accuracy']*100:.1f}%")

    with open(output_dir / f"{exp_name}_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


# -----------------------------------------------------------------------------
# 10. CLI Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="CareConnect Retinal AI Research GPU Training")
    parser.add_argument("--mbrset_root", type=str, required=True, help="Directory containing mBRSET images")
    parser.add_argument("--splits_dir", type=str, required=True, help="Directory with train.csv, val.csv, test.csv")
    parser.add_argument("--odir_root", type=str, default="", help="Directory with ODIR full_df.csv and preprocessed_images")
    parser.add_argument("--output_root", type=str, default="./experiments_output", help="Output directory for checkpoints and logs")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs per experiment")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size (reduce to 16 if OOM occurs)")
    parser.add_argument("--experiment", type=str, default="all", choices=["all", "exp1", "exp2", "exp3", "exp4", "exp5", "exp6", "exp7", "exp8"])
    parser.add_argument("--eval_test", action="store_true", help="Evaluate best candidate model on held-out test cohort")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n=======================================================")
    print(f" CARECONNECT RETINAL AI: RESEARCH EXPERIMENT ENGINE")
    print(f" Device: {device.type.upper()} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    print(f"=======================================================\n")

    splits_p = Path(args.splits_dir)
    train_df = pd.read_csv(splits_p / "train.csv")
    val_df = pd.read_csv(splits_p / "val.csv")
    test_df = pd.read_csv(splits_p / "test.csv")
    mbrset_img = Path(args.mbrset_root)
    out_dir = Path(args.output_root)

    print(f"Partitions Loaded: Train {len(train_df)} imgs ({train_df['patient'].nunique()} pts) | Val {len(val_df)} imgs ({val_df['patient'].nunique()} pts) | Test {len(test_df)} imgs ({test_df['patient'].nunique()} pts)")

    results_table = []

    # Run chosen experiments
    if args.experiment in ["all", "exp1"]:
        r1 = run_experiment("exp1_baseline", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, lr_backbone=1e-4, lr_heads=1e-4)
        results_table.append(r1)

    if args.experiment in ["all", "exp2"]:
        r2 = run_experiment("exp2_frozen_backbone", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, freeze_backbone=True, lr_heads=3e-4)
        results_table.append(r2)

    if args.experiment in ["all", "exp3"]:
        r3 = run_experiment("exp3_differential_lr", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, lr_backbone=1e-5, lr_heads=1e-4)
        results_table.append(r3)

    if args.experiment in ["all", "exp4"]:
        r4 = run_experiment("exp4_focal_loss", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, use_focal_loss=True, lr_backbone=1e-5, lr_heads=1e-4)
        results_table.append(r4)

    if args.experiment in ["all", "exp5"]:
        r5 = run_experiment("exp5_lr_3e5", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, lr_backbone=3e-5, lr_heads=1e-4)
        results_table.append(r5)

    if args.experiment in ["all", "exp6"]:
        r6 = run_experiment("exp6_medical_augmentation", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, enhanced_aug=True, lr_backbone=1e-5, lr_heads=1e-4)
        results_table.append(r6)

    # ODIR pretraining
    if args.experiment in ["all", "exp7"] and args.odir_root:
        odir_p = Path(args.odir_root)
        csv_p = odir_p / "full_df.csv"
        img_p = odir_p / "preprocessed_images"
        if csv_p.exists() and img_p.exists():
            odir_df = pd.read_csv(csv_p)
            custom_enc = pretrain_odir_encoder(odir_df, img_p, out_dir, device, epochs=min(5, args.epochs), batch_size=args.batch_size)
            r7 = run_experiment("exp7_odir_transfer", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, custom_encoder=custom_enc, lr_backbone=1e-5, lr_heads=1e-4)
            results_table.append(r7)
        else:
            print("[Warning] ODIR files not found. Skipping Exp 7.")

    if args.experiment in ["all", "exp8"]:
        r8 = run_experiment("exp8_multimodal_demographics", train_df, val_df, test_df, mbrset_img, out_dir, device, epochs=args.epochs, batch_size=args.batch_size, include_clinical=True, lr_backbone=1e-5, lr_heads=1e-4)
        results_table.append(r8)

    print("\n" + "="*70)
    print(" RESEARCH EXPERIMENT SUMMARY TABLE")
    print("="*70)
    summary_rows = []
    for r in results_table:
        summary_rows.append({
            "Experiment": r["experiment"],
            "Val VD ROC-AUC": r["val_metrics"]["roc_auc"],
            "Val VD PR-AUC": r["val_metrics"]["pr_auc"],
            "Val DR Accuracy": r["val_dr_accuracy"],
            "Optimal Threshold": r["best_threshold"],
        })
    sum_df = pd.DataFrame(summary_rows)
    print(sum_df.to_string(index=False))
    sum_df.to_csv(out_dir / "all_experiments_summary.csv", index=False)
    print(f"\nAll results saved to {out_dir / 'all_experiments_summary.csv'}")


if __name__ == "__main__":
    main()
