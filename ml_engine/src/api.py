from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import os

from src.models.failure_predictor import FailurePredictor
from src.models.duration_predictor import DurationPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="CI/CD ML Engine",
    description="Machine Learning inference service for CI/CD predictions",
    version="1.0.0"
)

# Load models on startup
failure_model = None
duration_model = None

@app.on_event("startup")
async def load_models():
    """Load ML models on startup"""
    global failure_model, duration_model
    
    try:
        failure_model = FailurePredictor()
        failure_model.load_model()
        logger.info("Failure prediction model loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load failure model: {e}")
        failure_model = FailurePredictor()
    
    try:
        duration_model = DurationPredictor()
        duration_model.load_model()
        logger.info("Duration prediction model loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load duration model: {e}")
        duration_model = DurationPredictor()


# Request/Response Models
class PredictionRequest(BaseModel):
    project_slug: str
    branch: str = "main"
    recent_build_count: int = 10
    success_rate: float = 0.5
    failure_count: int = 0
    average_duration: float = 300.0
    error_count: int = 0
    warning_count: int = 0
    total_lines: int = 0
    error_types: Dict[str, int] = {}


class FailurePredictionResponse(BaseModel):
    failure_probability: float
    predicted_status: str
    confidence: float
    factors: List[Dict[str, Any]]


class DurationPredictionResponse(BaseModel):
    predicted_duration: int
    min_duration: int
    max_duration: int
    confidence: float


@app.get("/health")
async def health_check():
    """Health check endpoint for ML engine"""
    return {
        "status": "healthy",
        "service": "ml-engine",
        "version": "1.0.0",
        "models_loaded": {
            "failure_model": failure_model is not None and failure_model.model is not None,
            "duration_model": duration_model is not None and duration_model.model is not None
        }
    }


@app.post("/predict/failure", response_model=FailurePredictionResponse)
async def predict_failure(request: PredictionRequest):
    """Predict build failure probability"""
    try:
        if failure_model is None:
            raise HTTPException(status_code=503, detail="Failure model not loaded")
        
        # Make prediction
        prediction = failure_model.predict(request.dict())
        
        return FailurePredictionResponse(
            failure_probability=prediction["failure_probability"],
            predicted_status=prediction["predicted_status"],
            confidence=prediction["confidence"],
            factors=prediction["factors"]
        )
    
    except Exception as e:
        logger.error(f"Error in failure prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/duration", response_model=DurationPredictionResponse)
async def predict_duration(request: PredictionRequest):
    """Predict build duration"""
    try:
        if duration_model is None:
            raise HTTPException(status_code=503, detail="Duration model not loaded")
        
        # Make prediction
        prediction = duration_model.predict(request.dict())
        
        return DurationPredictionResponse(
            predicted_duration=int(prediction["predicted_duration"]),
            min_duration=int(prediction["min_duration"]),
            max_duration=int(prediction["max_duration"]),
            confidence=prediction["confidence"]
        )
    
    except Exception as e:
        logger.error(f"Error in duration prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info")
async def get_model_info():
    """Get information about loaded models"""
    info = {
        "failure_model": None,
        "duration_model": None
    }
    
    if failure_model:
        info["failure_model"] = failure_model.get_model_info()
    
    if duration_model:
        info["duration_model"] = duration_model.get_model_info()
    
    return info
