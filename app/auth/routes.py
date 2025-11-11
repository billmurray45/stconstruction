from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.security.rate_limit import limiter
from app.auth.service import authenticate_user
from app.auth.dependencies import get_current_user
from app.users.models import User

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
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "message": e.detail}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Произошла ошибка при входе: {str(e)}"}
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
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
