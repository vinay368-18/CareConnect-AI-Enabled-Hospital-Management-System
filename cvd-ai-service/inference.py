"""
CareConnect Retinal AI: Independent Inference Engine
===================================================
Loads verified MultiTask EfficientNet-B0 (Experiment B) checkpoint on CPU.
Executes deterministic preprocessing matching training validation transforms.
Produces continuous prediction probabilities, validation-calibrated thresholds,
and mandatory clinical safety caveats.
"""

import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, UnidentifiedImageError
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from torchvision.transforms import InterpolationMode
from torchvision.models import efficientnet_b0

logger = logging.getLogger("cvd-inference")
logging.basicConfig(level=logging.INFO)

DR_CLASSES = ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]


class CareConnectMultiTaskNet(nn.Module):
    """
    Multi-Task Deep Convolutional Network for Retinal Risk Screening.
    Backbone: EfficientNet-B0 feature extractor (1,280 features).
    """

    def __init__(
        self,
        num_dr_classes: int = 5,
        dropout: float = 0.4,
    ):
        super().__init__()
        # Pretrained=False to ensure fully offline loading without internet access
        base = efficientnet_b0(weights=None)
        self.features = base.features
        self.avgpool = base.avgpool
        self.dropout = nn.Dropout(p=dropout)

        feature_dim = 1280
        self.head_vd = nn.Linear(feature_dim, 1)
        self.head_ht = nn.Linear(feature_dim, 1)
        self.head_dr = nn.Linear(feature_dim, num_dr_classes)

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.features(x)
        pooled = self.avgpool(feats).flatten(1)
        return self.dropout(pooled)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        f = self.extract_features(x)
        return {
            "vascular_disease": self.head_vd(f).squeeze(-1),
            "systemic_hypertension": self.head_ht(f).squeeze(-1),
            "dr_grade": self.head_dr(f),
        }


class RetinalPredictor:
    """
    Production inference controller managing preprocessing, PyTorch forward pass,
    threshold calibration, and clinical disclaimer attachment.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.base_dir = Path(__file__).resolve().parent

        if config_path is None:
            self.config_path = self.base_dir / "config.json"
        else:
            self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        m_cfg = self.config.get("model", {})
        self.image_size = int(m_cfg.get("image_size", 224))
        self.mean = m_cfg.get("mean", [0.485, 0.456, 0.406])
        self.std = m_cfg.get("std", [0.229, 0.224, 0.225])
        self.dr_classes = m_cfg.get("dr_classes", DR_CLASSES)

        # Thresholds (Frozen from mBRSET validation partition)
        t_cfg = self.config.get("thresholds", {})
        self.vd_threshold = float(t_cfg.get("vascular_disease", {}).get("value", 0.4996))
        self.ht_threshold = float(t_cfg.get("systemic_hypertension", {}).get("value", 0.4288))

        dr_conf_cfg = t_cfg.get("dr_confidence", {})
        self.dr_min_top_prob = float(dr_conf_cfg.get("min_top_probability", 0.50))
        self.dr_min_margin = float(dr_conf_cfg.get("min_margin", 0.15))

        # Build transform pipeline (identical to dataset.py validation transform)
        self.transform = T.Compose([
            T.Resize((self.image_size, self.image_size), interpolation=InterpolationMode.BILINEAR, antialias=True),
            T.ToTensor(),
            T.Normalize(mean=self.mean, std=self.std),
        ])

        # Resolve weights path
        weights_rel = m_cfg.get("weights_file", "models/best_model.pt")
        self.weights_path = (self.base_dir / weights_rel).resolve()
        if not self.weights_path.exists():
            # Fallback to ml/checkpoints if available
            alt_path = (self.base_dir.parent / "ml" / "checkpoints" / "mbrset" / "experiment_b_efficientnet_b0" / "best_model.pt").resolve()
            if alt_path.exists():
                self.weights_path = alt_path
            else:
                raise FileNotFoundError(f"Model weight file not found at: {self.weights_path}")

        self.device = torch.device("cpu")
        self.model = CareConnectMultiTaskNet(num_dr_classes=len(self.dr_classes), dropout=0.4)

        logger.info(f"Loading checkpoint weights from {self.weights_path}...")
        checkpoint = torch.load(self.weights_path, map_location="cpu", weights_only=False)
        state_dict = checkpoint.get("model_state_dict", checkpoint)

        # Harmonize state dict keys between training and inference
        cleaned_state = {}
        for k, v in state_dict.items():
            clean_k = k.replace("module.", "")
            if clean_k.startswith("head_cvd."):
                clean_k = clean_k.replace("head_cvd.", "head_vd.")
            cleaned_state[clean_k] = v

        self.model.load_state_dict(cleaned_state, strict=False)
        self.model.to(self.device)
        self.model.eval()
        logger.info("CareConnectMultiTaskNet model loaded successfully on CPU.")

    def preprocess_image(self, image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> torch.Tensor:
        """
        Validate and convert file path, raw bytes, numpy array, or PIL Image
        into normalized (1, 3, 224, 224) PyTorch tensor.
        """
        img_rgb: Image.Image

        if isinstance(image_input, (str, Path)):
            p = Path(image_input)
            if not p.exists():
                raise FileNotFoundError(f"Image not found at {p}")
            with Image.open(p) as im:
                img_rgb = im.convert("RGB")
        elif isinstance(image_input, bytes):
            try:
                with Image.open(io.BytesIO(image_input)) as im:
                    img_rgb = im.convert("RGB")
            except Exception as e:
                raise ValueError("Uploaded file is not a valid or readable image.") from e
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

        # Validate minimum dimensions to prevent corrupt or placeholder inputs
        w, h = img_rgb.size
        if w < 64 or h < 64:
            raise ValueError(f"Image dimensions ({w}x{h}) are too small for retinal analysis (minimum 64x64).")

        tensor = self.transform(img_rgb)
        return tensor.unsqueeze(0)  # Shape: (1, 3, H, W)

    @torch.no_grad()
    def predict(self, image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Run forward inference on retinal fundus image and return structured prediction dictionary.
        """
        x = self.preprocess_image(image_input).to(self.device)
        logits = self.model(x)

        p_vd = float(torch.sigmoid(logits["vascular_disease"]).cpu().item())
        p_ht = float(torch.sigmoid(logits["systemic_hypertension"]).cpu().item())
        p_dr_arr = F.softmax(logits["dr_grade"], dim=-1).cpu().squeeze(0).numpy()

        # Decision thresholding based on frozen validation threshold
        vd_pred = "Positive" if p_vd >= self.vd_threshold else "Negative"
        ht_pred = "Positive" if p_ht >= self.ht_threshold else "Negative"

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
            # Vascular Disease (Primary CVD Target)
            "cvd_predicted_probability": round(p_vd, 4),
            "cvd_threshold": self.vd_threshold,
            "cvd_prediction": vd_pred,
            "cvd_reliability_badge": "Low reliability: image-only discriminative performance on systemic vascular disease is near chance (Test ROC-AUC: 0.5202). Not a diagnostic test.",

            # Systemic Hypertension
            "hypertension_predicted_probability": round(p_ht, 4),
            "hypertension_threshold": self.ht_threshold,
            "hypertension_prediction": ht_pred,

            # Diabetic Retinopathy (Direct Ocular Finding - High Confidence)
            "dr_predicted_grade": dr_class,
            "dr_confidence": round(top_prob, 4),
            "dr_confidence_badge": dr_badge,
            "dr_probabilities": dr_prob_dict,

            # Clinical Safety & Caveats
            "experimental_flag": True,
            "clinical_caveats": (
                "Experimental research screening only. Retinal image-only models exhibit weak discrimination "
                "for systemic vascular disease (Test ROC-AUC: 0.5202; 95% CI: 0.3936–0.6416). Diabetic Retinopathy "
                "accuracy (76.99%) reflects direct ocular pathology and does NOT indicate cardiovascular disease accuracy. "
                "Attending physician review, standard blood pressure check, lipid profile, and 12-lead ECG are mandatory."
            ),
        }


# Global singleton instance
_GLOBAL_PREDICTOR: Optional[RetinalPredictor] = None


def get_predictor() -> RetinalPredictor:
    """Return initialized predictor instance."""
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None:
        _GLOBAL_PREDICTOR = RetinalPredictor()
    return _GLOBAL_PREDICTOR


def predict_image(image_input: Union[str, Path, bytes, np.ndarray, Image.Image]) -> Dict[str, Any]:
    """Public convenience function."""
    return get_predictor().predict(image_input)
