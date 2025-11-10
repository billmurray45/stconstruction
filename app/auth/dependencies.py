from typing import Optional

from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.users.models import User
from app.users.repository import UserRepository


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    """
    Dependency для получения текущего авторизованного пользователя из сессии
    """
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация"
        )

    user = await UserRepository.get_user_by_id(session, user_id)

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    if not user.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Пользователь заблокирован!"
        )

    return user


async def get_current_user_optional(request: Request, session: AsyncSession = Depends(get_session)) -> Optional[User]:
    """
    Dependency для получения текущего пользователя (опционально)
    """
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = await UserRepository.get_user_by_id(session, user_id)

    if not user or not user.is_active:
        request.session.clear()
        return None

    return user


async def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency для проверки прав суперпользователя
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен. Требуются права администратора"
        )

    return current_user


async def set_current_user_optional(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Зависимость, которая получает пользователя и добавляет его в request.state.
    Используется на уровне роутера, чтобы избежать повторений.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        request.state.current_user = None
        return

    user = await UserRepository.get_user_by_id(session, user_id)
    if not user or not user.is_active:
        request.state.current_user = None
        request.session.clear()
        return

    request.state.current_user = user
