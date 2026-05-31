import json
import redis.asyncio as redis
import structlog
from typing import Optional, Any, Callable
from backend.config import settings

logger = structlog.get_logger(__name__)

class CacheService:
    _instance = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
        return cls._instance

    async def connect(self):
        if self._client is None:
            try:
                self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                # Ping to check connection
                await self._client.ping()
                logger.info("cache.connected", url=settings.REDIS_URL)
            except Exception as e:
                logger.error("cache.connection_failed", error=str(e))
                self._client = None

    async def get_client(self) -> Optional[redis.Redis]:
        if not self._client:
            await self.connect()
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        client = await self.get_client()
        if not client:
            return None
        
        try:
            val = await client.get(key)
            if val:
                logger.debug("cache.hit", key=key)
                return json.loads(val)
            logger.debug("cache.miss", key=key)
            return None
        except Exception as e:
            logger.error("cache.get_failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: int = settings.CACHE_TTL_SHORT):
        client = await self.get_client()
        if not client:
            return
            
        try:
            val_str = json.dumps(value, default=str)
            await client.set(key, val_str, ex=ttl)
            logger.debug("cache.set", key=key, ttl=ttl)
        except Exception as e:
            logger.error("cache.set_failed", key=key, error=str(e))

    async def delete(self, key: str):
        client = await self.get_client()
        if not client:
            return
            
        try:
            await client.delete(key)
            logger.debug("cache.delete", key=key)
        except Exception as e:
            logger.error("cache.delete_failed", key=key, error=str(e))

cache_service = CacheService()
