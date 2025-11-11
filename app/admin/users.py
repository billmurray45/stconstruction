import logging
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.config.logging import log_security_event
from app.core.web.templates import templates

from app.auth.dependencies import require_superuser
from app.users.models import User
from app.users.repository import UserRepository
from app.users.service import update_user_admin, create_user
from app.users.schemas import RegisterForm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Admin Users"])


@router.get("/", response_class=HTMLResponse)
async def admin_users_list(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    all_users = await UserRepository.get_all_users(session)

    return templates.TemplateResponse(
        "admin/users/list.html",
        {
            "request": request,
            "current_user": current_user,
            "users": all_users
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def admin_user_add_form(
    request: Request,
    current_user: User = Depends(require_superuser),
):
    return templates.TemplateResponse(
        "admin/users/add.html",
        {
            "request": request,
            "current_user": current_user
        }
    )


@router.post("/add")
async def admin_user_add(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    is_superuser: bool = Form(False),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        register_form = RegisterForm(
            email=email,
            username=username,
            full_name=full_name,
            password=password
        )
        user = await create_user(session, register_form)

        if is_superuser:
            user.is_superuser = True
            await UserRepository.update_user(session, user)

        # Логируем создание пользователя
        log_security_event(
            event_type="admin_user_created",
            details={
                "admin_id": current_user.id,
                "admin_email": current_user.email,
                "new_user_id": user.id,
                "new_user_email": email,
                "is_superuser": is_superuser,
                "ip": request.client.host if request.client else "unknown"
            },
            level="INFO"
        )

        return RedirectResponse(url="/admin/users?success=created", status_code=303)
    except HTTPException as e:
        logger.warning(f"User creation failed: {e.detail}")
        if e.status_code == 409:
            return RedirectResponse(url="/admin/users/add?error=already_exists", status_code=303)
        elif e.status_code == 400:
            return RedirectResponse(url="/admin/users/add?error=invalid_password", status_code=303)
        else:
            return RedirectResponse(url="/admin/users?error=unknown", status_code=303)


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def admin_user_edit_form(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    user = await UserRepository.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return templates.TemplateResponse(
        "admin/users/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "user": user
        }
    )


@router.post("/{user_id}/edit")
async def admin_user_edit(
    request: Request,
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    is_superuser: bool = Form(False),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Получаем старые данные для логирования изменений
        user = await UserRepository.get_user_by_id(session, user_id)
        old_email = user.email if user else "unknown"
        old_superuser = user.is_superuser if user else False

        await update_user_admin(
            session=session,
            user_id=user_id,
            email=email,
            full_name=full_name,
            is_superuser=is_superuser,
            current_user_id=current_user.id
        )

        # Логируем изменения
        changes = []
        if old_email != email:
            changes.append(f"email: {old_email} -> {email}")
        if old_superuser != is_superuser:
            changes.append(f"is_superuser: {old_superuser} -> {is_superuser}")

        log_security_event(
            event_type="admin_user_updated",
            details={
                "admin_id": current_user.id,
                "admin_email": current_user.email,
                "user_id": user_id,
                "changes": ", ".join(changes) if changes else "name only",
                "ip": request.client.host if request.client else "unknown"
            },
            level="INFO"
        )

        return RedirectResponse(url="/admin/users?success=updated", status_code=303)
    except HTTPException as e:
        logger.warning(f"User update failed: {e.detail}")
        if e.status_code == 404:
            return RedirectResponse(url="/admin/users?error=not_found", status_code=303)
        elif e.status_code == 400:
            return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=cannot_remove_own_superuser", status_code=303)
        elif e.status_code == 409:
            return RedirectResponse(url=f"/admin/users/{user_id}/edit?error=email_exists", status_code=303)
        else:
            return RedirectResponse(url="/admin/users?error=unknown", status_code=303)


@router.post("/{user_id}/delete")
async def admin_user_delete(
    request: Request,
    user_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    user = await UserRepository.get_user_by_id(session, user_id)
    if not user:
        return RedirectResponse(url="/admin/users?error=not_found", status_code=303)

    if user.id == current_user.id:
        return RedirectResponse(url="/admin/users?error=cannot_delete_yourself", status_code=303)

    # Сохраняем данные перед удалением
    deleted_email = user.email
    deleted_id = user.id

    await UserRepository.delete_user(session, user)

    # Логируем удаление пользователя
    log_security_event(
        event_type="admin_user_deleted",
        details={
            "admin_id": current_user.id,
            "admin_email": current_user.email,
            "deleted_user_id": deleted_id,
            "deleted_user_email": deleted_email,
            "ip": request.client.host if request.client else "unknown"
        },
        level="WARNING"  # WARNING т.к. это критичная операция
    )

    return RedirectResponse(url="/admin/users?success=deleted", status_code=303)
