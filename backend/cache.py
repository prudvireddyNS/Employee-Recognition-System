from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
import redis
from .config import get_settings

settings = get_settings()

async def setup_cache():
    redis_client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf8",
        decode_responses=True
    )
    FastAPICache.init(
        RedisBackend(redis_client),
        prefix="fastapi-cache",
        expire=300  # Default cache expiration of 5 minutes
    )
