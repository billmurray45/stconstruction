import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.csrf import SimpleCSRFMiddleware
from app.core.database import get_session
from app.landing.service import SiteSettingsService

from app.admin import admin_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.news.routes import router as news_router
from app.landing.routes import router as landing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async for session in get_session():
        try:
            await SiteSettingsService.initialize_settings(session)
        finally:
            break
    yield

app = FastAPI(
    title="Standart Construction",
    description="SSR Landing website for Standart Construction",
    version="1.0",
    lifespan=lifespan,
)


# CSRF Protection
app.add_middleware(
    SimpleCSRFMiddleware,
    token_name="csrf_token",
    header_name="x-csrf-token",
    exempt_paths=["/static"],
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
