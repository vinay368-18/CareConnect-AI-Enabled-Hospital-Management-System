"""
CareConnect Retinal AI: PyTorch Dataset & Transforms Module
===========================================================
- Self-contained, portable dataset loader.
- Resolves relative image paths against configurable data roots.
- Provides strict training (augmented) and inference (deterministic) transforms.
- Returns targets with masking vectors to prevent missing labels from updating gradients.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms(
    image_size: int = 224,
    mean: List[float] = IMAGENET_MEAN,
    std: List[float] = IMAGENET_STD,
    rotation_degrees: int = 15,
) -> T.Compose:
    """Stochastic image augmentations applied strictly during training."""
    return T.Compose([
        T.Resize((image_size, image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomVerticalFlip(p=0.2),
        T.RandomRotation(degrees=rotation_degrees),
        T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
        T.ToTensor(),
        T.Normalize(mean=mean, std=std),
    ])


def get_inference_transforms(
    image_size: int = 224,
    mean: List[float] = IMAGENET_MEAN,
    std: List[float] = IMAGENET_STD,
) -> T.Compose:
    """Deterministic transforms applied during validation, testing, and inference."""
    return T.Compose([
        T.Resize((image_size, image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
        T.ToTensor(),
        T.Normalize(mean=mean, std=std),
    ])


class CareConnectFundusDataset(Dataset):
    """
    Multi-task PyTorch Dataset for retinal fundus images.
    Returns:
        image: Tensor of shape (3, H, W)
        targets: dict with 'vascular_disease', 'systemic_hypertension', 'dr_grade'
        masks: dict with 1.0 for valid supervision, 0.0 for missing/masked labels
        metadata: dict with 'patient', 'file', 'index'
    """

    def __init__(
        self,
        df: pd.DataFrame,
        images_dir: Union[str, Path],
        transform: Optional[Callable] = None,
        is_training: bool = False,
        image_size: int = 224,
    ):
        self.df = df.reset_index(drop=True)
        self.images_dir = Path(images_dir)
        self.is_training = is_training

        if transform is not None:
            self.transform = transform
        else:
            self.transform = get_train_transforms(image_size) if is_training else get_inference_transforms(image_size)

        # Precompute targets and masks
        # Primary Target: vascular_disease (0 or 1, or -1 for missing)
        vd_vals = pd.to_numeric(self.df.get("vascular_disease", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.vd_targets = np.where(np.isin(vd_vals, [0, 1]), vd_vals, -1).astype(np.float32)
        self.vd_masks = (self.vd_targets >= 0).astype(np.float32)

        # Secondary Target: systemic_hypertension (0 or 1, or -1 for missing)
        ht_vals = pd.to_numeric(self.df.get("systemic_hypertension", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.ht_targets = np.where(np.isin(ht_vals, [0, 1]), ht_vals, -1).astype(np.float32)
        self.ht_masks = (self.ht_targets >= 0).astype(np.float32)

        # Secondary Target: dr_grade (0, 1, 2, 3, 4, or -1 for missing)
        dr_vals = pd.to_numeric(self.df.get("dr_grade", pd.Series([-1] * len(self.df))), errors="coerce").fillna(-1).values
        self.dr_targets = np.where(np.isin(dr_vals, [0, 1, 2, 3, 4]), dr_vals, -1).astype(np.int64)
        self.dr_masks = (self.dr_targets >= 0).astype(np.float32)

        self.files = self.df["file"].values
        self.patients = self.df["patient"].values

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        fname = self.files[idx]
        img_path = self.images_dir / fname

        if not img_path.exists():
            # Try searching by relative path if present
            rel = self.df.iloc[idx].get("relative_path")
            if rel and (self.images_dir.parent / rel).exists():
                img_path = self.images_dir.parent / rel
            else:
                raise FileNotFoundError(f"Image not found at {img_path}")

        try:
            with Image.open(img_path) as im:
                image_rgb = im.convert("RGB")
        except Exception as e:
            raise IOError(f"Failed to load image at {img_path}: {e}")

        image_tensor = self.transform(image_rgb)

        return {
            "image": image_tensor,
            "targets": {
                "vascular_disease": torch.tensor(max(self.vd_targets[idx], 0.0), dtype=torch.float32),
                "systemic_hypertension": torch.tensor(max(self.ht_targets[idx], 0.0), dtype=torch.float32),
                "dr_grade": torch.tensor(max(self.dr_targets[idx], 0), dtype=torch.long),
            },
            "masks": {
                "vascular_disease": torch.tensor(self.vd_masks[idx], dtype=torch.float32),
                "systemic_hypertension": torch.tensor(self.ht_masks[idx], dtype=torch.float32),
                "dr_grade": torch.tensor(self.dr_masks[idx], dtype=torch.float32),
            },
            "metadata": {
                "patient": int(self.patients[idx]),
                "file": fname,
                "index": idx,
            },
        }
