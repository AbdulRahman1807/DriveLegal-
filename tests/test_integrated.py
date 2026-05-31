import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.security import create_access_token
from backend.models.user import User
from backend.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Helper fixture to create a valid JWT access token for integrated testing
@pytest.fixture
def auth_headers(prepare_database, db_session):
    # Create a dummy user in the SQLite memory db first
    async def create_user():
        async with db_session as session:
            user = User(
                id=uuid.uuid4(),
                email="testuser@drivelegal.app",
                hashed_password=hash_password("password123"),
                role="user",
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    # We must run this async inside the synchronous fixture
    import asyncio
    loop = asyncio.get_event_loop()
    user = loop.run_until_complete(create_user())
    
    token = create_access_token(str(user.id), user.role)
    return {"Authorization": f"Bearer {token}"}

client = TestClient(app)

def test_api_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "DriveLegal HHA-VRAG+ Engine"}

def test_api_chat_valid(auth_headers):
    response = client.post(
        "/api/v1/chat", 
        json={"query": "Test query", "session_id": "test_session_id"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "citations" in data
    assert "fines" in data
    # We should have retrieved something from seeds
    assert len(data["citations"]) > 0

def test_api_chat_invalid_payload(auth_headers):
    payload = {
        "wrong_key": "What happens?"
    }
    response = client.post(
        "/api/v1/chat", 
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 422 # Pydantic validation error
