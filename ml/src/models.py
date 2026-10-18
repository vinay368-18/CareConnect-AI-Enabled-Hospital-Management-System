"""
CareConnect Retinal AI: Model Architecture Module
=================================================
Multi-Task EfficientNet-B0 with dedicated heads for:
- vascular_disease (Primary CVD target, binary logit)
- systemic_hypertension (Binary logit)
- dr_grade (5-class ICDR Diabetic Retinopathy logits)
Optional tabular clinical MLP feature fusion branch.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights


DR_CLASSES = ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]


class CareConnectMultiTaskNet(nn.Module):
    """
    Multi-Task Deep Convolutional Network for Retinal Risk Screening.
    Backbone: EfficientNet-B0 feature extractor (1,280 features).
    """

    def __init__(
        self,
        pretrained: bool = True,
        dropout: float = 0.4,
        clinical_dim: int = 0,
        clinical_hidden: int = 32,
        clinical_dropout: float = 0.2,
        num_dr_classes: int = 5,
    ):
        super().__init__()
        self.clinical_dim = clinical_dim
        self.num_dr_classes = num_dr_classes

        # Backbone
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        base = efficientnet_b0(weights=weights)
        self.features = base.features
        self.avgpool = base.avgpool
        self.dropout = nn.Dropout(p=dropout)

        feature_dim = 1280

        # Optional clinical fusion
        if clinical_dim > 0:
            self.clinical_mlp = nn.Sequential(
                nn.Linear(clinical_dim, clinical_hidden),
                nn.ReLU(inplace=True),
                nn.Dropout(p=clinical_dropout),
            )
            total_feature_dim = feature_dim + clinical_hidden
        else:
            self.clinical_mlp = None
            total_feature_dim = feature_dim

        # Multi-task heads
        self.head_vd = nn.Linear(total_feature_dim, 1)
        self.head_ht = nn.Linear(total_feature_dim, 1)
        self.head_dr = nn.Linear(total_feature_dim, num_dr_classes)

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

    @torch.no_grad()
    def predict_probabilities(
        self,
        x: torch.Tensor,
        c: Optional[torch.Tensor] = None,
    ) -> Dict[str, Any]:
        """Inference helper returning bounded probabilities."""
        self.eval()
        logits = self.forward(x, c)

        p_vd = torch.sigmoid(logits["vascular_disease"]).cpu().numpy()
        p_ht = torch.sigmoid(logits["systemic_hypertension"]).cpu().numpy()
        p_dr = F.softmax(logits["dr_grade"], dim=-1).cpu().numpy()

        return {
            "vascular_disease_prob": p_vd,
            "systemic_hypertension_prob": p_ht,
            "dr_probabilities": p_dr,
        }
