"""
Context processors для глобальных переменных в шаблонах
"""
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.landing.service import SiteSettingsService


async def get_site_settings_context(session: AsyncSession) -> dict:
    """
    Получить настройки сайта для использования в шаблонах

    Использование в шаблоне:
    {{ site.company_name }}
    {{ site.phone_primary }}
    {{ site.email_general }}
    """
    try:
        settings = await SiteSettingsService.get_settings(session)
        return {
            "site": settings
        }
    except Exception:
        return {"site": None}
