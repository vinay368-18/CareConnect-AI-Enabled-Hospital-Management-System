"""
CareConnect Retinal AI: Model Training Pipeline
===============================================
- Multi-task training for pure vascular_disease, systemic_hypertension, and dr_grade.
- Resolves all paths relative to project root.
- Strict isolation: validation and test splits are NEVER accessed for gradient updates.
- Imbalance class weighting calculated strictly from training data.
- Supports smoke-test mode for fast verification.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.dataset import CareConnectFundusDataset, get_inference_transforms, get_train_transforms
from ml.src.losses import CareConnectMultiTaskLoss, compute_training_class_weights
from ml.src.metrics import aggregate_patient_predictions, compute_binary_metrics, compute_dr_metrics
from ml.src.models import CareConnectMultiTaskNet


def resolve_image_dir(data_root: Optional[Path]) -> Path:
    """Find images directory from local or provided data root."""
    if data_root and (data_root / "images").exists():
        return data_root / "images"

    # Search standard paths
    candidates = [
        Path(r"C:\Users\vinay\CVD Project\mbrset-a-mobile-brazilian-retinal-dataset-1.0-20261001T140750Z-1-001\mbrset-a-mobile-brazilian-retinal-dataset-1.0\images"),
        PROJECT_ROOT / "ml" / "datasets" / "images",
    ]
    for c in candidates:
        if c.exists():
            return c

    # Search for any images folder
    found = list(Path(r"C:\Users\vinay").rglob("labels_mbrset.csv"))
    if found:
        img_p = found[0].parent / "images"
        if img_p.exists():
            return img_p

    raise FileNotFoundError("Could not locate mBRSET images directory.")


def train_one_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    criterion: CareConnectMultiTaskLoss,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> Dict[str, float]:
    """Train for a single epoch with finite loss and valid gradient assertions."""
    model.train()
    total_loss = 0.0
    total_vd_loss = 0.0
    total_ht_loss = 0.0
    total_dr_loss = 0.0
    count = 0

    for batch in loader:
        images = batch["image"].to(device)
        targets = {k: v.to(device) for k, v in batch["targets"].items()}
        masks = {k: v.to(device) for k, v in batch["masks"].items()}

        optimizer.zero_grad()
        logits = model(images)

        loss, breakdown = criterion(logits, targets, masks)

        # Verification: finite loss
        if not torch.isfinite(loss):
            raise FloatingPointError(f"Non-finite loss encountered: {loss.item()}")

        loss.backward()

        # Verification: valid gradients exist
        has_valid_grad = False
        for param in model.parameters():
            if param.grad is not None and torch.isfinite(param.grad).all():
                has_valid_grad = True
                break
        if not has_valid_grad:
            raise RuntimeError("Backward pass completed but no valid finite gradients were found!")

        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()

        b_size = images.size(0)
        total_loss += breakdown["total_loss"] * b_size
        total_vd_loss += breakdown["loss_vd"] * b_size
        total_ht_loss += breakdown["loss_ht"] * b_size
        total_dr_loss += breakdown["loss_dr"] * b_size
        count += b_size

    n = max(count, 1)
    return {
        "train_loss": total_loss / n,
        "train_vd_loss": total_vd_loss / n,
        "train_ht_loss": total_ht_loss / n,
        "train_dr_loss": total_dr_loss / n,
    }


@torch.no_grad()
def evaluate_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    criterion: CareConnectMultiTaskLoss,
    device: torch.device,
) -> Dict[str, Any]:
    """Evaluate on validation cohort without gradient updates."""
    model.eval()
    total_loss = 0.0
    count = 0

    all_vd_probs, all_ht_probs, all_dr_preds = [], [], []
    all_vd_true, all_ht_true, all_dr_true = [], [], []
    all_patients, all_files = [], []

    for batch in loader:
        images = batch["image"].to(device)
        targets = {k: v.to(device) for k, v in batch["targets"].items()}
        masks = {k: v.to(device) for k, v in batch["masks"].items()}

        logits = model(images)
        loss, breakdown = criterion(logits, targets, masks)

        b_size = images.size(0)
        total_loss += breakdown["total_loss"] * b_size
        count += b_size

        vd_p = torch.sigmoid(logits["vascular_disease"]).cpu().numpy()
        ht_p = torch.sigmoid(logits["systemic_hypertension"]).cpu().numpy()
        dr_pred = logits["dr_grade"].argmax(dim=-1).cpu().numpy()

        all_vd_probs.extend(vd_p.tolist() if vd_p.ndim > 0 else [float(vd_p)])
        all_ht_probs.extend(ht_p.tolist() if ht_p.ndim > 0 else [float(ht_p)])
        all_dr_preds.extend(dr_pred.tolist() if dr_pred.ndim > 0 else [int(dr_pred)])

        all_vd_true.extend(targets["vascular_disease"].cpu().numpy().tolist())
        all_ht_true.extend(targets["systemic_hypertension"].cpu().numpy().tolist())
        p_list = batch["metadata"]["patient"]
        all_patients.extend([int(p.item()) if isinstance(p, torch.Tensor) else int(p) for p in p_list])
        all_files.extend(batch["metadata"]["file"])

    val_loss = total_loss / max(count, 1)

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

    # Patient-level aggregation for vascular disease
    y_vd_true, y_vd_prob, _ = aggregate_patient_predictions(eval_df, "vd_prob", "vd_true")
    vd_metrics = compute_binary_metrics(y_vd_true, y_vd_prob, n_bootstraps=100)

    # Patient-level aggregation for HT
    y_ht_true, y_ht_prob, _ = aggregate_patient_predictions(eval_df, "ht_prob", "ht_true")
    ht_metrics = compute_binary_metrics(y_ht_true, y_ht_prob, n_bootstraps=100)

    # DR metrics
    dr_metrics = compute_dr_metrics(np.array(all_dr_true), np.array(all_dr_preds))

    return {
        "val_loss": val_loss,
        "vd_metrics": vd_metrics,
        "ht_metrics": ht_metrics,
        "dr_metrics": dr_metrics,
        "eval_df": eval_df,
    }


def run_training(
    config_path: Path,
    data_root: Optional[Path] = None,
    epochs_override: Optional[int] = None,
    batch_size_override: Optional[int] = None,
    smoke_test: bool = False,
) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Resolve paths relative to project root
    splits_dir = PROJECT_ROOT / config["data"]["splits_dir"]
    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"

    if not (train_csv.exists() and val_csv.exists()):
        raise FileNotFoundError(f"Split CSVs not found in {splits_dir}. Run prepare_data.py first.")

    train_df = pd.read_csv(train_csv)
    val_df = pd.read_csv(val_csv)

    images_dir = resolve_image_dir(data_root)

    # Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Train] Training Device: {device.type.upper()}")

    # Training parameters
    epochs = epochs_override or (2 if smoke_test else config["training"].get("epochs", 25))
    batch_size = batch_size_override or (4 if smoke_test else config["training"].get("batch_size", 16))

    if smoke_test:
        print("[Train] SMOKE TEST MODE: Subsetting to 16 train / 8 val samples.")
        train_df = train_df.head(16).copy()
        val_df = val_df.head(8).copy()

    # Create Datasets & Loaders
    image_size = config["data"].get("image_size", 224)
    train_dataset = CareConnectFundusDataset(train_df, images_dir=images_dir, is_training=True, image_size=image_size)
    val_dataset = CareConnectFundusDataset(val_df, images_dir=images_dir, is_training=False, image_size=image_size)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Model
    model = CareConnectMultiTaskNet(pretrained=config["model"].get("pretrained", True)).to(device)

    # Loss: compute class weights strictly on training dataframe
    weights = compute_training_class_weights(train_df)
    print(f"[Train] Computed Training Class Weights: VD={weights['vascular_disease']:.3f}, HT={weights['systemic_hypertension']:.3f}")

    criterion = CareConnectMultiTaskLoss(
        pos_weight_vd=weights["vascular_disease"],
        pos_weight_ht=weights["systemic_hypertension"],
        task_weights=config["training"].get("task_weights"),
        device=device,
    ).to(device)

    # Optimizer
    optimizer = torch.optim.AdamW(
        [
            {"params": model.features.parameters(), "lr": config["training"].get("learning_rate_backbone", 1e-4)},
            {"params": [p for n, p in model.named_parameters() if not n.startswith("features.")],
             "lr": config["training"].get("learning_rate_head", 1e-3)},
        ],
        weight_decay=config["training"].get("weight_decay", 1e-2),
    )

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1), eta_min=1e-6)

    # Checkpoint output directory
    checkpoints_dir = PROJECT_ROOT / config["outputs"]["checkpoints_dir"]
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    best_ckpt_path = PROJECT_ROOT / config["outputs"]["best_checkpoint"]
    last_ckpt_path = PROJECT_ROOT / config["outputs"]["last_checkpoint"]

    metrics_dir = PROJECT_ROOT / config["outputs"]["metrics_dir"]
    metrics_dir.mkdir(parents=True, exist_ok=True)

    history = []
    best_vd_auc = -1.0

    print("=" * 60)
    print(f"Starting Training: {epochs} Epochs | Batch Size: {batch_size}")
    print(f"Train images: {len(train_dataset)} | Val images: {len(val_dataset)}")
    print("=" * 60)

    for ep in range(1, epochs + 1):
        t0 = time.time()
        train_res = train_one_epoch(model, train_loader, criterion, optimizer, device)
        scheduler.step()
        val_res = evaluate_epoch(model, val_loader, criterion, device)
        elapsed = time.time() - t0

        vd_auc = val_res["vd_metrics"].get("roc_auc") or 0.5
        ht_auc = val_res["ht_metrics"].get("roc_auc") or 0.5
        dr_acc = val_res["dr_metrics"].get("accuracy") or 0.0

        rec = {
            "epoch": ep,
            "train_loss": train_res["train_loss"],
            "val_loss": val_res["val_loss"],
            "vd_roc_auc": vd_auc,
            "ht_roc_auc": ht_auc,
            "dr_accuracy": dr_acc,
            "elapsed_seconds": round(elapsed, 2),
        }
        history.append(rec)

        print(f"Epoch {ep:02d}/{epochs:02d} | Train Loss: {train_res['train_loss']:.4f} | "
              f"Val Loss: {val_res['val_loss']:.4f} | VD AUC: {vd_auc:.4f} | "
              f"HT AUC: {ht_auc:.4f} | DR Acc: {dr_acc:.4f} | ({elapsed:.1f}s)")

        # Save last checkpoint
        torch.save({
            "epoch": ep,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "config": config,
            "weights": weights,
        }, last_ckpt_path)

        # Save best checkpoint
        if vd_auc > best_vd_auc:
            best_vd_auc = vd_auc
            torch.save({
                "epoch": ep,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "config": config,
                "weights": weights,
                "val_metrics": val_res,
            }, best_ckpt_path)

    # Save training history
    history_df = pd.DataFrame(history)
    history_csv_path = metrics_dir / "training_history.csv"
    history_df.to_csv(history_csv_path, index=False)
    print(f"[Train] Saved training history: {history_csv_path}")
    print(f"[Train] Checkpoints saved to {checkpoints_dir}")

    return {
        "status": "success",
        "epochs_completed": epochs,
        "best_vd_auc": best_vd_auc,
        "history": history,
        "best_checkpoint": str(best_ckpt_path),
        "last_checkpoint": str(last_ckpt_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Train CareConnect Retinal AI")
    parser.add_argument("--config", type=str, default="ml/configs/config.json", help="Path to config JSON")
    parser.add_argument("--data-root", type=str, default=None, help="Optional data root override")
    parser.add_argument("--epochs", type=int, default=None, help="Epoch count override")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size override")
    parser.add_argument("--smoke-test", action="store_true", help="Run rapid smoke test")
    args = parser.parse_args()

    cfg_path = PROJECT_ROOT / args.config if not Path(args.config).is_absolute() else Path(args.config)
    data_root = Path(args.data_root) if args.data_root else None

    run_training(
        config_path=cfg_path,
        data_root=data_root,
        epochs_override=args.epochs,
        batch_size_override=args.batch_size,
        smoke_test=args.smoke_test,
    )


if __name__ == "__main__":
    main()
