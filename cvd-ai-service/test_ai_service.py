"""
CareConnect Retinal AI Microservice Direct Security & Functional Test Suite
===========================================================================
Direct unit & security test suite testing API logic, rate limiting, authentication,
image validation, clinical caveat integrity, and model inference without reliance
on external network transports or anyio thread portals.

Test Invariants:
1. Health endpoint metadata integrity & zero path disclosure.
2. API Key rejection when missing (HTTP 401).
3. API Key rejection when invalid (HTTP 401).
4. API Key acceptance when valid.
5. In-memory per-IP rate limiter enforcement (HTTP 429 after 60 req/min).
6. File extension validation & non-image rejection (HTTP 400).
7. Corrupted image byte rejection (HTTP 400).
8. Undersized image rejection (HTTP 400).
9. Oversized image dimension rejection (HTTP 400).
10. Valid fundus image byte processing.
11. Service degradation handling when model is uninitialized (HTTP 503).
12. Clinical assessment disclaimer integrity and non-diagnostic framing.
13. Model inference and multi-task screening output schema validation.
"""

import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

from PIL import Image

# Ensure cvd-ai-service is on import path
SERVICE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVICE_DIR.parent
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

# Configure test API Key before importing api_server
TEST_API_KEY = "test_careconnect_sec_key_2026"
os.environ["HMS_AI_API_KEY"] = TEST_API_KEY

import api_server
from api_server import (
    health,
    verify_api_key,
    check_rate_limit,
    validate_image_bytes,
    compute_clinical_assessment,
    HTTPException,
    _rate_store,
)


class TestCareConnectAIServiceSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_image_path = PROJECT_ROOT / "src" / "main" / "webapp" / "uploads" / "fundus" / "samples" / "img00330.jpg"
        if not cls.sample_image_path.exists():
            raise FileNotFoundError(f"Sample fundus image not found at: {cls.sample_image_path}")
        with open(cls.sample_image_path, "rb") as f:
            cls.sample_image_bytes = f.read()

    def setUp(self):
        # Reset rate limiter store between tests
        _rate_store.clear()
        os.environ["HMS_AI_API_KEY"] = TEST_API_KEY

    def test_01_health_metadata_and_path_leak_prevention(self):
        """Verify health check returns expected status and does not leak local filesystem paths."""
        res = health()
        self.assertIn("status", res)
        self.assertEqual(res["model_version"], "2.0.0-experiment_b")
        self.assertEqual(res["architecture"], "CareConnectMultiTaskNet (EfficientNet-B0)")
        self.assertIn("experimental_notice", res)

        # Invariant: No filesystem paths leaked in metadata
        for k, v in res.items():
            val_str = str(v)
            self.assertFalse("C:\\" in val_str or "/home/" in val_str or "Users" in val_str,
                             f"Sensitive path leak detected in health metadata key '{k}': {val_str}")

    def test_02_verify_api_key_missing_rejected(self):
        """Verify missing X-API-Key header raises HTTP 401."""
        with self.assertRaises(HTTPException) as ctx:
            verify_api_key(None)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid or missing", ctx.exception.detail)

    def test_03_verify_api_key_invalid_rejected(self):
        """Verify invalid X-API-Key raises HTTP 401."""
        with self.assertRaises(HTTPException) as ctx:
            verify_api_key("tampered_invalid_api_key_value")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Invalid or missing", ctx.exception.detail)

    def test_04_verify_api_key_valid_accepted(self):
        """Verify matching X-API-Key executes without exception."""
        try:
            verify_api_key(TEST_API_KEY)
        except HTTPException:
            self.fail("verify_api_key raised HTTPException unexpectedly with valid key.")

    def test_05_rate_limiter_enforcement(self):
        """Verify rate limiter permits 60 requests and blocks the 61st with HTTP 429."""
        mock_req = MagicMock()
        mock_req.client.host = "192.168.1.100"

        for i in range(60):
            check_rate_limit(mock_req)

        with self.assertRaises(HTTPException) as ctx:
            check_rate_limit(mock_req)
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertIn("Rate limit exceeded", ctx.exception.detail)

    def test_06_reject_invalid_file_extension(self):
        """Verify non-image extensions raise HTTP 400."""
        with self.assertRaises(HTTPException) as ctx:
            validate_image_bytes(b"sample script data", "malicious_script.php")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid file type", ctx.exception.detail)

    def test_07_reject_corrupted_image(self):
        """Verify corrupted bytes masquerading as image raise HTTP 400."""
        corrupted = b"\xFF\xD8\xFF\xE0" + b"\x00" * 200 + b"not a jpeg stream"
        with self.assertRaises(HTTPException) as ctx:
            validate_image_bytes(corrupted, "test_corrupt.jpg")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("not a valid, uncorrupted image", ctx.exception.detail)

    def test_08_reject_undersized_image(self):
        """Verify images smaller than 64x64 pixels raise HTTP 400."""
        tiny = Image.new("RGB", (32, 32), color=(255, 0, 0))
        buf = io.BytesIO()
        tiny.save(buf, format="JPEG")
        with self.assertRaises(HTTPException) as ctx:
            validate_image_bytes(buf.getvalue(), "tiny.jpg")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("too small", ctx.exception.detail)

    def test_09_reject_oversized_image_dimensions(self):
        """Verify images exceeding 10000x10000 pixels raise HTTP 400."""
        large = Image.new("RGB", (10001, 100), color=(0, 255, 0))
        buf = io.BytesIO()
        large.save(buf, format="PNG")
        with self.assertRaises(HTTPException) as ctx:
            validate_image_bytes(buf.getvalue(), "oversized.png")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("exceed maximum allowed", ctx.exception.detail)

    def test_10_accept_valid_fundus_image(self):
        """Verify valid fundus image passes validation cleanly and returns RGB Image."""
        img = validate_image_bytes(self.sample_image_bytes, "img00330.jpg")
        self.assertIsNotNone(img)
        self.assertEqual(img.mode, "RGB")
        self.assertGreaterEqual(img.width, 64)
        self.assertGreaterEqual(img.height, 64)

    def test_11_service_degradation_when_model_missing(self):
        """Verify service degradation is correctly reported when model is uninitialized."""
        orig_predictor = api_server.PREDICTOR
        try:
            api_server.PREDICTOR = None
            res = health()
            self.assertEqual(res["status"], "degraded")
            self.assertFalse(res["model_loaded"])
        finally:
            api_server.PREDICTOR = orig_predictor

    def test_12_clinical_caveat_integrity(self):
        """Verify clinical assessment outputs non-diagnostic experimental guidance."""
        assessment = compute_clinical_assessment({"dr_predicted_grade": "No DR"})
        self.assertIn("risk_level", assessment)
        self.assertIn("recommendation", assessment)
        self.assertIn("Experimental AI research output", assessment["recommendation"])
        self.assertIn("physician", assessment["recommendation"].lower())
        self.assertNotIn("Diagnosed with CVD", assessment["recommendation"])
        self.assertNotIn("Confirmed Cardiovascular Disease", assessment["recommendation"])

    def test_13_model_inference_pipeline_and_schema(self):
        """Verify end-to-end model inference with real weights generates expected multi-task schema."""
        if api_server.PREDICTOR is None:
            api_server.startup_event()

        self.assertIsNotNone(api_server.PREDICTOR, "Predictor should be initialized after startup_event")

        img = validate_image_bytes(self.sample_image_bytes, "img00330.jpg")
        results = api_server.PREDICTOR.predict(img)
        assessment = compute_clinical_assessment(results)

        self.assertIn("cvd_prediction", results)
        self.assertIn("hypertension_prediction", results)
        self.assertIn("dr_predicted_grade", results)
        self.assertIn("cvd_predicted_probability", results)
        self.assertTrue(0.0 <= results["cvd_predicted_probability"] <= 1.0)
        self.assertIn("recommendation", assessment)
        self.assertIn("physician", assessment["recommendation"].lower())


if __name__ == "__main__":
    unittest.main()
