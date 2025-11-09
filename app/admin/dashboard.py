from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.templates import templates
from app.auth.dependencies import require_superuser
from app.users.models import User
from app.news.repository import NewsRepository
from app.users.repository import UserRepository


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    all_news = await NewsRepository.get_all_news(session, published_only=False)
    published_news = [news for news in all_news if news.is_published]

    all_users = await UserRepository.get_all_users(session)

    stats = {
        "total_news": len(all_news),
        "published_news": len(published_news),
        "draft_news": len(all_news) - len(published_news),
        "total_users": len(all_users),
    }

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats
        }
    )
