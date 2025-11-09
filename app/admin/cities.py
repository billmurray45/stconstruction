from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.templates import templates
from app.core.utils import generate_slug
from app.users.models import User
from app.auth.dependencies import require_superuser
from app.projects.service import CityService
from app.projects.schemas import CityCreate, CityUpdate

router = APIRouter(prefix="/cities", tags=["admin-cities"])


@router.get("/", response_class=HTMLResponse)
async def admin_cities_list(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    cities = await CityService.get_all_cities(session, active_only=False)
    return templates.TemplateResponse(
        "admin/cities/list.html",
        {
            "request": request,
            "current_user": current_user,
            "cities": cities
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def admin_city_add_form(
    request: Request,
    current_user: User = Depends(require_superuser)
):
    return templates.TemplateResponse(
        "admin/cities/add.html",
        {
            "request": request,
            "current_user": current_user
        }
    )


@router.post("/add")
async def admin_city_add(
    name: str = Form(...),
    slug: str = Form(""),
    is_active: bool = Form(False),
    sort_order: int = Form(0),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(name)

        city_data = CityCreate(
            name=name,
            slug=slug,
            is_active=is_active,
            sort_order=sort_order
        )
        await CityService.create_city(session, city_data)
        return RedirectResponse(url="/admin/cities?success=created", status_code=303)
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/cities/add?error={str(e)}",
            status_code=303
        )


@router.get("/{city_id}/edit", response_class=HTMLResponse)
async def admin_city_edit_form(
    city_id: int,
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    city = await CityService.get_city_by_id(session, city_id)
    return templates.TemplateResponse(
        "admin/cities/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "city": city
        }
    )


@router.post("/{city_id}/edit")
async def admin_city_edit(
    city_id: int,
    name: str = Form(...),
    slug: str = Form(""),
    is_active: bool = Form(False),
    sort_order: int = Form(0),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(name)

        city_data = CityUpdate(
            name=name,
            slug=slug,
            is_active=is_active,
            sort_order=sort_order
        )
        await CityService.update_city(session, city_id, city_data)
        return RedirectResponse(url="/admin/cities?success=updated", status_code=303)
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/cities/{city_id}/edit?error={str(e)}",
            status_code=303
        )


@router.post("/{city_id}/delete")
async def admin_city_delete(
    city_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        await CityService.delete_city(session, city_id)
        return RedirectResponse(url="/admin/cities?success=deleted", status_code=303)
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/cities?error={str(e)}",
            status_code=303
        )
