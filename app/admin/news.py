from fastapi import APIRouter, Request, Form, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

import uuid

from app.core.config.database import get_session
from app.core.web.templates import templates
from app.core.utils.helpers import generate_slug
from app.core.security.file_validator import validate_image_upload, save_uploaded_file, FileValidationError

from app.auth.dependencies import require_superuser
from app.users.models import User
from app.news.service import (
    get_all_news,
    get_news_by_id,
    create_news,
    update_news_service,
    delete_news_service
)
from app.news.schemas import NewsCreate, NewsUpdate


router = APIRouter(prefix="/news", tags=["Admin News"])


@router.get("/", response_class=HTMLResponse)
async def admin_news_list(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    all_news = await get_all_news(session, published_only=False)

    return templates.TemplateResponse(
        "admin/news/list.html",
        {
            "request": request,
            "current_user": current_user,
            "news_list": all_news
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def admin_news_add_form(
    request: Request,
    current_user: User = Depends(require_superuser)
):
    return templates.TemplateResponse(
        "admin/news/add.html",
        {
            "request": request,
            "current_user": current_user,
            "error": None
        }
    )


@router.post("/add")
async def admin_news_add(
    request: Request,
    title: str = Form(...),
    slug: str = Form(""),
    description: str = Form(...),
    content: str = Form(...),
    is_published: bool = Form(False),
    image: UploadFile = File(...),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(title)

        if image and image.filename:
            # Валидация загружаемого изображения
            await validate_image_upload(image, field_name="изображение новости")

            # Генерация уникального имени для файла
            file_extension = Path(image.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Сохранение файла
            destination_dir = Path("app/static/uploads/news")
            await save_uploaded_file(image, destination_dir, unique_filename)

            image_path = f"uploads/news/{unique_filename}"
        else:
            image_path = "uploads/news/default.jpg"

        news_data = NewsCreate(
            title=title,
            slug=slug,
            description=description,
            content=content,
            image_path=image_path,
            is_published=is_published
        )

        await create_news(session, news_data)

        return RedirectResponse(url="/admin/news?success=created", status_code=302)

    except FileValidationError as e:
        return templates.TemplateResponse(
            "admin/news/add.html",
            {
                "request": request,
                "current_user": current_user,
                "error": e.detail,
                "form_data": {
                    "title": title,
                    "slug": slug,
                    "description": description,
                    "content": content,
                    "is_published": is_published
                }
            },
            status_code=400
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            "admin/news/add.html",
            {
                "request": request,
                "current_user": current_user,
                "error": e.detail,
                "form_data": {
                    "title": title,
                    "slug": slug,
                    "description": description,
                    "content": content,
                    "is_published": is_published
                }
            },
            status_code=400
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/news/add.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"Ошибка при создании новости: {str(e)}",
                "form_data": {
                    "title": title,
                    "slug": slug,
                    "description": description,
                    "content": content,
                    "is_published": is_published
                }
            },
            status_code=500
        )


@router.get("/{news_id}/edit", response_class=HTMLResponse)
async def admin_news_edit_form(
    request: Request,
    news_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        news = await get_news_by_id(session, news_id)

        return templates.TemplateResponse(
            "admin/news/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "news": news,
                "error": None
            }
        )
    except HTTPException:
        return RedirectResponse(url="/admin/news?error=not_found", status_code=302)


@router.post("/{news_id}/edit")
async def admin_news_edit(
    request: Request,
    news_id: int,
    title: str = Form(...),
    slug: str = Form(""),
    description: str = Form(...),
    content: str = Form(...),
    is_published: bool = Form(False),
    image: UploadFile = File(None),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        news = await get_news_by_id(session, news_id)

        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(title)

        # Handle image upload if new image provided
        image_path = news.image_path
        if image and image.filename:
            # Валидация загружаемого изображения
            await validate_image_upload(image, field_name="изображение новости")

            file_extension = Path(image.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Сохранение файла
            destination_dir = Path("app/static/uploads/news")
            await save_uploaded_file(image, destination_dir, unique_filename)

            image_path = f"uploads/news/{unique_filename}"

            # Delete old image if exists and not default
            if news.image_path and news.image_path != "uploads/news/default.jpg":
                old_image_path = Path("app/static") / news.image_path
                if old_image_path.exists():
                    old_image_path.unlink()

        news_data = NewsUpdate(
            title=title,
            slug=slug,
            description=description,
            content=content,
            image_path=image_path,
            is_published=is_published
        )

        await update_news_service(session, news_id, news_data)

        return RedirectResponse(url="/admin/news?success=updated", status_code=302)

    except FileValidationError as e:
        news = await get_news_by_id(session, news_id)
        return templates.TemplateResponse(
            "admin/news/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "news": news,
                "error": e.detail
            },
            status_code=400
        )
    except HTTPException as e:
        news = await get_news_by_id(session, news_id)
        return templates.TemplateResponse(
            "admin/news/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "news": news,
                "error": e.detail
            },
            status_code=400
        )


@router.post("/{news_id}/delete")
async def admin_news_delete(
    news_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        news = await get_news_by_id(session, news_id)

        await delete_news_service(session, news_id)

        # Delete image file if not default
        if news.image_path and news.image_path != "uploads/news/default.jpg":
            image_path = Path("app/static") / news.image_path
            if image_path.exists():
                image_path.unlink()

        return RedirectResponse(url="/admin/news?success=deleted", status_code=302)

    except HTTPException:
        return RedirectResponse(url="/admin/news?error=delete_failed", status_code=302)
