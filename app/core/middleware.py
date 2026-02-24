"""
Middleware for request/response logging and monitoring.
"""
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger
logger = logging.getLogger("bookapi")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.

    Features:
    - Unique request ID for tracing
    - Request duration measurement
    - Client IP logging
    - Status code logging
    - Error logging
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]

        # Store request_id in request state for use in routes/services
        request.state.request_id = request_id

        # Record start time
        start_time = time.perf_counter()

        # Get request info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""

        # Log incoming request
        logger.info(
            f"[{request_id}] ▶ {method} {path}"
            f"{f'?{query}' if query else ''} | "
            f"Client: {client_ip}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Determine log level based on status code
            status_code = response.status_code
            if status_code >= 500:
                log_func = logger.error
                status_icon = "✗"
            elif status_code >= 400:
                log_func = logger.warning
                status_icon = "⚠"
            else:
                log_func = logger.info
                status_icon = "✓"

            # Log response
            log_func(
                f"[{request_id}] {status_icon} {method} {path} | "
                f"Status: {status_code} | "
                f"Duration: {duration_ms:.2f}ms"
            )

            # Add request ID to response headers for client-side tracing
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.exception(
                f"[{request_id}] ✗ {method} {path} | "
                f"Error: {type(e).__name__}: {str(e)} | "
                f"Duration: {duration_ms:.2f}ms"
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
