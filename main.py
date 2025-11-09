import uvicorn

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.database import get_session
from app.landing.service import SiteSettingsService

from app.admin import admin_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.news.routes import router as news_router
from app.landing.routes import router as landing_router

app = FastAPI(
    title="Standart Construction",
    description="SSR Landing website for Standart Construction",
    version="1.0",
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="stconstruction_session",
    max_age=14 * 24 * 60 * 60,
    same_site="lax",
    https_only=False  # Изменить на True в Production
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(landing_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    async for session in get_session():
        try:
            # Инициализируем настройки сайта
            await SiteSettingsService.initialize_settings(session)
        finally:
            break


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
