"""
Simple CSRF Protection Middleware for FastAPI SSR applications
Works with hidden form fields and session-based tokens
"""
import secrets
from typing import Callable
from urllib.parse import parse_qs
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from starlette.datastructures import FormData


class SimpleCSRFMiddleware(BaseHTTPMiddleware):
    """
    Simple CSRF protection middleware that:
    1. Generates a token and stores it in session
    2. Validates token from POST data or headers
    3. Works with both HTML forms (hidden fields) and AJAX (headers)
    """

    def __init__(
        self,
        app,
        secret_key: str = None,
        token_name: str = "csrf_token",
        header_name: str = "x-csrf-token",
        exempt_methods: set = None,
        exempt_paths: list = None,
    ):
        super().__init__(app)
        self.token_name = token_name
        self.header_name = header_name
        self.exempt_methods = exempt_methods or {"GET", "HEAD", "OPTIONS", "TRACE"}
        self.exempt_paths = exempt_paths or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for safe methods
        if request.method in self.exempt_methods:
            response = await call_next(request)
            return response

        # Skip for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            response = await call_next(request)
            return response

        # Get token from session
        session_token = request.session.get(self.token_name)

        if not session_token:
            # No token in session - this shouldn't happen if session middleware is working
            return PlainTextResponse(
                "CSRF token missing from session",
                status_code=403
            )

        # Get submitted token from form data or header
        submitted_token = None

        # Check header first (for AJAX requests)
        submitted_token = request.headers.get(self.header_name)

        # If not in header, check form data
        if not submitted_token:
            # Get content type
            content_type = request.headers.get("content-type", "")

            # Only try to parse form data if it's application/x-www-form-urlencoded
            # For multipart/form-data, require header (too complex to parse and rebuild)
            if "application/x-www-form-urlencoded" in content_type:
                try:
                    # Read raw body
                    body = await request.body()

                    # Parse form data
                    body_str = body.decode('utf-8')
                    parsed_data = parse_qs(body_str)

                    # Get CSRF token
                    if self.token_name in parsed_data:
                        submitted_token = parsed_data[self.token_name][0]

                    # CRITICAL: Create a new receive function that returns the body again
                    async def new_receive():
                        return {"type": "http.request", "body": body, "more_body": False}

                    # Replace the receive function so FastAPI can read body again
                    request._receive = new_receive

                except Exception as e:
                    import logging
                    logging.error(f"CSRF middleware error parsing form: {e}")
                    pass
            elif "multipart/form-data" in content_type:
                # For file uploads, REQUIRE header (JavaScript handles this automatically)
                pass  # Token checked below

        # Validate token
        if not submitted_token:
            return PlainTextResponse(
                "CSRF token missing from request",
                status_code=403
            )

        if not secrets.compare_digest(session_token, submitted_token):
            return PlainTextResponse(
                "CSRF token verification failed",
                status_code=403
            )

        # Token is valid, proceed with request
        response = await call_next(request)
        return response


def generate_csrf_token(request: Request, token_name: str = "csrf_token") -> str:
    """
    Generate or retrieve CSRF token from session

    Args:
        request: FastAPI Request object
        token_name: Name of the token in session

    Returns:
        CSRF token string
    """
    # Check if token already exists in session
    if token_name in request.session:
        return request.session[token_name]

    # Generate new token
    token = secrets.token_urlsafe(32)
    request.session[token_name] = token

    return token


def get_csrf_token(request: Request, token_name: str = "csrf_token") -> str:
    """
    Get CSRF token from session (read-only)

    Args:
        request: FastAPI Request object
        token_name: Name of the token in session

    Returns:
        CSRF token string or empty string if not found
    """
    return request.session.get(token_name, "")
