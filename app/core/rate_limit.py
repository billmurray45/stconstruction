"""
Rate Limiting Configuration for FastAPI
Uses slowapi for request rate limiting
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting
    Uses IP address by default, but can be extended to use user_id for authenticated users
    """
    # For authenticated users, use user_id if available
    if hasattr(request.state, "current_user") and request.state.current_user:
        return f"user:{request.state.current_user.id}"

    # Otherwise use IP address
    return get_remote_address(request)


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=["200/hour"],  # Global default: 200 requests per hour per IP
    storage_uri=settings.REDIS_URL if settings.is_production else "memory://",  # In-memory storage (use Redis in production)
    headers_enabled=True,  # Add X-RateLimit-* headers to responses
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    Returns user-friendly JSON response
    """
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Too Many Requests",
            "message": "Слишком много запросов. Пожалуйста, попробуйте позже.",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else None
        },
        headers={"Retry-After": "60"}  # Suggest retry after 60 seconds
    )
