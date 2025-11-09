from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_password_hash

from .schemas import RegisterForm, UserUpdate
from .models import User
from .repository import UserRepository


async def create_user(session: AsyncSession, user_data: RegisterForm) -> User:
    if await UserRepository.get_user_by_email(session, str(user_data.email)):
        raise HTTPException(409, "Email уже зарегистрирован в системе")
    if await UserRepository.get_user_by_username(session, user_data.username):
        raise HTTPException(409, "Имя пользователя уже занято")
    if len(user_data.password) < 8:
        raise HTTPException(400, "Пароль должен содержать минимум 8 символов")

    user = User(
        email=str(user_data.email),
        hashed_password=get_password_hash(user_data.password),
        username=user_data.username,
        full_name=user_data.full_name,
    )

    return await UserRepository.create_user(session, user)


async def update_user_service(session: AsyncSession, user_id: int, user_data: UserUpdate) -> User | None:
    user = await UserRepository.get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(404, "Пользователь не найден")

    user_data = user_data.model_dump(exclude_unset=True)

    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    for field, value in user_data.items():
        setattr(user, field, value)

    return await UserRepository.update_user(session, user)


async def update_user_admin(
    session: AsyncSession,
    user_id: int,
    email: str,
    full_name: str,
    is_superuser: bool,
    current_user_id: int
) -> User:
    user = await UserRepository.get_user_by_id(session, user_id)

    if not user:
        raise HTTPException(404, "Пользователь не найден")

    if user.id == current_user_id and not is_superuser:
        raise HTTPException(400, "Вы не можете снять статус администратора с самого себя")

    if user.email != email:
        existing_user = await UserRepository.get_user_by_email(session, email)
        if existing_user:
            raise HTTPException(409, "Пользователь с таким email уже существует")

    user.email = email
    user.full_name = full_name
    user.is_superuser = is_superuser

    return await UserRepository.update_user(session, user)
