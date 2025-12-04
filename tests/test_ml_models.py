import pytest
import numpy as np
import sys
import os

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ml_engine')))

from src.models.failure_predictor import FailurePredictor
from src.models.duration_predictor import DurationPredictor


class TestFailurePredictor:
    """Test failure prediction model"""
    
    def test_initialization(self):
        """Test model can be initialized"""
        predictor = FailurePredictor()
        assert predictor is not None
        assert predictor.feature_names is not None
    
    def test_extract_features(self):
        """Test feature extraction"""
        predictor = FailurePredictor()
        
        data = {
            'success_rate': 0.8,
            'failure_count': 2,
            'error_count': 5,
            'error_types': {'compilation': 2, 'test': 3}
        }
        
        features = predictor.extract_features(data)
        assert features is not None
        assert features.shape[1] == len(predictor.feature_names)
    
    def test_prediction_with_default_model(self):
        """Test prediction with rule-based model"""
        predictor = FailurePredictor()
        
        # High risk data
        data = {
            'success_rate': 0.3,
            'failure_count': 5,
            'error_count': 10,
            'warning_count': 5,
            'total_lines': 1000,
            'error_types': {
                'compilation': 3,
                'runtime': 2,
                'test': 5,
                'timeout': 0,
                'memory': 0
            }
        }
        
        result = predictor.predict(data)
        
        assert 'failure_probability' in result
        assert 'predicted_status' in result
        assert 'confidence' in result
        assert 'factors' in result
        assert 0 <= result['failure_probability'] <= 1
        assert result['predicted_status'] in ['success', 'failed']
    
    def test_prediction_low_risk(self):
        """Test prediction with low risk data"""
        predictor = FailurePredictor()
        
        data = {
            'success_rate': 0.95,
            'failure_count': 0,
            'error_count': 0,
            'warning_count': 0,
            'total_lines': 100,
            'error_types': {}
        }
        
        result = predictor.predict(data)
        
        # Should predict low failure probability
        assert result['failure_probability'] < 0.5
        assert result['predicted_status'] == 'success'
    
    def test_get_model_info(self):
        """Test model info retrieval"""
        predictor = FailurePredictor()
        info = predictor.get_model_info()
        
        assert 'type' in info
        assert 'algorithm' in info
        assert 'features' in info
        assert info['type'] == 'FailurePredictor'


class TestDurationPredictor:
    """Test duration prediction model"""
    
    def test_initialization(self):
        """Test model can be initialized"""
        predictor = DurationPredictor()
        assert predictor is not None
        assert predictor.feature_names is not None
    
    def test_extract_features(self):
        """Test feature extraction"""
        predictor = DurationPredictor()
        
        data = {
            'average_duration': 300.0,
            'recent_build_count': 10,
            'success_rate': 0.8
        }
        
        features = predictor.extract_features(data)
        assert features is not None
        assert features.shape[1] == len(predictor.feature_names)
    
    def test_prediction_with_default_model(self):
        """Test prediction with rule-based model"""
        predictor = DurationPredictor()
        
        data = {
            'average_duration': 300.0,
            'recent_build_count': 10,
            'success_rate': 0.8,
            'total_lines': 1000,
            'error_count': 2,
            'warning_count': 1
        }
        
        result = predictor.predict(data)
        
        assert 'predicted_duration' in result
        assert 'min_duration' in result
        assert 'max_duration' in result
        assert 'confidence' in result
        assert result['predicted_duration'] > 0
        assert result['min_duration'] < result['predicted_duration']
        assert result['max_duration'] > result['predicted_duration']
    
    def test_duration_adjustment_for_errors(self):
        """Test that errors increase predicted duration"""
        predictor = DurationPredictor()
        
        # Data without errors
        data_no_errors = {
            'average_duration': 300.0,
            'recent_build_count': 10,
            'success_rate': 0.9,
            'total_lines': 1000,
            'error_count': 0,
            'warning_count': 0
        }
        
        # Data with many errors
        data_with_errors = {
            'average_duration': 300.0,
            'recent_build_count': 10,
            'success_rate': 0.5,
            'total_lines': 1000,
            'error_count': 10,
            'warning_count': 5
        }
        
        result_no_errors = predictor.predict(data_no_errors)
        result_with_errors = predictor.predict(data_with_errors)
        
        # Duration should be higher with errors
        assert result_with_errors['predicted_duration'] >= result_no_errors['predicted_duration']
    
    def test_get_model_info(self):
        """Test model info retrieval"""
        predictor = DurationPredictor()
        info = predictor.get_model_info()
        
        assert 'type' in info
        assert 'algorithm' in info
        assert 'features' in info
        assert info['type'] == 'DurationPredictor'


class TestModelIntegration:
    """Test integration between models"""
    
    def test_both_models_together(self):
        """Test using both models on same data"""
        failure_predictor = FailurePredictor()
        duration_predictor = DurationPredictor()
        
        data = {
            'project_slug': 'gh/test/repo',
            'success_rate': 0.7,
            'failure_count': 3,
            'average_duration': 300.0,
            'recent_build_count': 10,
            'error_count': 5,
            'warning_count': 2,
            'total_lines': 1000,
            'error_types': {'test': 3, 'compilation': 2}
        }
        
        failure_result = failure_predictor.predict(data)
        duration_result = duration_predictor.predict(data)
        
        # Both should return valid results
        assert failure_result is not None
        assert duration_result is not None
        
        # High failure probability should correlate with longer duration
        if failure_result['failure_probability'] > 0.7:
            # Failed builds often take longer
            assert duration_result['predicted_duration'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
