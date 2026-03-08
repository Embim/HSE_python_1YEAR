import redis.asyncio as aioredis

from src.config import settings
from src.logger import api_logger

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client
    if not settings.REDIS_URL:
        api_logger.warning("REDIS_URL not set — cache disabled")
        return
    try:
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await client.ping()
        redis_client = client
        api_logger.info("Redis connected: %s", settings.REDIS_URL)
    except Exception as e:
        api_logger.warning("Redis unavailable (%s) — cache disabled", e)


async def close_redis():
    if redis_client:
        await redis_client.aclose()
        api_logger.info("Redis connection closed")


async def cache_get(key: str) -> str | None:
    if redis_client is None:
        return None
    value = await redis_client.get(key)
    if value is not None:
        api_logger.debug("CACHE HIT — %s", key)
    else:
        api_logger.debug("CACHE MISS — %s", key)
    return value


async def cache_set(key: str, value: str, ttl: int = 3600):
    if redis_client is None:
        return
    await redis_client.set(key, value, ex=ttl)
    api_logger.debug("CACHE SET — %s (ttl=%ds)", key, ttl)


async def cache_delete(key: str):
    if redis_client is None:
        return
    await redis_client.delete(key)
    api_logger.debug("CACHE DEL — %s", key)
