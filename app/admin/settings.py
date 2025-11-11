from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pathlib import Path

import uuid
import os

from app.core.config.database import get_session
from app.core.web.templates import templates
from app.core.security.file_validator import validate_image_upload, save_uploaded_file, FileValidationError, MAX_LOGO_SIZE

from app.users.models import User
from app.auth.dependencies import require_superuser
from app.landing.service import SiteSettingsService
from app.landing.schemas import SiteSettingsUpdate

router = APIRouter(prefix="/settings", tags=["admin-settings"])

# Путь для сохранения логотипа
UPLOAD_DIR = Path("app/static/uploads/settings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def admin_settings_page(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    settings = await SiteSettingsService.get_settings(session)
    return templates.TemplateResponse(
        "admin/settings/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "settings": settings
        }
    )


@router.post("/", response_class=HTMLResponse)
async def admin_settings_update(
    request: Request,
    company_name: str = Form(...),
    logo: Optional[UploadFile] = File(None),
    phone_primary: Optional[str] = Form(None),
    phone_secondary: Optional[str] = Form(None),
    email_general: Optional[str] = Form(None),
    email_orders: Optional[str] = Form(None),
    addresses_text: Optional[str] = Form(None),
    social_instagram: Optional[str] = Form(None),
    social_facebook: Optional[str] = Form(None),
    social_whatsapp: Optional[str] = Form(None),
    social_telegram: Optional[str] = Form(None),
    social_youtube: Optional[str] = Form(None),
    working_hours: Optional[str] = Form(None),
    inn: Optional[str] = Form(None),
    bin: Optional[str] = Form(None),
    legal_address: Optional[str] = Form(None),
    meta_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    meta_keywords: Optional[str] = Form(None),
    stats_projects_completed: Optional[str] = Form(None),
    stats_clients: Optional[str] = Form(None),
    stats_years_experience: Optional[str] = Form(None),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    """Обновление настроек сайта"""
    try:
        settings = await SiteSettingsService.get_settings(session)

        # Обработка логотипа
        logo_path = settings.logo_path
        if logo and logo.filename:
            # Валидация логотипа (меньший лимит размера)
            await validate_image_upload(
                logo,
                max_size=MAX_LOGO_SIZE,
                field_name="логотип"
            )

            file_extension = os.path.splitext(logo.filename)[1].lower()
            unique_filename = f"logo_{uuid.uuid4()}{file_extension}"

            # Сохранение файла
            await save_uploaded_file(logo, UPLOAD_DIR, unique_filename)

            logo_path = f"/static/uploads/settings/{unique_filename}"

        # Преобразование addresses_text в JSON (простой вариант)
        addresses_json = None
        if addresses_text:
            addresses_json = {"text": addresses_text}

        # Обработка числовых полей (пустые строки -> None)
        stats_projects_int = int(stats_projects_completed) if stats_projects_completed and stats_projects_completed.strip() else 0
        stats_clients_int = int(stats_clients) if stats_clients and stats_clients.strip() else 0
        stats_experience_int = int(stats_years_experience) if stats_years_experience and stats_years_experience.strip() else 0

        # Создаем схему для обновления
        settings_data = SiteSettingsUpdate(
            company_name=company_name,
            logo_path=logo_path,
            phone_primary=phone_primary,
            phone_secondary=phone_secondary,
            email_general=email_general,
            email_orders=email_orders,
            addresses=addresses_json,
            social_instagram=social_instagram,
            social_facebook=social_facebook,
            social_whatsapp=social_whatsapp,
            social_telegram=social_telegram,
            social_youtube=social_youtube,
            working_hours=working_hours,
            inn=inn,
            bin=bin,
            legal_address=legal_address,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            stats_projects_completed=stats_projects_int,
            stats_clients=stats_clients_int,
            stats_years_experience=stats_experience_int
        )

        await SiteSettingsService.update_settings(session, settings_data)
        return RedirectResponse(url="/admin/settings?success=updated", status_code=303)

    except FileValidationError as e:
        return RedirectResponse(
            url=f"/admin/settings?error={e.detail}",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/settings?error={str(e)}",
            status_code=303
        )
