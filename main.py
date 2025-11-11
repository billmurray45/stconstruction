import uvicorn
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config.settings import settings
from app.core.config.logging import setup_logging
from app.core.security.csrf import SimpleCSRFMiddleware
from app.core.config.database import get_session
from app.core.security.rate_limit import limiter, rate_limit_exceeded_handler
from app.landing.service import SiteSettingsService
from app.admin.init_admin import initialize_admin_user
from slowapi.errors import RateLimitExceeded

from app.admin import admin_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.news.routes import router as news_router
from app.landing.routes import router as landing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Standart Construction application...")

    # Инициализация настроек сайта и админа
    async for session in get_session():
        try:
            await SiteSettingsService.initialize_settings(session)
            logger.info("Site settings initialized successfully")

            # Создание админа при первом запуске
            await initialize_admin_user(session)
            logger.info("Admin user initialization completed")
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
        finally:
            break

    yield

    logger.info("Shutting down Standart Construction application...")

app = FastAPI(
    title="Standart Construction",
    description="SSR Landing website for Standart Construction",
    version="1.0",
    lifespan=lifespan,
)


# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CSRF Protection
app.add_middleware(
    SimpleCSRFMiddleware,
    token_name="csrf_token",
    header_name="x-csrf-token",
    exempt_paths=["/static", "/health"],
)

# Session Middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="stconstruction_session",
    max_age=14 * 24 * 60 * 60,
    same_site="lax",
    https_only=settings.is_production
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(landing_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(admin_router)


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "construction",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health/db", tags=["Health"])
async def health_check_db():
    try:
        async for session in get_session():
            try:
                # Simple query to check DB connection
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                result.scalar()

                return {
                    "status": "healthy",
                    "service": "construction",
                    "database": "connected"
                }
            finally:
                break
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Database health check failed: {e}")

        from fastapi import Response
        return Response(
            content='{"status": "unhealthy", "database": "disconnected"}',
            status_code=503,
            media_type="application/json"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
