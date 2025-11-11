import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.config.logging import log_security_event
from app.core.security.rate_limit import limiter
from app.auth.service import authenticate_user
from app.auth.dependencies import get_current_user
from app.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        user = await authenticate_user(session, email, password)

        request.session["user_id"] = user.id

        # Успешный вход
        log_security_event(
            event_type="login_success",
            details={
                "user_id": user.id,
                "email": email,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            },
            level="INFO"
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Вход выполнен успешно!",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name
                }
            }
        )
    except HTTPException as e:
        # Неудачная попытка входа
        log_security_event(
            event_type="login_failed",
            details={
                "email": email,
                "ip": request.client.host if request.client else "unknown",
                "reason": e.detail,
                "status_code": e.status_code
            },
            level="WARNING"
        )
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "message": e.detail}
        )
    except Exception as e:
        logger.error(f"Login error for {email}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Произошла ошибка при входе: {str(e)}"}
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    log_security_event(
        event_type="logout",
        details={
            "user_id": current_user.id,
            "email": current_user.email,
            "ip": request.client.host if request.client else "unknown"
        },
        level="INFO"
    )

    request.session.clear()

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Выход выполнен успешно!"
        }
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
                "full_name": current_user.full_name,
                "is_active": current_user.is_active,
                "is_superuser": current_user.is_superuser,
                "created_at": current_user.created_at.isoformat(),
            }
        }
    )
