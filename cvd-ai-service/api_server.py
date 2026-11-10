"""
CareConnect Retinal AI REST API Microservice
============================================
FastAPI service exposing PyTorch Multi-Task Retinal Screening Model (Experiment B).
Endpoints:
- GET  /health          Service health, model loading status, version metadata
- POST /predict         Multi-task screening on uploaded retinal image (multipart/form-data)
- POST /predict-base64  Multi-task screening on base64 encoded image
- POST /segment         Optional Residual U-Net retinal vessel segmentation
"""

import base64
import hmac
import io
import logging
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, File, Form, Header, Request, UploadFile, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

from inference import RetinalPredictor, DR_CLASSES

# Optional vessel segmentation module
try:
    from vessel_segmentation import VesselSegmenter
except ImportError:
    VesselSegmenter = None

logger = logging.getLogger("cvd-api")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Local configuration file (shared with the Java web application)
# ---------------------------------------------------------------------------
# Settings already present in the environment always win. Missing ones are
# filled from careconnect.env (KEY=VALUE lines, same format as .env.example),
# looked up at $HMS_CONFIG_FILE, then ~/.careconnect/careconnect.env.
# The file lives outside the project, so the API key never enters Git.
def _load_local_config() -> Optional[Path]:
    candidates = []
    explicit = os.environ.get("HMS_CONFIG_FILE", "").strip()
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.home() / ".careconnect" / "careconnect.env")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            logger.warning(f"[CVD API] Could not read config file {path}: {exc}")
            continue
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            key, sep, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not sep or not key:
                continue
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key, value)
        logger.info(f"[CVD API] Loaded settings from {path}")
        return path
    return None


_load_local_config()

# ---------------------------------------------------------------------------
# API Key Authentication
# ---------------------------------------------------------------------------
def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Validate the X-API-Key header using constant-time comparison."""
    api_key = os.environ.get("HMS_AI_API_KEY", "")
    if not api_key:
        logger.error("[CVD API] HMS_AI_API_KEY environment variable is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service authentication is not configured on server.",
        )

    if x_api_key is None or not hmac.compare_digest(x_api_key, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service authentication credentials.",
        )


# ---------------------------------------------------------------------------
# Rate Limiter (in-memory, per-IP, 60 requests/minute for prediction endpoints)
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX = 60
RATE_LIMIT_WINDOW = 60  # seconds
_rate_store: Dict[str, list] = defaultdict(list)
_rate_last_cleanup = time.monotonic()


def _cleanup_rate_store() -> None:
    """Remove expired timestamps older than the rate-limit window."""
    global _rate_last_cleanup
    now = time.monotonic()
    if now - _rate_last_cleanup < RATE_LIMIT_WINDOW:
        return
    _rate_last_cleanup = now
    cutoff = now - RATE_LIMIT_WINDOW
    expired_keys = []
    for ip, timestamps in _rate_store.items():
        _rate_store[ip] = [t for t in timestamps if t > cutoff]
        if not _rate_store[ip]:
            expired_keys.append(ip)
    for ip in expired_keys:
        del _rate_store[ip]


def check_rate_limit(request: Request) -> None:
    """Enforce per-IP rate limiting on prediction and segmentation endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    _cleanup_rate_store()
    cutoff = now - RATE_LIMIT_WINDOW
    timestamps = _rate_store[client_ip]
    _rate_store[client_ip] = [t for t in timestamps if t > cutoff]
    if len(_rate_store[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 60 requests per minute.",
        )
    _rate_store[client_ip].append(now)


# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
_cors_origins_env = os.environ.get("HMS_CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080")
CORS_ORIGINS = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app = FastAPI(
    title="CareConnect Retinal AI Microservice",
    description="Multi-Task Retinal Image Screening API (Vascular Disease, Hypertension, Diabetic Retinopathy)",
    version="2.0.0-experiment_b"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Global model instances
PREDICTOR: Optional[RetinalPredictor] = None
VESSEL: Optional[Any] = None
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_IMAGE_DIMENSION = 10000  # pixels
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@app.on_event("startup")
def startup_event():
    global PREDICTOR, VESSEL
    logger.info("[CVD API] Initializing CareConnect Retinal AI microservice...")

    if not os.environ.get("HMS_AI_API_KEY"):
        logger.warning("[CVD API] WARNING: HMS_AI_API_KEY environment variable is not set. Inference endpoints will reject requests.")

    try:
        PREDICTOR = RetinalPredictor()
        logger.info("[CVD API] PyTorch model loaded successfully on CPU.")
    except Exception as e:
        logger.error(f"[CVD API] Failed to load PyTorch model: {e}")
        PREDICTOR = None

    if VesselSegmenter is not None:
        try:
            VESSEL = VesselSegmenter()
            logger.info("[CVD API] Residual U-Net vessel segmentation model loaded.")
        except Exception as e:
            VESSEL = None
            logger.warning(f"[CVD API] Vessel segmentation disabled: {e}")


@app.get("/")
def root():
    return {
        "service": "CareConnect Retinal AI Screening Service",
        "version": "2.0.0-experiment_b",
        "status": "online",
        "tasks": ["vascular_disease", "systemic_hypertension", "dr_grade"],
        "clinical_safety_notice": "Experimental research screening only. Not a medical diagnosis."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy" if PREDICTOR is not None else "degraded",
        "model_loaded": PREDICTOR is not None,
        "model_version": "2.0.0-experiment_b",
        "architecture": "CareConnectMultiTaskNet (EfficientNet-B0)",
        "device": "cpu",
        "vessel_model_loaded": VESSEL is not None,
        "tasks": ["vascular_disease", "systemic_hypertension", "dr_grade"],
        "experimental_notice": "Research screening only. Not for standalone clinical diagnosis."
    }


def compute_clinical_assessment(results: Dict[str, Any]) -> Dict[str, str]:
    """
    Produce responsible clinical messaging adhering strictly to research boundaries.
    Never invents unvalidated diagnostic risk categories.
    """
    dr_grade = results.get("dr_predicted_grade", "No DR")

    risk_level = "Experimental Screening - Requires Clinical Review"

    recommendation = (
        "Experimental AI research output. Complete comprehensive cardiovascular risk assessment "
        "(blood pressure, fasting lipid panel, 12-lead ECG) by an attending physician is mandatory. "
    )
    if dr_grade in ["Moderate", "Severe", "Proliferative"]:
        recommendation += f"Urgent ophthalmology referral recommended for evaluation of retinal {dr_grade} Diabetic Retinopathy."
    else:
        recommendation += "Routine comprehensive clinical examination recommended."

    return {
        "risk_level": risk_level,
        "recommendation": recommendation
    }


def validate_image_bytes(content: bytes, filename: Optional[str] = None) -> Image.Image:
    """Validate file size, extension, and decodability safely."""
    if not content or len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds 25 MB limit (received {len(content) / (1024*1024):.1f} MB)."
        )

    if filename:
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type '{suffix}'. Allowed formats: JPG, JPEG, PNG."
            )

    try:
        image = Image.open(io.BytesIO(content))
        image.verify()  # Fast integrity check
        # Reopen for actual processing (verify closes the file handle)
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except (UnidentifiedImageError, ValueError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid, uncorrupted image."
        )

    w, h = image.size
    if w < 64 or h < 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image dimensions ({w}x{h}) are too small for retinal analysis (minimum 64x64)."
        )

    if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image dimensions ({w}x{h}) exceed maximum allowed ({MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})."
        )

    return image


@app.post("/predict", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
async def predict_image(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form("Residual U-Net"),
):
    """
    Main prediction endpoint accepting multipart/form-data retinal fundus image.
    Never persists uploaded images permanently to disk.
    """
    if PREDICTOR is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Model service is temporarily unavailable or still initializing."
        )

    try:
        content = await file.read()
        image = validate_image_bytes(content, file.filename)
        results = PREDICTOR.predict(image)
        assessment = compute_clinical_assessment(results)

        dr_grade_name = results["dr_predicted_grade"]
        dr_grade_idx = 0
        if dr_grade_name in DR_CLASSES:
            dr_grade_idx = DR_CLASSES.index(dr_grade_name)

        used_model = model_name or "Residual U-Net"

        return {
            "status": "success",
            "model_version": "2.0.0-experiment_b",
            "model_used": used_model,
            "cvd": {
                "probability": results["cvd_predicted_probability"],
                "result": results["cvd_prediction"],
            },
            "hypertension": {
                "probability": results["hypertension_predicted_probability"],
                "result": results["hypertension_prediction"],
            },
            "diabetic_retinopathy": {
                "grade": dr_grade_idx,
                "label": dr_grade_name,
                "confidence": results["dr_confidence"],
            },
            "risk_assessment": {
                "risk_level": assessment["risk_level"],
                "recommendation": assessment["recommendation"],
            },
            # Flat backwards-compatibility fields
            "cvd_prediction": results["cvd_prediction"],
            "cvd_probability": results["cvd_predicted_probability"],
            "cvd_threshold": results["cvd_threshold"],
            "hypertension_prediction": results["hypertension_prediction"],
            "hypertension_probability": results["hypertension_predicted_probability"],
            "hypertension_threshold": results["hypertension_threshold"],
            "dr_grade": dr_grade_name,
            "dr_confidence": results["dr_confidence"],
            "dr_probabilities": {k: round(v, 4) for k, v in results["dr_probabilities"].items()},
            "risk_level": assessment["risk_level"],
            "recommendation": assessment["recommendation"],
            "reliability_badge": results.get("cvd_reliability_badge", ""),
            "clinical_caveats": results.get("clinical_caveats", ""),
            "experimental_flag": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Inference error during /predict: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during image tensor preprocessing or inference."
        )


class Base64Payload(BaseModel):
    image_base64: str


@app.post("/predict-base64", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
def predict_base64(payload: Base64Payload):
    """Prediction endpoint accepting base64 encoded image strings."""
    if PREDICTOR is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Model service is temporarily unavailable."
        )

    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        decoded = base64.b64decode(raw_b64)
        image = validate_image_bytes(decoded)
        results = PREDICTOR.predict(image)
        assessment = compute_clinical_assessment(results)

        return {
            "status": "success",
            "model_version": "2.0.0-experiment_b",
            "cvd_prediction": results["cvd_prediction"],
            "cvd_probability": results["cvd_predicted_probability"],
            "cvd_threshold": results["cvd_threshold"],
            "hypertension_prediction": results["hypertension_prediction"],
            "hypertension_probability": results["hypertension_predicted_probability"],
            "hypertension_threshold": results["hypertension_threshold"],
            "dr_grade": results["dr_predicted_grade"],
            "dr_confidence": results["dr_confidence"],
            "dr_probabilities": {k: round(v, 4) for k, v in results["dr_probabilities"].items()},
            "risk_level": assessment["risk_level"],
            "recommendation": assessment["recommendation"],
            "reliability_badge": results.get("cvd_reliability_badge", ""),
            "clinical_caveats": results.get("clinical_caveats", ""),
            "experimental_flag": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Inference error during /predict-base64: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing base64 image data."
        )


@app.post("/segment", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)])
def segment_vessels(file: UploadFile = File(...)):
    """Optional Residual U-Net vessel segmentation endpoint."""
    if VESSEL is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vessel segmentation model not loaded."
        )
    try:
        content = file.file.read()
        image = validate_image_bytes(content, file.filename)
        result = VESSEL.segment(image)
        return Response(
            content=result["overlay_png"],
            media_type="image/png",
            headers={
                "X-Vessel-Density": f"{result['vessel_density']:.2f}",
                "X-Vessel-Image-Size": f"{result['size'][0]}x{result['size'][1]}",
                "Access-Control-Expose-Headers": "X-Vessel-Density, X-Vessel-Image-Size",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Segmentation error: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to segment retinal vessel overlay."
        )


if __name__ == "__main__":
    import uvicorn
    from urllib.parse import urlparse
    # Listen on the port the web application calls (HMS_AI_API_URL), default 5000.
    _port = urlparse(os.environ.get("HMS_AI_API_URL", "http://127.0.0.1:5000")).port or 5000
    # Enforce binding strictly to localhost (127.0.0.1)
    uvicorn.run(app, host="127.0.0.1", port=_port)
