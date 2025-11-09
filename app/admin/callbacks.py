from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_session
from app.core.templates import templates
from app.auth.dependencies import require_superuser
from app.users.models import User
from app.landing.models import CallbackRequest

router = APIRouter(prefix="/callbacks", tags=["Admin Callbacks"])


@router.get("/", response_class=HTMLResponse)
async def admin_get_callback_requests(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(CallbackRequest).order_by(CallbackRequest.created_at.desc())
    result = await session.execute(stmt)
    callbacks = result.scalars().all()

    return templates.TemplateResponse(
        "admin/callbacks/list.html",
        {
            "request": request,
            "current_user": current_user,
            "callbacks": callbacks,
            "title": "Заявки на звонок"
        }
    )
