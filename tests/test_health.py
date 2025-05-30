import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "PAMP Submissions Service" in data["message"]


def test_health_endpoint():
    """Test the basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_swagger_ui_accessible():
    """Test that Swagger UI is accessible"""
    response = client.get("/swagger-ui")
    assert response.status_code == 200


def test_openapi_spec_accessible():
    """Test that OpenAPI spec is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data 