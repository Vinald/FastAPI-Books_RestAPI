import logging
from typing import Optional

import redis.asyncio as redis
from redis.exceptions import ConnectionError, RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async Redis connection pool
redis_pool = redis.ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

# Token blacklist Redis client
token_blacklist = redis.Redis(connection_pool=redis_pool)

# Key prefix for blacklisted tokens
TOKEN_BLACKLIST_PREFIX = "blacklist:token:"

# Flag to track Redis availability
_redis_available: Optional[bool] = None


async def check_redis_connection() -> bool:
    """Check if Redis is available."""
    global _redis_available
    try:
        await token_blacklist.ping()
        _redis_available = True
        return True
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis is not available: {e}")
        _redis_available = False
        return False


async def is_redis_available() -> bool:
    """Return cached Redis availability status or check if unknown."""
    global _redis_available
    if _redis_available is None:
        return await check_redis_connection()
    return _redis_available


async def add_token_to_blacklist(jti: str, expires_in: int) -> bool:
    """
    Add a token to the blacklist.

    Args:
        jti: JWT Token ID (unique identifier for the token)
        expires_in: Time in seconds until the token expires (we only need to keep it blacklisted until then)

    Returns:
        True if successfully added, False otherwise
    """
    try:
        key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
        # Set the token in Redis with expiration (no need to keep it after token would expire anyway)
        await token_blacklist.setex(key, expires_in, "revoked")
        return True
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to add token to blacklist: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding token to blacklist: {e}")
        return False


async def is_token_blacklisted(jti: str) -> bool:
    """
    Check if a token is blacklisted.

    Args:
        jti: JWT Token ID to check

    Returns:
        True if token is blacklisted, False otherwise
    """
    try:
        key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
        result = await token_blacklist.get(key)
        return result is not None
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis unavailable when checking blacklist: {e}")
        # If Redis is unavailable, fail open (allow the token)
        # You might want to fail closed in high-security environments
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking token blacklist: {e}")
        return False


async def remove_token_from_blacklist(jti: str) -> bool:
    """
    Remove a token from the blacklist (if needed).

    Args:
        jti: JWT Token ID to remove

    Returns:
        True if successfully removed, False otherwise
    """
    try:
        key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
        await token_blacklist.delete(key)
        return True
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to remove token from blacklist: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error removing token from blacklist: {e}")
        return False


async def blacklist_all_user_tokens(user_uuid: str, expires_in: int) -> bool:
    """
    Add a marker to blacklist all tokens for a user issued before now.
    Useful for "logout from all devices" functionality.

    Args:
        user_uuid: User's UUID
        expires_in: Time in seconds (should match max token lifetime)

    Returns:
        True if successful, False otherwise
    """
    try:
        key = f"blacklist:user:{user_uuid}"
        import time
        # Store the timestamp - any token issued before this is invalid
        await token_blacklist.setex(key, expires_in, str(int(time.time())))
        return True
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to blacklist all user tokens: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error blacklisting all user tokens: {e}")
        return False


async def is_user_token_blacklisted(user_uuid: str, token_iat: int) -> bool:
    """
    Check if a user's tokens issued before a certain time are blacklisted.

    Args:
        user_uuid: User's UUID
        token_iat: Token's issued-at timestamp

    Returns:
        True if token should be considered blacklisted, False otherwise
    """
    try:
        key = f"blacklist:user:{user_uuid}"
        blacklist_time = await token_blacklist.get(key)
        if blacklist_time is None:
            return False
        return token_iat < int(blacklist_time)
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis unavailable when checking user token blacklist: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking user token blacklist: {e}")
        return False


async def close_redis_connection():
    """Close Redis connection pool."""
    try:
        await token_blacklist.close()
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
