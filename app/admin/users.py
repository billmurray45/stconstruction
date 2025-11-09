from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.templates import templates
from app.auth.dependencies import require_superuser
from app.users.models import User
from app.users.repository import UserRepository
from app.users.service import update_user_admin, create_user
from app.users.schemas import RegisterForm


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

        return RedirectResponse(url="/admin/users?success=created", status_code=303)
    except HTTPException as e:
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
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    is_superuser: bool = Form(False),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        await update_user_admin(
            session=session,
            user_id=user_id,
            email=email,
            full_name=full_name,
            is_superuser=is_superuser,
            current_user_id=current_user.id
        )
        return RedirectResponse(url="/admin/users?success=updated", status_code=303)
    except HTTPException as e:
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
    user_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    user = await UserRepository.get_user_by_id(session, user_id)
    if not user:
        return RedirectResponse(url="/admin/users?error=not_found", status_code=303)

    if user.id == current_user.id:
        return RedirectResponse(url="/admin/users?error=cannot_delete_yourself", status_code=303)

    await UserRepository.delete_user(session, user)

    return RedirectResponse(url="/admin/users?success=deleted", status_code=303)
