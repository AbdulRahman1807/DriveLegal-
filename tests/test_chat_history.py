import pytest
import fakeredis.aioredis
from backend.chat.history import ChatHistoryManager
from backend.config import settings
import uuid

@pytest.fixture
async def mock_history_manager():
    manager = ChatHistoryManager()
    # Override client with fakeredis
    manager.client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield manager
    await manager.client.close()

@pytest.mark.asyncio
async def test_sliding_window_eviction(mock_history_manager):
    session_id = str(uuid.uuid4())
    
    # Insert 15 messages (over the 10 message limit)
    for i in range(15):
        role = "user" if i % 2 == 0 else "model"
        await mock_history_manager.add_message(session_id, role, f"Message {i}")
        
    # Fetch history
    history = await mock_history_manager.get_history(session_id)
    
    # Verify exactly 10 messages remain
    assert len(history) == 10, f"Expected 10 messages in sliding window, got {len(history)}"
    
    # Verify it kept the MOST RECENT messages (Message 5 to Message 14)
    assert history[-1]["content"] == "Message 14"
    assert history[0]["content"] == "Message 5"
