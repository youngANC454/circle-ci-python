import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class FailurePredictor:
    """Machine Learning model for predicting build failures"""
    
    def __init__(self, model_path: str = "data/models/failure_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = [
            'success_rate',
            'failure_count',
            'recent_build_count',
            'error_count',
            'warning_count',
            'total_lines',
            'error_compilation',
            'error_runtime',
            'error_test',
            'error_timeout',
            'error_memory'
        ]
        
    def load_model(self):
        """Load trained model from disk"""
        if os.path.exists(self.model_path):
            try:
                saved_data = joblib.load(self.model_path)
                self.model = saved_data['model']
                self.scaler = saved_data['scaler']
                logger.info(f"Model loaded from {self.model_path}")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self._create_default_model()
        else:
            logger.warning("Model file not found, using default model")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default model (rule-based) when no trained model exists"""
        logger.info("Creating default rule-based model")
        self.model = None
        self.scaler = StandardScaler()
    
    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract features from input data"""
        # Get error type counts
        error_types = data.get('error_types', {})
        
        features = [
            data.get('success_rate', 0.5),
            data.get('failure_count', 0),
            data.get('recent_build_count', 0),
            data.get('error_count', 0),
            data.get('warning_count', 0),
            data.get('total_lines', 0),
            error_types.get('compilation', 0),
            error_types.get('runtime', 0),
            error_types.get('test', 0),
            error_types.get('timeout', 0),
            error_types.get('memory', 0)
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make failure prediction"""
        features = self.extract_features(data)
        
        # If model is trained, use it
        if self.model is not None:
            try:
                # Scale features
                features_scaled = self.scaler.transform(features)
                
                # Get probability
                proba = self.model.predict_proba(features_scaled)[0]
                failure_prob = float(proba[1])  # Probability of failure class
                
                # Get prediction
                prediction = self.model.predict(features_scaled)[0]
                predicted_status = "failed" if prediction == 1 else "success"
                
                # Calculate confidence
                confidence = float(max(proba))
                
            except Exception as e:
                logger.error(f"Model prediction error: {e}")
                return self._rule_based_prediction(data)
        else:
            # Use rule-based prediction
            return self._rule_based_prediction(data)
        
        # Identify key factors
        factors = self._identify_factors(data, features[0], failure_prob)
        
        return {
            "failure_probability": failure_prob,
            "predicted_status": predicted_status,
            "confidence": confidence,
            "factors": factors
        }
    
    def _rule_based_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple rule-based prediction when ML model is unavailable"""
        success_rate = data.get('success_rate', 0.5)
        error_count = data.get('error_count', 0)
        failure_count = data.get('failure_count', 0)
        
        # Simple heuristic
        failure_prob = 0.0
        
        # Factor 1: Success rate
        failure_prob += (1.0 - success_rate) * 0.4
        
        # Factor 2: Recent errors
        if error_count > 0:
            failure_prob += min(error_count / 10.0, 0.3)
        
        # Factor 3: Recent failures
        if failure_count > 0:
            failure_prob += min(failure_count / 5.0, 0.3)
        
        # Cap at 1.0
        failure_prob = min(failure_prob, 1.0)
        
        predicted_status = "failed" if failure_prob > 0.5 else "success"
        confidence = abs(failure_prob - 0.5) * 2  # 0-1 scale
        
        factors = self._identify_factors(data, None, failure_prob)
        
        return {
            "failure_probability": failure_prob,
            "predicted_status": predicted_status,
            "confidence": confidence,
            "factors": factors
        }
    
    def _identify_factors(
        self, 
        data: Dict[str, Any], 
        features: np.ndarray,
        failure_prob: float
    ) -> List[Dict[str, Any]]:
        """Identify key factors contributing to prediction"""
        factors = []
        
        success_rate = data.get('success_rate', 0.5)
        if success_rate < 0.7:
            factors.append({
                "factor": "Low success rate",
                "value": f"{success_rate*100:.1f}%",
                "impact": "high"
            })
        
        error_count = data.get('error_count', 0)
        if error_count > 5:
            factors.append({
                "factor": "High error count",
                "value": error_count,
                "impact": "high"
            })
        
        failure_count = data.get('failure_count', 0)
        if failure_count > 3:
            factors.append({
                "factor": "Recent failures",
                "value": failure_count,
                "impact": "medium"
            })
        
        error_types = data.get('error_types', {})
        for err_type, count in error_types.items():
            if count > 0:
                factors.append({
                    "factor": f"{err_type.capitalize()} errors",
                    "value": count,
                    "impact": "medium"
                })
        
        return factors[:5]  # Top 5 factors
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "type": "FailurePredictor",
            "algorithm": "RandomForest" if self.model else "RuleBased",
            "features": self.feature_names,
            "loaded": self.model is not None
        }
