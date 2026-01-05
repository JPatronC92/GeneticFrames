"""
Cache Manager - Redis with in-memory fallback
"""

import json
from typing import Optional, Any
from loguru import logger
from app.core.config import settings

# Try to import Redis, but don't fail if not available
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache fallback")


class CacheManager:
    """Cache manager with Redis and in-memory fallback"""
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.memory_cache: dict = {}
        self.enabled = settings.REDIS_ENABLED and REDIS_AVAILABLE
    
    async def connect(self):
        """Connect to Redis"""
        if not self.enabled:
            logger.info("Cache: Using in-memory fallback")
            return
        
        try:
            self.redis_client = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Falling back to in-memory cache")
            self.enabled = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.enabled and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to memory cache
        return self.memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS):
        """Set value in cache with TTL"""
        serialized = json.dumps(value)
        
        if self.enabled and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, serialized)
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to memory cache (no TTL in memory)
        self.memory_cache[key] = value
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if self.enabled and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        self.memory_cache.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if self.enabled and self.redis_client:
            try:
                return await self.redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
        
        return key in self.memory_cache
    
    async def ping(self):
        """Test cache connection"""
        if self.enabled and self.redis_client:
            await self.redis_client.ping()
        return True


# Global cache manager instance
cache_manager = CacheManager()
