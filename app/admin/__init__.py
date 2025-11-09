from fastapi import APIRouter

# Main admin router
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Import and register routers from submodules
from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .news import router as news_router
from .users import router as users_router
from .cities import router as cities_router
from .projects import router as projects_router
from .settings import router as settings_router

# Register routers
admin_router.include_router(auth_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(news_router)
admin_router.include_router(users_router)
admin_router.include_router(cities_router)
admin_router.include_router(projects_router)
admin_router.include_router(settings_router)

__all__ = ["admin_router"]
