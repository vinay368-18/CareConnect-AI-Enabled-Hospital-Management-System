"""
CVD & Retinal Multi-Task AI REST API Service
Integrates PyTorch Deep Learning with Hospital Management System (HMS)
"""

import io
import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from inference import RetinalPredictor
from vessel_segmentation import VesselSegmenter

app = FastAPI(
    title="CareConnect CVD & Retinal AI Microservice",
    description="Cardiovascular Disease, Hypertension & Diabetic Retinopathy Risk Screening API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Predictor instance
PREDICTOR: Optional[RetinalPredictor] = None
VESSEL: Optional[VesselSegmenter] = None

@app.on_event("startup")
def startup_event():
    global PREDICTOR, VESSEL
    print("[CVD API] Initializing RetinalPredictor PyTorch model...")
    PREDICTOR = RetinalPredictor()
    print("[CVD API] PyTorch model loaded successfully on CPU.")
    try:
        VESSEL = VesselSegmenter()
        print("[CVD API] Residual U-Net vessel segmentation model loaded.")
    except Exception as e:  # the rest of the API keeps working without it
        VESSEL = None
        print(f"[CVD API] Vessel segmentation disabled: {e}")

@app.get("/")
def root():
    return {
        "service": "CareConnect AI CVD & Retinal Analysis Service",
        "status": "online",
        "model": "MultiTask EfficientNet-B0",
        "tasks": ["Cardiovascular Disease (CVD)", "Systemic Hypertension", "Diabetic Retinopathy (ICDR)"]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": PREDICTOR is not None,
        "vessel_model_loaded": VESSEL is not None
    }

def compute_overall_assessment(results: Dict[str, Any]) -> Dict[str, str]:
    p_cvd = results.get("cvd_predicted_probability", 0.0)
    p_ht = results.get("hypertension_predicted_probability", 0.0)
    pred_cvd = results.get("cvd_prediction", "Negative")
    pred_ht = results.get("hypertension_prediction", "Negative")
    dr_grade = results.get("dr_predicted_grade", "No DR")

    if pred_cvd == "Positive" and p_cvd >= 0.60:
        risk_level = "High Risk"
        recommendation = "Immediate cardiovascular assessment recommended. Schedule ECG, lipid profile, and comprehensive cardiology consult."
    elif pred_cvd == "Positive" or (pred_ht == "Positive" and p_ht >= 0.55):
        risk_level = "Moderate Risk"
        recommendation = "Elevated cardiovascular / hypertension markers detected. Recommend routine blood pressure monitoring and preventive lifestyle modifications."
    elif dr_grade in ["Moderate", "Severe", "Proliferative"]:
        risk_level = "Moderate Risk"
        recommendation = "Signs of Diabetic Retinopathy detected. Urgently schedule a dilated fundus eye exam with an ophthalmologist."
    else:
        risk_level = "Low Risk"
        recommendation = "Retinal markers within normal parameters. Continue annual preventive health check-ups."

    return {
        "risk_level": risk_level,
        "recommendation": recommendation
    }

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    if not PREDICTOR:
        raise HTTPException(status_code=503, detail="AI Model not ready")

    try:
        content = await file.read()
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    results = PREDICTOR.predict(image)
    assessment = compute_overall_assessment(results)

    return {
        "status": "success",
        "cvd_prediction": results["cvd_prediction"],
        "cvd_probability": round(float(results["cvd_predicted_probability"]), 4),
        "cvd_threshold": results["cvd_threshold"],
        "hypertension_prediction": results["hypertension_prediction"],
        "hypertension_probability": round(float(results["hypertension_predicted_probability"]), 4),
        "hypertension_threshold": results["hypertension_threshold"],
        "dr_grade": results["dr_predicted_grade"],
        "dr_confidence": round(float(results["dr_confidence"]), 4),
        "dr_probabilities": {k: round(v, 4) for k, v in results["dr_probabilities"].items()},
        "risk_level": assessment["risk_level"],
        "recommendation": assessment["recommendation"],
        "reliability_badge": results.get("cvd_reliability_badge", "")
    }

class Base64Payload(BaseModel):
    image_base64: str

@app.post("/predict-base64")
def predict_base64(payload: Base64Payload):
    if not PREDICTOR:
        raise HTTPException(status_code=503, detail="AI Model not ready")

    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        decoded = base64.b64decode(raw_b64)
        image = Image.open(io.BytesIO(decoded)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {str(e)}")

    results = PREDICTOR.predict(image)
    assessment = compute_overall_assessment(results)

    return {
        "status": "success",
        "cvd_prediction": results["cvd_prediction"],
        "cvd_probability": round(float(results["cvd_predicted_probability"]), 4),
        "cvd_threshold": results["cvd_threshold"],
        "hypertension_prediction": results["hypertension_prediction"],
        "hypertension_probability": round(float(results["hypertension_predicted_probability"]), 4),
        "hypertension_threshold": results["hypertension_threshold"],
        "dr_grade": results["dr_predicted_grade"],
        "dr_confidence": round(float(results["dr_confidence"]), 4),
        "dr_probabilities": {k: round(v, 4) for k, v in results["dr_probabilities"].items()},
        "risk_level": assessment["risk_level"],
        "recommendation": assessment["recommendation"],
        "reliability_badge": results.get("cvd_reliability_badge", "")
    }

@app.post("/segment")
def segment_vessels(file: UploadFile = File(...)):
    """Residual U-Net vessel segmentation. Returns a PNG overlay; vessel density is in the X-Vessel-Density header."""
    if VESSEL is None:
        raise HTTPException(status_code=503, detail="Vessel segmentation model not loaded")
    try:
        image = Image.open(io.BytesIO(file.file.read())).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

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

@app.get("/sample-images")
def get_sample_images():
    """List demo retinal fundus images available on the system."""
    sample_dir = Path(r"c:\Users\vinay\CVD Project\BRSET_v1.0.2-20261001T140733Z-1-006\BRSET_v1.0.2\physionet.org\files\brazilian-ophthalmological\1.0.2\fundus_photos")
    samples = []
    if sample_dir.exists():
        for f in list(sample_dir.glob("*.jpg"))[:6]:
            samples.append({
                "filename": f.name,
                "path": str(f)
            })
    return {"samples": samples}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
