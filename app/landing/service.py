from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from .models import CallbackRequest
from .schemas import CallbackRequestCreate
from .models import SiteSettings
from .repository import SiteSettingsRepository
from .schemas import SiteSettingsUpdate


class SiteSettingsService:
    """Сервис для работы с настройками сайта"""

    @staticmethod
    async def get_settings(session: AsyncSession) -> SiteSettings:
        """
        Получить настройки сайта
        Если не существуют - создать с дефолтными значениями
        """
        return await SiteSettingsRepository.get_or_create_settings(session)

    @staticmethod
    async def update_settings(
        session: AsyncSession,
        settings_data: SiteSettingsUpdate
    ) -> SiteSettings:
        """Обновить настройки сайта"""
        settings = await SiteSettingsRepository.get_or_create_settings(session)

        # Обновляем все поля из схемы
        for field, value in settings_data.model_dump(exclude_unset=True).items():
            if hasattr(settings, field):
                setattr(settings, field, value)

        return await SiteSettingsRepository.update_settings(session, settings)

    @staticmethod
    async def initialize_settings(session: AsyncSession) -> SiteSettings:
        """
        Инициализировать настройки при первом запуске
        Можно вызвать из startup event
        """
        existing = await SiteSettingsRepository.get_settings(session)
        if existing:
            return existing

        return await SiteSettingsRepository.create_default_settings(session)


class LandingService:
    @staticmethod
    async def create_callback_request(session: AsyncSession, data: CallbackRequestCreate) -> CallbackRequest:
        new_request = CallbackRequest(
            name=data.name,
            phone=data.phone
        )
        session.add(new_request)
        await session.commit()
        await session.refresh(new_request)
        return new_request
