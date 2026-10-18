"""
CareConnect Retinal AI: Standalone Inference Module
===================================================
- Independent, decoupled inference engine.
- Loads PyTorch checkpoint locally on CPU (no external weight downloading).
- Strictly deterministic preprocessing matching validation transforms.
- Bounded probabilities, explicit thresholds, and clinical safety notices.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as T

import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.models import CareConnectMultiTaskNet, DR_CLASSES


class CareConnectPredictor:
    """
    Inference controller managing fundus preprocessing, neural forward pass,
    thresholding, and clinical output formatting.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        config_path: Optional[Union[str, Path]] = None,
        device: str = "cpu",
    ):
        self.device = torch.device(device)

        # 1. Config
        if config_path is None:
            self.config_path = PROJECT_ROOT / "ml" / "configs" / "config.json"
        else:
            self.config_path = Path(config_path)

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {}

        data_cfg = self.config.get("data", {})
        self.image_size = data_cfg.get("image_size", 224)
        self.mean = data_cfg.get("mean", [0.485, 0.456, 0.406])
        self.std = data_cfg.get("std", [0.229, 0.224, 0.225])

        # 2. Decision Thresholds (Default to 0.50 if not specified)
        self.vd_threshold = 0.50
        self.ht_threshold = 0.50

        # 3. Transforms
        self.transform = T.Compose([
            T.Resize((self.image_size, self.image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
            T.ToTensor(),
            T.Normalize(mean=self.mean, std=self.std),
        ])

        # 4. Model & Weights
        if checkpoint_path is None:
            # Try best trained or baseline checkpoint
            candidates = [
                PROJECT_ROOT / "ml" / "checkpoints" / "mbrset" / "best_model.pt",
                PROJECT_ROOT / "ml" / "checkpoints" / "baseline" / "best_efficientnet_b0_baseline.pt",
                PROJECT_ROOT / "cvd-ai-service" / "models" / "best_model.pt",
            ]
            self.checkpoint_path = None
            for c in candidates:
                if c.exists():
                    self.checkpoint_path = c
                    break
            if self.checkpoint_path is None:
                raise FileNotFoundError(f"No checkpoint found in candidate locations: {candidates}")
        else:
            self.checkpoint_path = Path(checkpoint_path)
            if not self.checkpoint_path.exists():
                raise FileNotFoundError(f"Checkpoint not found at {self.checkpoint_path}")

        # Initialize network offline
        self.model = CareConnectMultiTaskNet(pretrained=False).to(self.device)

        ckpt = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        state_dict = ckpt.get("model_state_dict", ckpt)

        # Handle potential key prefixes
        cleaned_state = {}
        for k, v in state_dict.items():
            clean_k = k.replace("module.", "")
            # Adapt legacy head names if necessary
            if clean_k == "head_cvd.weight":
                clean_k = "head_vd.weight"
            elif clean_k == "head_cvd.bias":
                clean_k = "head_vd.bias"
            cleaned_state[clean_k] = v

        missing, unexpected = self.model.load_state_dict(cleaned_state, strict=False)
        self.model.eval()

    def preprocess_image(self, image_input: Union[str, Path, np.ndarray, Image.Image]) -> torch.Tensor:
        """Validate input and return normalized (1, 3, H, W) tensor."""
        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                raise FileNotFoundError(f"Image not found at {p}")
            with Image.open(p) as im:
                img_rgb = im.convert("RGB")
        elif isinstance(image_input, np.ndarray):
            img_rgb = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img_rgb = image_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        tensor = self.transform(img_rgb)
        return tensor.unsqueeze(0).to(self.device)

    @torch.no_grad()
    def predict(self, image_input: Union[str, Path, np.ndarray, Image.Image]) -> Dict[str, Any]:
        """Run multi-task forward pass and return structured predictions."""
        x = self.preprocess_image(image_input)
        logits = self.model(x)

        p_vd = float(torch.sigmoid(logits["vascular_disease"]).cpu().item())
        p_ht = float(torch.sigmoid(logits["systemic_hypertension"]).cpu().item())
        p_dr_arr = torch.softmax(logits["dr_grade"], dim=-1).cpu().squeeze(0).numpy()

        vd_pred = "Positive" if p_vd >= self.vd_threshold else "Negative"
        ht_pred = "Positive" if p_ht >= self.ht_threshold else "Negative"

        top_dr_idx = int(np.argmax(p_dr_arr))
        dr_grade_name = DR_CLASSES[top_dr_idx] if top_dr_idx < len(DR_CLASSES) else f"Grade {top_dr_idx}"
        dr_conf = float(p_dr_arr[top_dr_idx])

        dr_probs_dict = {DR_CLASSES[i]: float(p_dr_arr[i]) for i in range(len(DR_CLASSES))}

        return {
            "vascular_disease_probability": round(p_vd, 4),
            "vascular_disease_prediction": vd_pred,
            "vascular_disease_threshold": self.vd_threshold,
            "hypertension_probability": round(p_ht, 4),
            "hypertension_prediction": ht_pred,
            "hypertension_threshold": self.ht_threshold,
            "dr_predicted_grade": dr_grade_name,
            "dr_confidence": round(dr_conf, 4),
            "dr_probabilities": dr_probs_dict,
            "model_checkpoint": str(self.checkpoint_path),
            "disclaimer": "RESEARCH PROTOTYPE ONLY: Predictions are model-generated screening estimates, not a clinical diagnosis.",
        }
