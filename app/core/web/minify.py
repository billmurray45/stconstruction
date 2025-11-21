"""
HTML Minification Middleware
Automatically minifies HTML responses in production
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import htmlmin

logger = logging.getLogger(__name__)


class HTMLMinifyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to minify HTML responses in production
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only minify HTML responses in production
        if not self.enabled:
            return response

        # Check if response is HTML
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return response

        # Get response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            # Minify HTML
            html_content = body.decode("utf-8")
            minified_html = htmlmin.minify(
                html_content,
                remove_comments=True,
                remove_empty_space=True,
                remove_all_empty_space=False,  # Keep some spaces for readability
                reduce_boolean_attributes=True,
                remove_optional_attribute_quotes=False,  # Keep quotes for security
                convert_charrefs=True,
                keep_pre=True  # Preserve <pre> tags
            )

            # Calculate compression ratio
            original_size = len(body)
            minified_size = len(minified_html.encode("utf-8"))
            saved_percent = (1 - minified_size / original_size) * 100 if original_size > 0 else 0

            logger.debug(
                f"HTML minified: {request.url.path} | "
                f"{original_size} -> {minified_size} bytes | "
                f"Saved {saved_percent:.1f}%"
            )

            # Create new response with minified content
            return Response(
                content=minified_html,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        except Exception as e:
            logger.warning(f"Failed to minify HTML for {request.url.path}: {str(e)}")
            # Return original response if minification fails
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
