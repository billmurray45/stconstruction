from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from .models import SiteSettings


class SiteSettingsRepository:
    """
    Репозиторий для работы с настройками сайта
    Singleton pattern - всегда работает с записью id=1
    """

    SETTINGS_ID = 1

    @staticmethod
    async def get_settings(session: AsyncSession) -> Optional[SiteSettings]:
        result = await session.execute(
            select(SiteSettings).where(SiteSettings.id == SiteSettingsRepository.SETTINGS_ID)
        )
        return result.scalars().first()

    @staticmethod
    async def get_or_create_settings(session: AsyncSession) -> SiteSettings:
        settings = await SiteSettingsRepository.get_settings(session)

        if not settings:
            settings = SiteSettings(
                id=SiteSettingsRepository.SETTINGS_ID,
                company_name="Standart Construction"
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        return settings

    @staticmethod
    async def update_settings(session: AsyncSession, settings: SiteSettings) -> SiteSettings:
        await session.commit()
        await session.refresh(settings)
        return settings

    @staticmethod
    async def create_default_settings(session: AsyncSession) -> SiteSettings:

        settings = SiteSettings(
            id=SiteSettingsRepository.SETTINGS_ID,
            company_name="Standart Construction",
            phone_primary="+7 (777) 123-45-67",
            email_general="info@standart-construction.kz",
            working_hours="Пн-Пт: 9:00-18:00",
            meta_title="Standart Construction - Строительная компания в Казахстане",
            meta_description="Строительство жилых комплексов комфорт, премиум и бизнес класса",
            stats_years_experience=10,
            stats_projects_completed=50,
            stats_clients=1000
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
        return settings
