from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.core.database import get_session
from app.core.templates import templates
from app.core.context_processors import get_site_settings_context
from app.auth.dependencies import set_current_user_optional

from .service import (
    get_news_by_id,
    get_news_by_slug,
    get_all_news,
)

router = APIRouter(
    prefix="/news",
    tags=["News"],
    dependencies=[Depends(set_current_user_optional)]
)

UPLOAD_DIR = Path("app/static/uploads/news")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def get_news_list(
    request: Request,
    published_only: bool = True,
    session: AsyncSession = Depends(get_session)
):
    news_list = await get_all_news(session, published_only)
    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "news/index.html",
        {
            "request": request,
            "news_list": news_list,
            **site_context
        }
    )


@router.get("/id/{news_id}", response_class=HTMLResponse)
async def get_news_by_id_route(
    request: Request,
    news_id: int,
    session: AsyncSession = Depends(get_session)
):
    news = await get_news_by_id(session, news_id)
    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "news/full_page.html",
        {
            "request": request,
            "news": news,
            **site_context
        }
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def get_news_by_slug_route(
    request: Request,
    slug: str,
    session: AsyncSession = Depends(get_session)
):
    news = await get_news_by_slug(session, slug)
    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "news/full_page.html",
        {
            "request": request,
            "news": news,
            **site_context
        }
    )
