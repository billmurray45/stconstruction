import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.config.logging import log_security_event
from app.core.web.templates import templates
from app.core.security.rate_limit import limiter
from app.auth.service import authenticate_user

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/admin/", status_code=302)

    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "error": None
        }
    )


@router.post("/login")
@limiter.limit("5/minute")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        user = await authenticate_user(session, email, password)
    except HTTPException as e:
        # Неудачная попытка входа в админку
        log_security_event(
            event_type="admin_login_failed",
            details={
                "email": email,
                "ip": request.client.host if request.client else "unknown",
                "reason": "Authentication failed"
            },
            level="WARNING"
        )
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": e.detail
            },
            status_code=e.status_code
        )

    if not user.is_superuser:
        # Попытка доступа без прав администратора
        log_security_event(
            event_type="admin_access_denied",
            details={
                "user_id": user.id,
                "email": email,
                "ip": request.client.host if request.client else "unknown",
                "reason": "Not a superuser"
            },
            level="WARNING"
        )
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "Доступ запрещен. Требуются права администратора"
            },
            status_code=403
        )

    request.session["user_id"] = user.id

    # Успешный вход админа
    log_security_event(
        event_type="admin_login_success",
        details={
            "user_id": user.id,
            "email": email,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        },
        level="INFO"
    )

    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/logout")
async def admin_logout(request: Request):
    user_id = request.session.get("user_id")

    if user_id:
        log_security_event(
            event_type="admin_logout",
            details={
                "user_id": user_id,
                "ip": request.client.host if request.client else "unknown"
            },
            level="INFO"
        )

    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)
