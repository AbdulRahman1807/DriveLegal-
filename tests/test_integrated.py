import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}

def test_api_chat_valid():
    response = client.post(
        "/api/v1/chat", 
        json={"query": "Test query", "session_id": "test_session_id"},
        headers={"Authorization": "Bearer drivelegal-secret-dev-key"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "citations" in data
    assert "fines" in data
    # We should have retrieved something from seeds
    assert len(data["citations"]) > 0

def test_api_chat_invalid_payload():
    payload = {
        "wrong_key": "What happens?"
    }
    response = client.post(
        "/api/v1/chat", 
        json=payload,
        headers={"Authorization": "Bearer drivelegal-secret-dev-key"}
    )
    assert response.status_code == 422 # Pydantic validation error
