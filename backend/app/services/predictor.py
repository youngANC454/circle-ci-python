import httpx
import logging
from typing import Dict, Any

from app.config import settings
from app.models import FailurePrediction, DurationPrediction

logger = logging.getLogger(__name__)


class PredictorService:
    """Service for making ML predictions"""
    
    def __init__(self):
        self.ml_service_url = settings.ML_SERVICE_URL
        self.timeout = 30.0
    
    async def predict_failure(self, features: Dict[str, Any]) -> FailurePrediction:
        """Predict build failure probability"""
        url = f"{self.ml_service_url}/predict/failure"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=features)
                response.raise_for_status()
                data = response.json()
                
                # Determine risk level
                prob = data.get("failure_probability", 0.0)
                risk_level = self._determine_risk_level(prob)
                
                return FailurePrediction(
                    project_slug=features.get("project_slug", ""),
                    failure_probability=prob,
                    predicted_status="failed" if prob > 0.5 else "success",
                    confidence=data.get("confidence", 0.0),
                    risk_level=risk_level,
                    factors=data.get("factors", [])
                )
        
        except httpx.HTTPError as e:
            logger.error(f"Error calling ML service for failure prediction: {e}")
            # Return a default prediction
            return self._default_failure_prediction(features)
    
    async def predict_duration(self, features: Dict[str, Any]) -> DurationPrediction:
        """Predict build duration"""
        url = f"{self.ml_service_url}/predict/duration"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=features)
                response.raise_for_status()
                data = response.json()
                
                predicted_seconds = data.get("predicted_duration", 0)
                
                return DurationPrediction(
                    project_slug=features.get("project_slug", ""),
                    predicted_duration=predicted_seconds,
                    duration_range={
                        "min": data.get("min_duration", predicted_seconds - 60),
                        "max": data.get("max_duration", predicted_seconds + 60)
                    },
                    confidence=data.get("confidence", 0.0)
                )
        
        except httpx.HTTPError as e:
            logger.error(f"Error calling ML service for duration prediction: {e}")
            # Return a default prediction
            return self._default_duration_prediction(features)
    
    def _determine_risk_level(self, probability: float) -> str:
        """Determine risk level from probability"""
        if probability < 0.3:
            return "low"
        elif probability < 0.7:
            return "medium"
        else:
            return "high"
    
    def _default_failure_prediction(self, features: Dict[str, Any]) -> FailurePrediction:
        """Return default failure prediction when ML service is unavailable"""
        return FailurePrediction(
            project_slug=features.get("project_slug", "unknown"),
            failure_probability=0.5,
            predicted_status="unknown",
            confidence=0.0,
            risk_level="medium",
            factors=[{"note": "ML service unavailable, using default prediction"}]
        )
    
    def _default_duration_prediction(self, features: Dict[str, Any]) -> DurationPrediction:
        """Return default duration prediction when ML service is unavailable"""
        # Use average duration from features if available
        avg_duration = features.get("average_duration", 300)  # 5 minutes default
        
        return DurationPrediction(
            project_slug=features.get("project_slug", "unknown"),
            predicted_duration=int(avg_duration),
            duration_range={
                "min": int(avg_duration * 0.8),
                "max": int(avg_duration * 1.2)
            },
            confidence=0.0
        )


# Singleton instance
predictor_service = PredictorService()
