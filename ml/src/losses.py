"""
CareConnect Retinal AI: Loss Functions & Imbalance Handling
===========================================================
- Computes positive class weights strictly from the TRAINING partition.
- Valid and Test sets are NEVER accessed during weight calculation or loss optimization.
- Missing labels (mask == 0.0) are completely masked out of the gradient computation.
- Guards against NaN and Inf loss values.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F


def compute_training_class_weights(train_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate positive class weights strictly from the training partition:
    pos_weight = N_negative / max(N_positive, 1)

    Args:
        train_df: Training partition DataFrame.

    Returns:
        Dict with 'vascular_disease' and 'systemic_hypertension' weights.
    """
    # 1. vascular_disease
    vd_col = train_df["vascular_disease"]
    vd_valid = vd_col[vd_col.isin([0, 1])]
    n_vd_neg = (vd_valid == 0).sum()
    n_vd_pos = (vd_valid == 1).sum()
    pos_weight_vd = float(n_vd_neg / max(n_vd_pos, 1))

    # 2. systemic_hypertension
    ht_col = train_df["systemic_hypertension"]
    ht_valid = ht_col[ht_col.isin([0, 1])]
    n_ht_neg = (ht_valid == 0).sum()
    n_ht_pos = (ht_valid == 1).sum()
    pos_weight_ht = float(n_ht_neg / max(n_ht_pos, 1))

    return {
        "vascular_disease": pos_weight_vd,
        "systemic_hypertension": pos_weight_ht,
        "n_train_vd_pos": int(n_vd_pos),
        "n_train_vd_neg": int(n_vd_neg),
        "n_train_ht_pos": int(n_ht_pos),
        "n_train_ht_neg": int(n_ht_neg),
    }


class CareConnectMultiTaskLoss(nn.Module):
    """
    Multi-task loss module with task weight balancing and sample masking.
    """

    def __init__(
        self,
        pos_weight_vd: float = 1.0,
        pos_weight_ht: float = 1.0,
        task_weights: Optional[Dict[str, float]] = None,
        device: Optional[torch.device] = None,
    ):
        super().__init__()
        self.device = device if device is not None else torch.device("cpu")

        self.register_buffer("pos_weight_vd", torch.tensor(pos_weight_vd, dtype=torch.float32))
        self.register_buffer("pos_weight_ht", torch.tensor(pos_weight_ht, dtype=torch.float32))

        if task_weights is None:
            task_weights = {"vascular_disease": 1.0, "systemic_hypertension": 0.5, "dr_grade": 0.5}
        self.task_weights = task_weights

    def forward(
        self,
        logits_dict: Dict[str, torch.Tensor],
        targets_dict: Dict[str, torch.Tensor],
        masks_dict: Dict[str, torch.Tensor],
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute total multi-task loss and per-task losses.
        """
        # 1. Vascular Disease Loss
        vd_logits = logits_dict["vascular_disease"].float()
        vd_targets = targets_dict["vascular_disease"].float()
        vd_mask = masks_dict["vascular_disease"].float()

        loss_vd_raw = F.binary_cross_entropy_with_logits(
            vd_logits, vd_targets, pos_weight=self.pos_weight_vd, reduction="none"
        )
        valid_vd = vd_mask.sum().clamp(min=1.0)
        loss_vd = (loss_vd_raw * vd_mask).sum() / valid_vd

        # 2. Systemic Hypertension Loss
        ht_logits = logits_dict["systemic_hypertension"].float()
        ht_targets = targets_dict["systemic_hypertension"].float()
        ht_mask = masks_dict["systemic_hypertension"].float()

        loss_ht_raw = F.binary_cross_entropy_with_logits(
            ht_logits, ht_targets, pos_weight=self.pos_weight_ht, reduction="none"
        )
        valid_ht = ht_mask.sum().clamp(min=1.0)
        loss_ht = (loss_ht_raw * ht_mask).sum() / valid_ht

        # 3. Diabetic Retinopathy Loss (Cross-Entropy)
        dr_logits = logits_dict["dr_grade"].float()
        dr_targets = targets_dict["dr_grade"].long()
        dr_mask = masks_dict["dr_grade"].float()

        loss_dr_raw = F.cross_entropy(dr_logits, dr_targets, reduction="none")
        valid_dr = dr_mask.sum().clamp(min=1.0)
        loss_dr = (loss_dr_raw * dr_mask).sum() / valid_dr

        # Weighted combination
        total_loss = (
            self.task_weights.get("vascular_disease", 1.0) * loss_vd +
            self.task_weights.get("systemic_hypertension", 0.5) * loss_ht +
            self.task_weights.get("dr_grade", 0.5) * loss_dr
        )

        if torch.isnan(total_loss) or torch.isinf(total_loss):
            raise FloatingPointError("Loss diverged to NaN or Inf during forward computation!")

        breakdown = {
            "total_loss": float(total_loss.item()),
            "loss_vd": float(loss_vd.item()),
            "loss_ht": float(loss_ht.item()),
            "loss_dr": float(loss_dr.item()),
        }

        return total_loss, breakdown
