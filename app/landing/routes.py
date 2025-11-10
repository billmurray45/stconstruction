from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database import get_session
from app.core.web.templates import templates
from app.core.web.context_processors import get_site_settings_context
from app.core.secutiry.rate_limit import limiter
from app.news.service import get_latest_news
from app.projects.service import ProjectService, CityService
from app.auth.dependencies import set_current_user_optional
from .schemas import CallbackRequestCreate
from .service import LandingService

router = APIRouter(
    dependencies=[Depends(set_current_user_optional)]
)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: AsyncSession = Depends(get_session)):
    """Главная страница"""
    latest_news = await get_latest_news(session, limit=3)
    cities = await CityService.get_all_cities(session, active_only=True)
    projects = await ProjectService.get_all_projects(session, published_only=True)

    # Получаем настройки сайта для глобального доступа
    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "latest_news": latest_news,
            "cities": cities,
            "projects": projects,
            **site_context  # Добавляем настройки сайта в контекст
        }
    )


@router.get("/contacts", response_class=HTMLResponse)
async def contacts(request: Request, session: AsyncSession = Depends(get_session)):
    """Страница контактов"""
    # Получаем настройки сайта для отображения контактной информации
    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "contacts.html",
        {
            "request": request,
            **site_context
        }
    )


@router.get("/projects/{slug}", response_class=HTMLResponse)
async def project_detail(request: Request, slug: str, session: AsyncSession = Depends(get_session)):
    """Страница детального просмотра проекта"""
    project = await ProjectService.get_project_by_slug(session, slug)

    # Проверяем, что проект опубликован (если пользователь не админ)
    if not project.is_published and not getattr(request.state, 'current_user', None):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Проект не найден")

    site_context = await get_site_settings_context(session)

    return templates.TemplateResponse(
        "project_detail.html",
        {
            "request": request,
            "project": project,
            **site_context
        }
    )


@router.post("/request-callback")
@limiter.limit("10/hour")  # 10 callback requests per hour per IP
async def request_callback(
    request: Request,
    data: CallbackRequestCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        await LandingService.create_callback_request(session, data)
        return JSONResponse(
            status_code=201,
            content={"message": "Ваша заявка успешно отправлена!"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Произошла ошибка при отправке заявки."}
        )
