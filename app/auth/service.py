from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import verify_password
from app.users.models import User
from app.users.repository import UserRepository


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    """Аутентификация пользователя по email и паролю."""
    user = await UserRepository.get_user_by_email(session, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            401,
            detail="Неверный Email или пароль"
        )

    if not user.is_active:
        raise HTTPException(
            403,
            detail="Доступ запрещен. Пользователь заблокирован!"
        )

    return user
