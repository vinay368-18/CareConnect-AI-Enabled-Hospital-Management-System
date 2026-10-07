"""
Independent Inference Module for Retinal Multi-Task Disease Detection.
Decoupled completely from UI code.
Loads trained PyTorch model on CPU without downloading external weights.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from torchvision.models import efficientnet_b0


class MultiTaskNet(nn.Module):
    """
    EfficientNet-B0 backbone with 3 task heads:
    - head_cvd: 1 output (binary logit)
    - head_ht: 1 output (binary logit)
    - head_dr: 5 outputs (ICDR grades 0-4)
    """

    def __init__(self, num_dr_classes: int = 5, dropout: float = 0.4):
        super().__init__()
        # Pretrained=False to ensure fully offline loading without internet access
        base = efficientnet_b0(weights=None)
        self.features = base.features
        self.avgpool = base.avgpool
        self.dropout = nn.Dropout(p=dropout)

        feature_dim = 1280
        self.head_cvd = nn.Linear(feature_dim, 1)
        self.head_ht = nn.Linear(feature_dim, 1)
        self.head_dr = nn.Linear(feature_dim, num_dr_classes)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feats = self.features(x)
        pooled = self.avgpool(feats).flatten(1)
        dropped = self.dropout(pooled)

        return {
            "cvd": self.head_cvd(dropped).squeeze(-1),
            "hypertension": self.head_ht(dropped).squeeze(-1),
            "dr": self.head_dr(dropped),
        }


class RetinalPredictor:
    """
    Inference controller managing image preprocessing, model execution,
    thresholding, and output formatting.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.base_dir = Path(__file__).resolve().parent

        if config_path is None:
            self.config_path = self.base_dir / "config.json"
        else:
            self.config_path = Path(config_path)

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        m_cfg = self.config["model"]
        self.image_size = m_cfg.get("image_size", 224)
        self.mean = m_cfg.get("mean", [0.485, 0.456, 0.406])
        self.std = m_cfg.get("std", [0.229, 0.224, 0.225])
        self.dr_classes = m_cfg.get("dr_classes", ["No DR", "Mild", "Moderate", "Severe", "Proliferative"])

        # Thresholds
        t_cfg = self.config.get("thresholds", {})
        self.ht_threshold = float(t_cfg.get("hypertension", {}).get("value", 0.50))
        self.ht_threshold_source = t_cfg.get("hypertension", {}).get("source", "default threshold")

        self.cvd_threshold = float(t_cfg.get("cvd", {}).get("value", 0.50))
        self.cvd_threshold_source = t_cfg.get("cvd", {}).get("source", "default threshold")

        dr_conf_cfg = t_cfg.get("dr_confidence", {})
        self.dr_min_top_prob = float(dr_conf_cfg.get("min_top_probability", 0.50))
        self.dr_min_margin = float(dr_conf_cfg.get("min_margin", 0.15))

        # Badges
        b_cfg = self.config.get("reliability_badges", {})
        self.cvd_reliability_badge = b_cfg.get(
            "cvd", "Low reliability: image-only discriminative performance is near chance (~0.56 AUC in held-out test cohort)."
        )

        # Build transform pipeline (strictly deterministic, matching training validation transforms)
        self.transform = T.Compose([
            T.Resize((self.image_size, self.image_size), interpolation=T.InterpolationMode.BILINEAR, antialias=True),
            T.ToTensor(),
            T.Normalize(mean=self.mean, std=self.std),
        ])

        # Load weights
        weights_rel = m_cfg.get("weights_file", "models/best_model.pt")
        self.weights_path = (self.base_dir / weights_rel).resolve()
        if not self.weights_path.exists():
            raise FileNotFoundError(f"Model weight file not found: {self.weights_path}")

        self.device = torch.device("cpu")
        self.model = MultiTaskNet(num_dr_classes=len(self.dr_classes), dropout=0.4)

        checkpoint = torch.load(self.weights_path, map_location="cpu", weights_only=False)
        state_dict = checkpoint.get("model_state_dict", checkpoint)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    def preprocess_image(self, image_input: Union[str, Path, np.ndarray, Image.Image]) -> torch.Tensor:
        """
        Convert file path, numpy array, or PIL Image into normalized (1, 3, H, W) tensor.
        """
        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.exists():
                raise FileNotFoundError(f"Image not found at {path}")
            with Image.open(path) as im:
                img_rgb = im.convert("RGB")
        elif isinstance(image_input, np.ndarray):
            if image_input.ndim == 2:
                img_rgb = Image.fromarray(image_input).convert("RGB")
            elif image_input.ndim == 3:
                img_rgb = Image.fromarray(image_input).convert("RGB")
            else:
                raise ValueError(f"Invalid numpy array dimension: {image_input.ndim}")
        elif isinstance(image_input, Image.Image):
            img_rgb = image_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        tensor = self.transform(img_rgb)
        return tensor.unsqueeze(0)  # Shape: (1, 3, H, W)

    @torch.no_grad()
    def predict(self, image_input: Union[str, Path, np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Run forward pass on fundus image and return structured prediction dictionary.
        """
        x = self.preprocess_image(image_input).to(self.device)
        logits = self.model(x)

        p_cvd = float(torch.sigmoid(logits["cvd"]).cpu().item())
        p_ht = float(torch.sigmoid(logits["hypertension"]).cpu().item())
        p_dr_arr = F.softmax(logits["dr"], dim=-1).cpu().squeeze(0).numpy()

        # Decision thresholding
        ht_pred = "Positive" if p_ht >= self.ht_threshold else "Negative"
        cvd_pred = "Positive" if p_cvd >= self.cvd_threshold else "Negative"

        # DR Confidence & Grade
        sorted_indices = np.argsort(p_dr_arr)[::-1]
        top_idx = int(sorted_indices[0])
        second_idx = int(sorted_indices[1])

        top_prob = float(p_dr_arr[top_idx])
        second_prob = float(p_dr_arr[second_idx])
        margin = top_prob - second_prob

        dr_class = self.dr_classes[top_idx] if top_idx < len(self.dr_classes) else f"Grade {top_idx}"

        dr_low_confidence = (top_prob < self.dr_min_top_prob) or (margin < self.dr_min_margin)
        dr_badge = (
            f"Low confidence (top class {top_prob*100:.1f}%, margin {margin*100:.1f}%)"
            if dr_low_confidence
            else None
        )

        dr_prob_dict = {
            self.dr_classes[i]: float(p_dr_arr[i])
            for i in range(len(self.dr_classes))
        }

        return {
            # Systemic Hypertension
            "hypertension_predicted_probability": p_ht,
            "hypertension_threshold": self.ht_threshold,
            "hypertension_threshold_source": self.ht_threshold_source,
            "hypertension_prediction": ht_pred,

            # Cardiovascular Disease
            "cvd_predicted_probability": p_cvd,
            "cvd_threshold": self.cvd_threshold,
            "cvd_threshold_source": self.cvd_threshold_source,
            "cvd_prediction": cvd_pred,
            "cvd_reliability_badge": self.cvd_reliability_badge,

            # Diabetic Retinopathy
            "dr_predicted_grade": dr_class,
            "dr_confidence": top_prob,
            "dr_confidence_badge": dr_badge,
            "dr_probabilities": dr_prob_dict,
        }


# Global singleton instance
_GLOBAL_PREDICTOR: Optional[RetinalPredictor] = None


def get_predictor() -> RetinalPredictor:
    """Return initialized predictor instance."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None:
        _GLOBAL_PREDICTOR = RetinalPredictor()
    return _GLOBAL_PREDICTOR


def predict_image(image_input: Union[str, Path, np.ndarray, Image.Image]) -> Dict[str, Any]:
    """Public convenience function."""
    return get_predictor().predict(image_input)
