"""Tests for health check endpoint."""
from fastapi.testclient import TestClient


def test_health_check_success(test_client: TestClient) -> None:
    """Test health check endpoint returns ok status."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data


def test_health_check_response_structure(test_client: TestClient) -> None:
    """Test health check response has correct structure."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"status", "database"}
    assert isinstance(data["status"], str)
    assert isinstance(data["database"], str)


def test_health_check_database_connected(test_client: TestClient) -> None:
    """Test health check detects database connection."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["database"] == "connected"
