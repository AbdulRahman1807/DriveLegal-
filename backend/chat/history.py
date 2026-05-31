import json
from typing import List, Dict
import structlog
import tiktoken
from backend.core.cache import cache_service

logger = structlog.get_logger(__name__)
# Using cl100k_base as a rough proxy for LLM tokens
encoding = tiktoken.get_encoding("cl100k_base")

class ChatHistoryManager:
    def __init__(self):
        self.ttl = 86400 # 24 hours

    async def add_message(self, session_id: str, role: str, content: str):
        try:
            client = await cache_service.get_client()
            if not client:
                return
                
            key = f"chat_history:{session_id}"
            message = json.dumps({"role": role, "content": content})
            await client.rpush(key, message)
            await client.expire(key, self.ttl)
            
            # Enforce max length of 10 messages
            await client.ltrim(key, -10, -1)
            
            # Token eviction logic
            messages = await client.lrange(key, 0, -1)
            total_tokens = 0
            for i in range(len(messages)-1, -1, -1):
                msg_content = json.loads(messages[i])["content"]
                total_tokens += len(encoding.encode(msg_content))
                if total_tokens > 4000:
                    # Evict everything from 0 to i
                    await client.ltrim(key, i + 1, -1)
                    break
        except Exception as e:
            logger.error(f"Redis error adding message: {e}")

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        try:
            client = await cache_service.get_client()
            if not client:
                return []
                
            key = f"chat_history:{session_id}"
            messages = await client.lrange(key, 0, -1)
            return [json.loads(m) for m in messages]
        except Exception as e:
            logger.error(f"Redis error fetching history: {e}")
            return []
