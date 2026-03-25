import redis.asyncio as redis
from src.helpers.config import settings

# Global Redis client for FastAPI
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_jti_blacklisted(jti: str) -> bool:
    """Check if a JWT ID is in the Redis blacklist."""
    return await redis_client.exists(f"jti_blacklist:{jti}") > 0

async def blacklist_jti(jti: str, expire_days: int) -> None:
    """Add a JWT ID to the Redis blacklist with expiration."""
    # Convert days to seconds
    expire_seconds = expire_days * 24 * 60 * 60
    await redis_client.setex(f"jti_blacklist:{jti}", expire_seconds, "revoked")
