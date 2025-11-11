"""
Admin user initialization
Creates default admin user on application startup if it doesn't exist
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from app.users.repository import UserRepository
from app.auth.security import get_password_hash
from app.core.config.settings import settings

logger = logging.getLogger(__name__)


async def initialize_admin_user(session: AsyncSession) -> None:
    """
    Initialize default admin user if it doesn't exist

    Args:
        session: Database session
    """
    try:
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info(f"Admin user already exists: {settings.ADMIN_EMAIL}")
            return

        # Create admin user directly
        admin_user = User(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            is_active=True,
            is_superuser=True
        )

        await UserRepository.create_user(session, admin_user)

        logger.info(f"Admin user created successfully: {admin_user.email}")

    except Exception as e:
        logger.error(f"Failed to initialize admin user: {e}")
        raise
