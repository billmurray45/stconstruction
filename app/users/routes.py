from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.secutiry.rate_limit import limiter
from app.users.schemas import RegisterForm
from app.users.service import create_user

router = APIRouter(prefix="/auth", tags=["Users"])


@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register_post(
        request: Request,
        email: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
        full_name: str = Form(None),
        session: AsyncSession = Depends(get_session)
):
    try:
        user_data = RegisterForm(
            email=email,
            username=username,
            password=password,
            full_name=full_name
        )

        new_user = await create_user(session, user_data)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Регистрация успешна! Теперь вы можете войти в систему.",
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "username": new_user.username
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
            content={"success": False, "message": f"Произошла ошибка при регистрации: {str(e)}"}
        )
