import logging
import uuid
import os

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pathlib import Path

from app.core.config.database import get_session
from app.core.web.templates import templates
from app.core.utils.helpers import generate_slug
from app.core.security.file_validator import validate_multiple_images, save_uploaded_file, FileValidationError

from app.users.models import User
from app.auth.dependencies import require_superuser
from app.projects.service import ProjectService, CityService
from app.projects.schemas import ProjectCreate, ProjectUpdate
from app.projects.models import ProjectClass, ProjectStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["admin-projects"])

# Путь для сохранения изображений проектов
UPLOAD_DIR = Path("app/static/uploads/projects")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def admin_projects_list(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    projects = await ProjectService.get_all_projects(session, published_only=False)
    return templates.TemplateResponse(
        "admin/projects/list.html",
        {
            "request": request,
            "current_user": current_user,
            "projects": projects
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def admin_project_add_form(
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    cities = await CityService.get_all_cities(session, active_only=False)
    return templates.TemplateResponse(
        "admin/projects/add.html",
        {
            "request": request,
            "current_user": current_user,
            "cities": cities,
            "project_classes": ProjectClass,
            "project_statuses": ProjectStatus
        }
    )


@router.post("/add")
async def admin_project_add(
    title: str = Form(...),
    slug: str = Form(""),
    subtitle: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    city_id: int = Form(...),
    address: str = Form(...),
    project_class: ProjectClass = Form(...),
    status: ProjectStatus = Form(...),
    implementation_stage: Optional[str] = Form(None),
    completion_date: Optional[str] = Form(None),
    sold_percent: int = Form(0),
    is_published: bool = Form(False),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(title)

        # Обработка загруженных изображений
        image_data = None
        if images and images[0].filename:
            # Валидация всех изображений
            await validate_multiple_images(
                images,
                max_files=10,
                field_name="изображения проекта"
            )

            image_urls = []
            for image in images:
                # Генерируем уникальное имя файла
                file_extension = os.path.splitext(image.filename)[1].lower()
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                # Сохраняем файл
                await save_uploaded_file(image, UPLOAD_DIR, unique_filename)

                # Добавляем URL в список
                image_urls.append(f"/static/uploads/projects/{unique_filename}")

            if image_urls:
                image_data = {"urls": image_urls}

        project_data = ProjectCreate(
            title=title,
            slug=slug,
            subtitle=subtitle,
            description=description,
            city_id=city_id,
            address=address,
            project_class=project_class,
            status=status,
            implementation_stage=implementation_stage,
            completion_date=completion_date,
            sold_percent=sold_percent,
            images=image_data,
            is_published=is_published
        )
        project = await ProjectService.create_project(session, project_data)

        # Логируем создание проекта
        logger.info(
            f"Project created: id={project.id}, title='{title}', "
            f"status={status.value}, published={is_published}, by_user={current_user.email}"
        )

        return RedirectResponse(url="/admin/projects?success=created", status_code=303)
    except FileValidationError as e:
        return RedirectResponse(
            url=f"/admin/projects/add?error={e.detail}",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/projects/add?error={str(e)}",
            status_code=303
        )


@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def admin_project_edit_form(
    project_id: int,
    request: Request,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    project = await ProjectService.get_project_by_id(session, project_id)
    cities = await CityService.get_all_cities(session, active_only=False)
    return templates.TemplateResponse(
        "admin/projects/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "project": project,
            "cities": cities,
            "project_classes": ProjectClass,
            "project_statuses": ProjectStatus
        }
    )


@router.post("/{project_id}/edit")
async def admin_project_edit(
    project_id: int,
    title: str = Form(...),
    slug: str = Form(""),
    subtitle: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    city_id: int = Form(...),
    address: str = Form(...),
    project_class: ProjectClass = Form(...),
    status: ProjectStatus = Form(...),
    implementation_stage: Optional[str] = Form(None),
    completion_date: Optional[str] = Form(None),
    sold_percent: int = Form(0),
    is_published: bool = Form(False),
    keep_images: List[str] = Form([]),
    new_images: List[UploadFile] = File(None),
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        project = await ProjectService.get_project_by_id(session, project_id)

        # Генерация SEO URL
        if not slug or slug.strip() == "":
            slug = generate_slug(title)

        # Обработка изображений
        existing_urls = project.images.get("urls", []) if project.images else []

        # Определяем удаленные изображения и удаляем физические файлы
        deleted_urls = [url for url in existing_urls if url not in keep_images]
        for deleted_url in deleted_urls:
            # Извлекаем имя файла из URL и удаляем физический файл
            filename = deleted_url.split('/')[-1]
            file_path = UPLOAD_DIR / filename
            if file_path.exists():
                os.remove(file_path)

        # Оставляем только выбранные изображения
        kept_urls = [url for url in existing_urls if url in keep_images]

        # Добавляем новые изображения
        if new_images and new_images[0].filename:
            # Валидация новых изображений
            await validate_multiple_images(
                new_images,
                max_files=10,
                field_name="новые изображения"
            )

            for image in new_images:
                file_extension = os.path.splitext(image.filename)[1].lower()
                unique_filename = f"{uuid.uuid4()}{file_extension}"

                # Сохраняем файл
                await save_uploaded_file(image, UPLOAD_DIR, unique_filename)

                kept_urls.append(f"/static/uploads/projects/{unique_filename}")

        image_data = {"urls": kept_urls} if kept_urls else None

        project_data = ProjectUpdate(
            title=title,
            slug=slug,
            subtitle=subtitle,
            description=description,
            city_id=city_id,
            address=address,
            project_class=project_class,
            status=status,
            implementation_stage=implementation_stage,
            completion_date=completion_date,
            sold_percent=sold_percent,
            images=image_data,
            is_published=is_published
        )
        await ProjectService.update_project(session, project_id, project_data)

        # Логируем обновление проекта
        logger.info(
            f"Project updated: id={project_id}, title='{title}', "
            f"status={status.value}, published={is_published}, by_user={current_user.email}"
        )

        return RedirectResponse(url="/admin/projects?success=updated", status_code=303)
    except FileValidationError as e:
        return RedirectResponse(
            url=f"/admin/projects/{project_id}/edit?error={e.detail}",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/projects/{project_id}/edit?error={str(e)}",
            status_code=303
        )


@router.post("/{project_id}/delete")
async def admin_project_delete(
    project_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Получаем проект перед удалением для логирования
        project = await ProjectService.get_project_by_id(session, project_id)
        project_title = project.title if project else "unknown"

        await ProjectService.delete_project(session, project_id)

        # Логируем удаление проекта
        logger.info(
            f"Project deleted: id={project_id}, title='{project_title}', "
            f"by_user={current_user.email}"
        )

        return RedirectResponse(url="/admin/projects?success=deleted", status_code=303)
    except Exception as e:
        logger.error(f"Project deletion failed: {str(e)}")
        return RedirectResponse(
            url=f"/admin/projects?error={str(e)}",
            status_code=303
        )


@router.post("/{project_id}/toggle-publish")
async def admin_project_toggle_publish(
    project_id: int,
    current_user: User = Depends(require_superuser),
    session: AsyncSession = Depends(get_session)
):
    try:
        await ProjectService.toggle_publish(session, project_id)
        return RedirectResponse(url="/admin/projects?success=toggled", status_code=303)
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/projects?error={str(e)}",
            status_code=303
        )
