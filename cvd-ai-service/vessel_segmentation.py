"""
Residual U-Net retinal vessel segmentation for the CareConnect AI service.

The architecture, pre-processing (green channel + CLAHE, applied per 256x256 patch)
and overlapping-tile inference are identical to the training notebook
(residual_unet_vessel_segmentation.ipynb), so the trained weights behave the same here.

Weights file: models/residual_unet_best.pt  (copy of residual_unet_green_clahe_best.pt from training)
"""
import threading
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

PATCH = 256          # training patch size
STRIDE = 128         # tile overlap used for inference (same as the notebook)
MAX_SIDE = 1024      # large photos are shrunk so the longer side is at most this (speed + similar vessel scale to training data)
THRESHOLD = 0.5
DEFAULT_WEIGHTS = Path(__file__).parent / "models" / "residual_unet_best.pt"


class ResBlock(nn.Module):
    """conv-BN-ReLU-conv-BN + shortcut -> ReLU (identical to the training notebook)."""

    def __init__(self, cin, cout):
        super().__init__()
        self.c1 = nn.Conv2d(cin, cout, 3, padding=1, bias=False)
        self.b1 = nn.BatchNorm2d(cout)
        self.c2 = nn.Conv2d(cout, cout, 3, padding=1, bias=False)
        self.b2 = nn.BatchNorm2d(cout)
        self.sc = nn.Identity() if cin == cout else nn.Sequential(
            nn.Conv2d(cin, cout, 1, bias=False), nn.BatchNorm2d(cout))

    def forward(self, x):
        o = F.relu(self.b1(self.c1(x)))
        o = self.b2(self.c2(o))
        return F.relu(o + self.sc(x))


class ResUNet(nn.Module):
    def __init__(self, in_ch=1, base=32, depth=4):
        super().__init__()
        f = [base * 2 ** i for i in range(depth + 1)]
        self.enc = nn.ModuleList([ResBlock(in_ch, f[0])] + [ResBlock(f[i], f[i + 1]) for i in range(depth)])
        self.pool = nn.MaxPool2d(2)
        self.up = nn.ModuleList([nn.ConvTranspose2d(f[i + 1], f[i], 2, stride=2) for i in reversed(range(depth))])
        self.dec = nn.ModuleList([ResBlock(f[i] * 2, f[i]) for i in reversed(range(depth))])
        self.out = nn.Conv2d(f[0], 1, 1)

    def forward(self, x):
        skips = []
        x = self.enc[0](x)
        skips.append(x)
        for e in self.enc[1:-1]:
            x = e(self.pool(x))
            skips.append(x)
        x = self.enc[-1](self.pool(x))
        for up, dec, sk in zip(self.up, self.dec, reversed(skips)):
            x = dec(torch.cat([up(x), sk], 1))
        return self.out(x)  # raw logits


def _positions(length: int):
    pos = list(range(0, length - PATCH + 1, STRIDE))
    if pos[-1] != length - PATCH:
        pos.append(length - PATCH)
    return pos


class VesselSegmenter:
    def __init__(self, weights_path: Optional[str] = None, device: str = "cpu", max_side: int = MAX_SIDE):
        path = Path(weights_path) if weights_path else DEFAULT_WEIGHTS
        if not path.exists():
            raise FileNotFoundError(f"Vessel model weights not found: {path}")
        ck = torch.load(path, map_location=device, weights_only=True)
        if ck.get("preproc", "green_clahe") != "green_clahe":
            raise ValueError("These weights were not trained with green_clahe pre-processing.")
        self.device = torch.device(device)
        self.max_side = max_side
        self.model = ResUNet(1, int(ck.get("base", 32))).to(self.device)
        self.model.load_state_dict(ck["model"])
        self.model.eval()
        self._lock = threading.Lock()   # one image at a time (CPU friendly; also CLAHE objects are not thread-safe)

    # ---------------------------------------------------------------- helpers
    def _prepare(self, image: Image.Image) -> np.ndarray:
        rgb = np.array(image.convert("RGB"))
        h, w = rgb.shape[:2]
        scale = self.max_side / max(h, w)
        if scale < 1.0:
            rgb = cv2.resize(rgb, (int(round(w * scale)), int(round(h * scale))), interpolation=cv2.INTER_AREA)
        return rgb

    @staticmethod
    def _fov_mask(rgb: np.ndarray) -> np.ndarray:
        """Circular retina region (the black border around the photo is excluded)."""
        gray = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (0, 0), 3)
        fov = (gray > 12).astype(np.uint8)
        fov = cv2.morphologyEx(fov, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(fov)
        if n > 1:
            fov = (labels == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
        fov = cv2.erode(fov, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        return fov.astype(bool)

    @torch.no_grad()
    def _probability_map(self, rgb: np.ndarray, batch: int = 8) -> np.ndarray:
        h, w = rgb.shape[:2]
        ph, pw = max(0, PATCH - h), max(0, PATCH - w)
        if ph or pw:
            rgb = np.pad(rgb, ((0, ph), (0, pw), (0, 0)), mode="reflect")
        hh, ww = rgb.shape[:2]
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        coords = [(y, x) for y in _positions(hh) for x in _positions(ww)]
        acc = np.zeros((hh, ww), np.float32)
        cnt = np.zeros((hh, ww), np.float32)
        for i in range(0, len(coords), batch):
            cs = coords[i:i + batch]
            tiles = np.stack([clahe.apply(np.ascontiguousarray(rgb[y:y + PATCH, x:x + PATCH, 1])) for y, x in cs])
            xb = torch.from_numpy(tiles.astype(np.float32) / 255.0)[:, None].to(self.device)
            pr = torch.sigmoid(self.model(xb))[:, 0].cpu().numpy()
            for (y, x), p in zip(cs, pr):
                acc[y:y + PATCH, x:x + PATCH] += p
                cnt[y:y + PATCH, x:x + PATCH] += 1
        return (acc / cnt)[:h, :w]

    @staticmethod
    def _overlay_png(rgb: np.ndarray, vessels: np.ndarray) -> bytes:
        out = rgb.astype(np.float32)
        colour = np.array([0, 255, 160], np.float32)
        out[vessels] = 0.2 * out[vessels] + 0.8 * colour
        ok, buf = cv2.imencode(".png", cv2.cvtColor(out.astype(np.uint8), cv2.COLOR_RGB2BGR))
        if not ok:
            raise RuntimeError("PNG encoding failed")
        return buf.tobytes()

    # ------------------------------------------------------------------ API
    def segment(self, image: Image.Image) -> Dict:
        with self._lock:
            rgb = self._prepare(image)
            prob = self._probability_map(rgb)
            fov = self._fov_mask(rgb)
            vessels = (prob >= THRESHOLD) & fov
            density = float(vessels.sum() / max(1, fov.sum()) * 100.0)
            return {
                "overlay_png": self._overlay_png(rgb, vessels),
                "vessel_density": density,     # % of the retinal area classified as vessel
                "size": (rgb.shape[1], rgb.shape[0]),
            }
