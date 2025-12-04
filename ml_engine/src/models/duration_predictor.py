import numpy as np 
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict,Any
import logging

logger=logging.getLogger(__name__)

class DurationPredictor:
    def __init__(self,model_path:str="data/models/duration_model.pkl"):
        self.model_path=model_path
        self.model=None
        self.scaler=None
        self.feature_names=[
            "recent_build_count",
            "success_rate",
            "average_duration",
            "error_count",
            "warning_count",
            "total_lines"
        ]
    
    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                saved_data=joblib.load(self.model_path)
                self.model=saved_data['model']
                self.scaler=saved_data['scaler']
                logger.info(f"Model loaded successfully {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                self._create_default_model()
        else:
            logger.error("Model not found")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default model when no trained model exists"""
        logger.info("Creating default duration model")
        self.model = None
        self.scaler = StandardScaler()
    
    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        """Extract features from input data"""
        features = [
            data.get('average_duration', 300.0),
            data.get('recent_build_count', 0),
            data.get('success_rate', 0.5),
            data.get('total_lines', 0),
            data.get('error_count', 0),
            data.get('warning_count', 0)
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make duration prediction"""
        features = self.extract_features(data)
        
        # If model is trained, use it
        if self.model is not None:
            try:
                # Scale features
                features_scaled = self.scaler.transform(features)
                
                # Predict duration
                predicted_duration = float(self.model.predict(features_scaled)[0])
                
                # Calculate confidence (simplified)
                confidence = 0.85  # You can implement proper confidence calculation
                
            except Exception as e:
                logger.error(f"Model prediction error: {e}")
                return self._rule_based_prediction(data)
        else:
            # Use rule-based prediction
            return self._rule_based_prediction(data)
        
        # Calculate duration range (±20%)
        min_duration = predicted_duration * 0.8
        max_duration = predicted_duration * 1.2
        
        return {
            "predicted_duration": max(0, predicted_duration),
            "min_duration": max(0, min_duration),
            "max_duration": max_duration,
            "confidence": confidence
        }
    
    def _rule_based_prediction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple rule-based prediction when ML model is unavailable"""
        average_duration = data.get('average_duration', 300.0)
        error_count = data.get('error_count', 0)
        success_rate = data.get('success_rate', 0.5)
        
        # Base prediction on average
        predicted_duration = average_duration
        
        # Adjust based on success rate (failed builds often take longer)
        if success_rate < 0.5:
            predicted_duration *= 1.2
        
        # Adjust based on error count
        if error_count > 0:
            predicted_duration *= (1 + error_count * 0.05)
        
        # Calculate range
        min_duration = predicted_duration * 0.7
        max_duration = predicted_duration * 1.3
        
        confidence = 0.6  # Lower confidence for rule-based
        
        return {
            "predicted_duration": max(0, predicted_duration),
            "min_duration": max(0, min_duration),
            "max_duration": max_duration,
            "confidence": confidence
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "type": "DurationPredictor",
            "algorithm": "RandomForest" if self.model else "RuleBased",
            "features": self.feature_names,
            "loaded": self.model is not None
        }
