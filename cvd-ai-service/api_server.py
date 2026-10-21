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
import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

from inference import RetinalPredictor

# Optional vessel segmentation module
try:
    from vessel_segmentation import VesselSegmenter
except ImportError:
    VesselSegmenter = None

logger = logging.getLogger("cvd-api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="CareConnect Retinal AI Microservice",
    description="Multi-Task Retinal Image Screening API (Vascular Disease, Hypertension, Diabetic Retinopathy)",
    version="2.0.0-experiment_b"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances
PREDICTOR: Optional[RetinalPredictor] = None
VESSEL: Optional[Any] = None
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@app.on_event("startup")
def startup_event():
    global PREDICTOR, VESSEL
    logger.info("[CVD API] Initializing CareConnect Retinal AI microservice...")
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
        "model": "MultiTask EfficientNet-B0 (Experiment B)",
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
        "tasks": ["vascular_disease", "systemic_hypertension", "dr_grade"]
    }


def compute_clinical_assessment(results: Dict[str, Any]) -> Dict[str, str]:
    """
    Produce responsible clinical messaging adhering strictly to research boundaries.
    Never invents unvalidated diagnostic risk categories.
    """
    dr_grade = results.get("dr_predicted_grade", "No DR")
    p_vd = results.get("cvd_predicted_probability", 0.0)

    # Risk level phrasing maintains non-diagnostic, assistive framing
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
    except (UnidentifiedImageError, ValueError, OSError) as e:
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

    return image


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
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
        logger.error(f"Inference error during /predict: {e}", exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during image tensor preprocessing or inference."
        )


class Base64Payload(BaseModel):
    image_base64: str


@app.post("/predict-base64")
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


@app.post("/segment")
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
    uvicorn.run(app, host="127.0.0.1", port=5000)
