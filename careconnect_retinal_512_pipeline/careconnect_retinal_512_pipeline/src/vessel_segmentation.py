"""512x512 working-image segmentation via overlapping patches.

Connect the exact Residual U-Net class and checkpoint used by your project.
This wrapper assumes a one-channel grayscale input normalized to [0,1] and a
single-channel logits/probability output; adapt to match the model's training.
"""
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
from retinal_preprocess import preprocess_green_clahe, retinal_fov_mask

@dataclass
class SegmentationConfig:
    working_size: int = 512
    patch_size: int = 256
    stride: int = 128
    threshold: float = 0.5
    clahe_clip_limit: float = 2.0
    clahe_grid: tuple = (8, 8)
    device: str | None = None

def patch_starts(length, patch, stride):
    if patch > length:
        raise ValueError("patch size cannot exceed image size")
    if stride < 1 or stride > patch:
        raise ValueError("stride must be between 1 and patch size")
    starts = list(range(0, length - patch + 1, stride))
    if starts[-1] != length - patch:
        starts.append(length - patch)
    return starts

def _predict_patch(model, patch, device):
    x = torch.from_numpy(patch.astype(np.float32) / 255.0)[None, None].to(device)
    with torch.no_grad():
        y = model(x)
        if isinstance(y, (tuple, list)):
            y = y[0]
        if y.ndim == 3:
            y = y[:, None]
        if y.ndim != 4 or y.shape[:2] != (1, 1):
            raise ValueError(f"Expected output (1,1,H,W), got {tuple(y.shape)}")
        if y.min().item() < 0 or y.max().item() > 1:
            y = torch.sigmoid(y)
        y = torch.nn.functional.interpolate(y, size=patch.shape, mode="bilinear", align_corners=False)
        return y[0, 0].detach().cpu().numpy()

def segment_vessels(image, model: nn.Module, config=SegmentationConfig()):
    if config.working_size != 512:
        raise ValueError("working_size must be 512 for this workflow")
    rgb, clahe = preprocess_green_clahe(
        image, size=512, clip_limit=config.clahe_clip_limit, tile_grid=config.clahe_grid
    )
    device = torch.device(config.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = model.to(device).eval()
    h, w = clahe.shape
    sums = np.zeros((h, w), np.float32)
    counts = np.zeros((h, w), np.float32)
    for y0 in patch_starts(h, config.patch_size, config.stride):
        for x0 in patch_starts(w, config.patch_size, config.stride):
            patch = clahe[y0:y0+config.patch_size, x0:x0+config.patch_size]
            probs = _predict_patch(model, patch, device)
            sums[y0:y0+config.patch_size, x0:x0+config.patch_size] += probs
            counts[y0:y0+config.patch_size, x0:x0+config.patch_size] += 1
    probability = sums / np.maximum(counts, 1)
    mask = probability >= config.threshold
    fov = retinal_fov_mask(rgb)
    density = float((mask & fov).sum() / fov.sum() * 100) if fov.any() else 0.0
    overlay = np.zeros((h, w, 4), np.uint8)
    overlay[mask] = [0, 255, 255, 180]
    return {
        "rgb_512": rgb, "green_clahe_512": clahe,
        "probability_map_512": probability,
        "vessel_mask_512": mask.astype(np.uint8) * 255,
        "overlay_rgba_512": overlay,
        "vessel_density_percent": density, "device": str(device)
    }
