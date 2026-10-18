"""
CareConnect Retinal AI: Comprehensive Automated Test Suite
==========================================================
Tests:
1. File integrity & exclusion documentation
2. Target label mapping integrity (pure vascular_disease, no AMI conflation)
3. Duplicate image detection
4. Patient-level zero-leakage assertions
5. Split class distributions
6. Preprocessing pipeline consistency
7. Checkpoint loading & offline execution
8. End-to-end forward/backward gradient flow on a small batch
"""

import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.src.dataset import CareConnectFundusDataset, get_inference_transforms, get_train_transforms
from ml.src.losses import CareConnectMultiTaskLoss, compute_training_class_weights
from ml.src.models import CareConnectMultiTaskNet
from ml.src.predict import CareConnectPredictor


class TestCareConnectPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.splits_dir = PROJECT_ROOT / "ml" / "datasets" / "splits"
        cls.manifest_path = PROJECT_ROOT / "ml" / "datasets" / "dataset_manifest.csv"
        cls.exclusions_path = PROJECT_ROOT / "ml" / "datasets" / "audit_exclusions.csv"

        # Checkpoint path
        cls.ckpt_path = PROJECT_ROOT / "ml" / "checkpoints" / "baseline" / "best_efficientnet_b0_baseline.pt"
        if not cls.ckpt_path.exists():
            cls.ckpt_path = PROJECT_ROOT / "cvd-ai-service" / "models" / "best_model.pt"

        # Image dir
        candidates = [
            Path(r"C:\Users\vinay\CVD Project\mbrset-a-mobile-brazilian-retinal-dataset-1.0-20261001T140750Z-1-001\mbrset-a-mobile-brazilian-retinal-dataset-1.0\images"),
            PROJECT_ROOT / "ml" / "datasets" / "images",
        ]
        cls.images_dir = None
        for c in candidates:
            if c.exists():
                cls.images_dir = c
                break

    def test_01_manifest_and_exclusions_exist(self):
        """Verify manifest and exclusions report exist and are non-empty."""
        self.assertTrue(self.manifest_path.exists(), f"Missing {self.manifest_path}")
        self.assertTrue(self.exclusions_path.exists(), f"Missing {self.exclusions_path}")

        df_m = pd.read_csv(self.manifest_path)
        df_e = pd.read_csv(self.exclusions_path)

        self.assertGreater(len(df_m), 4000, "Manifest has fewer rows than expected.")
        self.assertGreater(len(df_e), 1000, "Exclusions report has fewer rows than expected.")

        # Every excluded row must have a documented reason
        self.assertTrue(df_e["detailed_reason"].notna().all(), "Some exclusions lack detailed reasons!")
        self.assertTrue(df_e["reason_code"].isin(["EXCL_NO_FILE", "EXCL_NO_LABEL"]).all(),
                        "Unknown exclusion reason code detected!")

    def test_02_split_files_exist_and_images_on_disk(self):
        """Verify that all files referenced in train, val, test splits exist on disk."""
        self.assertIsNotNone(self.images_dir, "Images directory not found for tests.")

        for s_name in ["train.csv", "val.csv", "test.csv"]:
            s_path = self.splits_dir / s_name
            self.assertTrue(s_path.exists(), f"Split file missing: {s_path}")

            df = pd.read_csv(s_path)
            self.assertGreater(len(df), 0, f"Split {s_name} is empty!")

            # Check a sample of 20 images from each split
            sample = df.sample(min(20, len(df)), random_state=42)
            for _, row in sample.iterrows():
                f_path = self.images_dir / row["file"]
                self.assertTrue(f_path.exists(), f"Referenced image not on disk: {f_path}")

    def test_03_zero_patient_leakage(self):
        """Enforce strict invariant: zero patient overlap between train, val, and test."""
        train_df = pd.read_csv(self.splits_dir / "train.csv")
        val_df = pd.read_csv(self.splits_dir / "val.csv")
        test_df = pd.read_csv(self.splits_dir / "test.csv")

        train_pts = set(train_df["patient"].unique())
        val_pts = set(val_df["patient"].unique())
        test_pts = set(test_df["patient"].unique())

        tv_overlap = train_pts & val_pts
        tt_overlap = train_pts & test_pts
        vt_overlap = val_pts & test_pts

        self.assertEqual(len(tv_overlap), 0, f"LEAKAGE: {len(tv_overlap)} patients in train and val!")
        self.assertEqual(len(tt_overlap), 0, f"LEAKAGE: {len(tt_overlap)} patients in train and test!")
        self.assertEqual(len(vt_overlap), 0, f"LEAKAGE: {len(vt_overlap)} patients in val and test!")

    def test_04_no_duplicate_images_in_partitions(self):
        """Verify that no image filename appears more than once across or within partitions."""
        train_df = pd.read_csv(self.splits_dir / "train.csv")
        val_df = pd.read_csv(self.splits_dir / "val.csv")
        test_df = pd.read_csv(self.splits_dir / "test.csv")

        all_files = list(train_df["file"]) + list(val_df["file"]) + list(test_df["file"])
        self.assertEqual(len(all_files), len(set(all_files)), "Duplicate image filenames found across splits!")

    def test_05_target_definitions_are_pure(self):
        """Verify that vascular_disease is strictly binary (0 or 1) and separate from AMI."""
        for s_name in ["train.csv", "val.csv", "test.csv"]:
            df = pd.read_csv(self.splits_dir / s_name)

            # Target must be strictly 0 or 1
            unique_targets = set(df["vascular_disease"].unique())
            self.assertTrue(unique_targets.issubset({0, 1}), f"Non-binary targets in {s_name}: {unique_targets}")

            # Verify AMI is kept distinct
            if "acute_myocardial_infarction" in df.columns:
                discrepancies = df[df["vascular_disease"] != df["acute_myocardial_infarction"]]
                # There should be cases where VD != AMI, confirming they are NOT conflated
                self.assertGreater(len(discrepancies), 0, f"AMI appears identical to VD in {s_name} - possible conflation!")

    def test_06_class_imbalance_weights_calculated_only_on_train(self):
        """Verify that compute_training_class_weights derives weights strictly from train_df."""
        train_df = pd.read_csv(self.splits_dir / "train.csv")
        weights = compute_training_class_weights(train_df)

        expected_vd_pos = (train_df["vascular_disease"] == 1).sum()
        expected_vd_neg = (train_df["vascular_disease"] == 0).sum()
        expected_weight = expected_vd_neg / max(expected_vd_pos, 1)

        self.assertAlmostEqual(weights["vascular_disease"], expected_weight, places=4)
        self.assertEqual(weights["n_train_vd_pos"], expected_vd_pos)
        self.assertEqual(weights["n_train_vd_neg"], expected_vd_neg)

    def test_07_preprocessing_consistency(self):
        """Verify image tensor shape, channels, and normalization boundaries."""
        t_infer = get_inference_transforms(image_size=224)

        # Create dummy PIL fundus image
        dummy = Image.new("RGB", (1600, 1600), color=(180, 80, 50))
        tensor = t_infer(dummy)

        self.assertEqual(tensor.shape, (3, 224, 224), "Output tensor shape mismatch!")
        self.assertEqual(tensor.dtype, torch.float32, "Tensor dtype should be float32.")
        self.assertTrue(torch.isfinite(tensor).all(), "Tensor contains NaN or Inf values!")

    def test_08_checkpoint_loading_and_offline_inference(self):
        """Verify that the baseline model loads without internet and runs forward inference."""
        self.assertTrue(self.ckpt_path.exists(), f"Checkpoint not found: {self.ckpt_path}")

        predictor = CareConnectPredictor(checkpoint_path=self.ckpt_path, device="cpu")

        dummy_img = Image.new("RGB", (224, 224), color=(200, 100, 50))
        results = predictor.predict(dummy_img)

        # Output schema assertions
        self.assertIn("vascular_disease_probability", results)
        self.assertIn("vascular_disease_prediction", results)
        self.assertIn("hypertension_probability", results)
        self.assertIn("dr_predicted_grade", results)

        p_vd = results["vascular_disease_probability"]
        self.assertGreaterEqual(p_vd, 0.0)
        self.assertLessEqual(p_vd, 1.0)
        self.assertIn(results["vascular_disease_prediction"], ["Positive", "Negative"])

    def test_09_small_batch_gradient_flow_and_finite_loss(self):
        """Test complete mini-training step on small batch: finite loss, valid gradients."""
        train_df = pd.read_csv(self.splits_dir / "train.csv").head(4)
        ds = CareConnectFundusDataset(train_df, images_dir=self.images_dir, is_training=True, image_size=224)

        from torch.utils.data import DataLoader
        loader = DataLoader(ds, batch_size=2, shuffle=False)

        model = CareConnectMultiTaskNet(pretrained=False)
        criterion = CareConnectMultiTaskLoss()
        optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

        batch = next(iter(loader))
        images = batch["image"]
        targets = batch["targets"]
        masks = batch["masks"]

        optimizer.zero_grad()
        logits = model(images)

        # Verify output shapes
        self.assertEqual(logits["vascular_disease"].shape, (2,), "Vascular disease logit shape mismatch!")
        self.assertEqual(logits["systemic_hypertension"].shape, (2,), "Hypertension logit shape mismatch!")
        self.assertEqual(logits["dr_grade"].shape, (2, 5), "DR grade logits shape mismatch!")

        loss, breakdown = criterion(logits, targets, masks)

        # Verify finite loss
        self.assertTrue(torch.isfinite(loss), f"Loss is not finite: {loss.item()}")
        self.assertGreater(loss.item(), 0.0, "Loss is non-positive!")

        loss.backward()

        # Verify valid finite gradients exist across heads and backbone
        head_vd_grad = model.head_vd.weight.grad
        self.assertIsNotNone(head_vd_grad, "Head VD weight gradient is None!")
        self.assertTrue(torch.isfinite(head_vd_grad).all(), "Head VD gradient has NaN/Inf!")

        backbone_grad = list(model.features.parameters())[0].grad
        self.assertIsNotNone(backbone_grad, "Backbone parameter gradient is None!")
        self.assertTrue(torch.isfinite(backbone_grad).all(), "Backbone gradient has NaN/Inf!")

        optimizer.step()


if __name__ == "__main__":
    unittest.main(verbosity=2)
