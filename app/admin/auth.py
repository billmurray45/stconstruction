from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.templates import templates
from app.auth.service import authenticate_user


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
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        user = await authenticate_user(session, email, password)
    except HTTPException as e:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": e.detail
            },
            status_code=e.status_code
        )

    if not user.is_superuser:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "Доступ запрещен. Требуются права администратора"
            },
            status_code=403
        )

    request.session["user_id"] = user.id

    return RedirectResponse(url="/admin/", status_code=302)


@router.post("/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)
