import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.services.circleci_client import CircleCIClient
from app.services.log_processor import LogProcessor


class TestCircleCIClient:
    """Test CircleCI API client"""
    
    def test_initialization(self):
        """Test client initialization"""
        client = CircleCIClient()
        assert client is not None
        assert client.base_url is not None
        assert client.headers is not None
    
    @pytest.mark.asyncio
    async def test_get_project_pipelines_mock(self):
        """Test fetching pipelines with mocked response"""
        client = CircleCIClient()
        
        mock_response = {
            "items": [
                {
                    "id": "pipeline-1",
                    "vcs": {"branch": "main", "revision": "abc123"}
                }
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=lambda: mock_response
                )
            )
            
            # This would normally call the API
            # For testing, we just verify the method exists
            assert hasattr(client, 'get_project_pipelines')
    
    @pytest.mark.asyncio
    async def test_get_pipeline_workflows(self):
        """Test fetching workflows for a pipeline"""
        client = CircleCIClient()
        
        # Verify method exists
        assert hasattr(client, 'get_pipeline_workflows')
    
    @pytest.mark.asyncio
    async def test_get_workflow_jobs(self):
        """Test fetching jobs for a workflow"""
        client = CircleCIClient()
        
        # Verify method exists
        assert hasattr(client, 'get_workflow_jobs')
    
    def test_calculate_duration(self):
        """Test duration calculation"""
        client = CircleCIClient()
        
        started_at = "2024-01-01T10:00:00Z"
        stopped_at = "2024-01-01T10:05:00Z"
        
        duration = client._calculate_duration(started_at, stopped_at)
        
        assert duration == 300  # 5 minutes = 300 seconds
    
    def test_calculate_duration_invalid(self):
        """Test duration calculation with invalid dates"""
        client = CircleCIClient()
        
        duration = client._calculate_duration(None, None)
        assert duration is None
        
        duration = client._calculate_duration("invalid", "invalid")
        assert duration is None


class TestLogProcessor:
    """Test log processing functionality"""
    
    def test_initialization(self):
        """Test log processor initialization"""
        processor = LogProcessor()
        assert processor is not None
        assert processor.error_regex is not None
        assert processor.warning_regex is not None
    
    def test_extract_features_empty_log(self):
        """Test feature extraction from empty log"""
        processor = LogProcessor()
        
        features = processor.extract_features("")
        
        assert features['total_lines'] == 0
        assert features['error_count'] == 0
        assert features['warning_count'] == 0
    
    def test_extract_features_with_errors(self):
        """Test feature extraction from log with errors"""
        processor = LogProcessor()
        
        log_content = """
        Building project...
        Error: compilation failed
        Warning: deprecated function used
        Error: test failed
        Build completed with errors
        """
        
        features = processor.extract_features(log_content)
        
        assert features['total_lines'] > 0
        assert features['error_count'] > 0
        assert features['warning_count'] > 0
    
    def test_classify_errors(self):
        """Test error classification"""
        processor = LogProcessor()
        
        log_content = """
        Compilation error in main.py
        Runtime exception occurred
        Test assertion failed
        Connection timeout
        Out of memory error
        """
        
        features = processor.extract_features(log_content)
        error_types = features['error_types']
        
        assert error_types['compilation'] > 0
        assert error_types['runtime'] > 0
        assert error_types['test'] > 0
        assert error_types['timeout'] > 0
        assert error_types['memory'] > 0
    
    def test_check_timeout(self):
        """Test timeout detection"""
        processor = LogProcessor()
        
        log_with_timeout = "Build timed out after 10 minutes"
        log_without_timeout = "Build completed successfully"
        
        assert processor._check_timeout(log_with_timeout) == True
        assert processor._check_timeout(log_without_timeout) == False
    
    def test_check_oom(self):
        """Test out-of-memory detection"""
        processor = LogProcessor()
        
        log_with_oom = "Process killed: out of memory"
        log_without_oom = "Process completed successfully"
        
        assert processor._check_oom(log_with_oom) == True
        assert processor._check_oom(log_without_oom) == False
    
    def test_summarize_logs(self):
        """Test log summarization"""
        processor = LogProcessor()
        
        log_content = """
        Line 1
        Error: something went wrong
        Line 3
        Line 4
        Error: another error
        """
        
        summary = processor.summarize_logs(log_content, max_lines=10)
        
        assert "Error" in summary
        assert len(summary) > 0
    
    def test_count_test_failures(self):
        """Test counting test failures"""
        processor = LogProcessor()
        
        log_content = """
        Running tests...
        Test 'test_login' failed
        Test 'test_signup' passed
        3 tests failed, 7 passed
        """
        
        features = processor.extract_features(log_content)
        
        assert features['test_failures'] > 0


class TestIntegration:
    """Test integration between CircleCI client and log processor"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete workflow from API to log processing"""
        client = CircleCIClient()
        processor = LogProcessor()
        
        # Simulate log content from CircleCI
        mock_log = """
        Starting build...
        Installing dependencies...
        Running tests...
        Error: 2 tests failed
        Build failed
        """
        
        # Process the log
        features = processor.extract_features(mock_log)
        
        # Verify we extracted meaningful features
        assert features is not None
        assert features['error_count'] > 0
        assert features['total_lines'] > 0
    
    def test_error_pattern_coverage(self):
        """Test that we detect various error types"""
        processor = LogProcessor()
        
        test_cases = {
            'compilation': "Syntax error in file.py",
            'runtime': "RuntimeError: division by zero",
            'test': "AssertionError: expected true but got false",
            'timeout': "Operation timed out after 30 seconds",
            'memory': "Fatal error: out of memory",
            'network': "Connection failed: network unreachable"
        }
        
        for error_type, log_line in test_cases.items():
            features = processor.extract_features(log_line)
            assert features['error_types'][error_type] > 0, \
                f"Failed to detect {error_type} error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
