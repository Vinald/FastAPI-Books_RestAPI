"""
Rate Limiting Module

Implements request throttling using SlowAPI with Redis backend.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    Uses user ID if authenticated, otherwise uses IP address.
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.uuid}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance with Redis storage
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100/minute"],  # Default rate limit
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
    strategy="fixed-window",
)


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "error": "rate_limit_exceeded",
            "retry_after": exc.detail,
            "message": f"Rate limit exceeded. Please try again later."
        },
        headers={
            "Retry-After": str(exc.detail),
            "X-RateLimit-Limit": request.headers.get("X-RateLimit-Limit", ""),
            "X-RateLimit-Remaining": "0",
        }
    )


# Rate limit decorators for common use cases
def rate_limit(limit: str = "10/minute"):
    """
    Rate limit decorator for endpoints.

    Usage:
        @router.get("/endpoint")
        @rate_limit("5/minute")
        async def endpoint():
            ...
    """
    return limiter.limit(limit)


# Predefined rate limiters
auth_limiter = limiter.limit("5/minute")  # Strict for auth endpoints
api_limiter = limiter.limit("60/minute")  # Standard API rate
upload_limiter = limiter.limit("10/minute")  # File uploads
search_limiter = limiter.limit("30/minute")  # Search operations
