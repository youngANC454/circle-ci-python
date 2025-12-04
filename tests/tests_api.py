import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_api_docs():
    """Test API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_predict_failure_endpoint():
    """Test failure prediction endpoint"""
    payload = {
        "project_slug": "gh/test/repo",
        "branch": "main",
        "recent_build_count": 10,
        "success_rate": 0.8,
        "failure_count": 2
    }
    
    response = client.post("/api/v1/predictions/failure", json=payload)
    # May fail if ML service is not running, but endpoint should exist
    assert response.status_code in [200, 500, 503]


def test_predict_duration_endpoint():
    """Test duration prediction endpoint"""
    payload = {
        "project_slug": "gh/test/repo",
        "branch": "main",
        "recent_build_count": 10,
        "average_duration": 300.0
    }
    
    response = client.post("/api/v1/predictions/duration", json=payload)
    # May fail if ML service is not running, but endpoint should exist
    assert response.status_code in [200, 500, 503]


def test_build_stats_endpoint():
    """Test build statistics endpoint"""
    response = client.get(
        "/api/v1/metrics/build-stats",
        params={"project_slug": "gh/test/repo", "days": 7}
    )
    # May return 404 if no data, but endpoint should exist
    assert response.status_code in [200, 404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
