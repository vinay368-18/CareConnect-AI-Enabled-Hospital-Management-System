"""
CareConnect Retinal AI Microservice Test Suite
=============================================
Tests:
1. Health endpoint (/health)
2. Valid image prediction (/predict)
3. Base64 prediction (/predict-base64)
4. Invalid file type rejection (HTTP 400)
5. Corrupted image bytes rejection (HTTP 400)
6. Undersized image rejection (HTTP 400)
7. Missing checkpoint / service degradation handling (HTTP 503)
8. Output schema and clinical caveats validation
"""

import base64
import io
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from PIL import Image
import torch

# Ensure cvd-ai-service is on import path
SERVICE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVICE_DIR.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

import api_server
from api_server import app, validate_image_bytes
import inference


class TestCareConnectAIService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Force startup event to initialize models
        api_server.startup_event()
        cls.client = TestClient(app)
        cls.sample_image_path = PROJECT_ROOT / "src" / "main" / "webapp" / "uploads" / "fundus" / "samples" / "img00330.jpg"
        if not cls.sample_image_path.exists():
            raise FileNotFoundError(f"Sample image not found: {cls.sample_image_path}")

    def test_01_health_endpoint(self):
        """Verify GET /health returns status healthy and expected metadata."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])
        self.assertEqual(data["model_version"], "2.0.0-experiment_b")
        self.assertEqual(data["device"], "cpu")
        self.assertIn("vascular_disease", data["tasks"])
        self.assertIn("dr_grade", data["tasks"])

    def test_02_predict_valid_image(self):
        """Verify POST /predict with a genuine fundus photograph."""
        with open(self.sample_image_path, "rb") as f:
            resp = self.client.post(
                "/predict",
                files={"file": ("img00330.jpg", f, "image/jpeg")}
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["model_version"], "2.0.0-experiment_b")

        # Vascular Disease (Primary CVD Target)
        self.assertIn("cvd_prediction", data)
        self.assertIn(data["cvd_prediction"], ["Positive", "Negative"])
        self.assertGreaterEqual(data["cvd_probability"], 0.0)
        self.assertLessEqual(data["cvd_probability"], 1.0)
        self.assertEqual(data["cvd_threshold"], 0.4996)

        # Systemic Hypertension
        self.assertIn("hypertension_prediction", data)
        self.assertGreaterEqual(data["hypertension_probability"], 0.0)
        self.assertLessEqual(data["hypertension_probability"], 1.0)
        self.assertEqual(data["hypertension_threshold"], 0.4288)

        # Diabetic Retinopathy
        self.assertIn("dr_grade", data)
        self.assertIn(data["dr_grade"], inference.DR_CLASSES)
        self.assertGreaterEqual(data["dr_confidence"], 0.0)
        self.assertLessEqual(data["dr_confidence"], 1.0)
        self.assertEqual(len(data["dr_probabilities"]), 5)

        # Clinical Safety Flags
        self.assertTrue(data["experimental_flag"])
        self.assertIn("clinical_caveats", data)
        self.assertIn("0.5202", data["clinical_caveats"])
        self.assertIn("risk_level", data)
        self.assertIn("recommendation", data)

    def test_03_predict_base64_payload(self):
        """Verify POST /predict-base64 with base64 encoded image."""
        with open(self.sample_image_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")

        resp = self.client.post("/predict-base64", json={"image_base64": b64_str})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("cvd_probability", data)
        self.assertIn("dr_grade", data)

    def test_04_reject_invalid_file_extension(self):
        """Verify POST /predict safely rejects non-image extensions with HTTP 400."""
        dummy_content = b"This is a text file, not an image."
        resp = self.client.post(
            "/predict",
            files={"file": ("report.pdf", dummy_content, "application/pdf")}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid file type", resp.json()["detail"])

    def test_05_reject_corrupted_image(self):
        """Verify POST /predict rejects corrupted / unreadable image bytes with HTTP 400."""
        corrupt_bytes = b"\xFF\xD8\xFF\xE0" + b"random_corrupted_noise_bytes_here" * 50
        resp = self.client.post(
            "/predict",
            files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not a valid, uncorrupted image", resp.json()["detail"])

    def test_06_reject_undersized_image(self):
        """Verify POST /predict rejects images smaller than 64x64 pixels."""
        tiny_img = Image.new("RGB", (32, 32), color=(255, 0, 0))
        buf = io.BytesIO()
        tiny_img.save(buf, format="JPEG")
        resp = self.client.post(
            "/predict",
            files={"file": ("tiny.jpg", buf.getvalue(), "image/jpeg")}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("too small", resp.json()["detail"])

    def test_07_service_unavailable_when_model_missing(self):
        """Verify POST /predict returns HTTP 503 when model is not initialized."""
        original_predictor = api_server.PREDICTOR
        try:
            api_server.PREDICTOR = None
            with open(self.sample_image_path, "rb") as f:
                resp = self.client.post(
                    "/predict",
                    files={"file": ("img00330.jpg", f, "image/jpeg")}
                )
            self.assertEqual(resp.status_code, 503)
            self.assertIn("temporarily unavailable", resp.json()["detail"])
        finally:
            api_server.PREDICTOR = original_predictor

    def test_08_clinical_disclaimer_integrity(self):
        """Ensure clinical warnings prevent unsupported diagnostic claims."""
        with open(self.sample_image_path, "rb") as f:
            resp = self.client.post(
                "/predict",
                files={"file": ("img00330.jpg", f, "image/jpeg")}
            )
        data = resp.json()
        # Verify CVD is never claimed as a proven diagnostic fact
        self.assertNotIn("Diagnosed with CVD", data["recommendation"])
        self.assertNotIn("Confirmed Cardiovascular Disease", data["recommendation"])
        # Verify physician consultation requirement is explicit
        self.assertIn("physician", data["recommendation"].lower())


if __name__ == "__main__":
    unittest.main()
