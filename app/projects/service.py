from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from typing import Optional, List

from .models import City, Project, ProjectStatus, ProjectClass
from .repository import CityRepository, ProjectRepository
from .schemas import CityCreate, CityUpdate, ProjectCreate, ProjectUpdate


class CityService:
    """Сервис для работы с городами"""

    @staticmethod
    async def create_city(session: AsyncSession, city_data: CityCreate) -> City:
        existing_city = await CityRepository.get_city_by_slug(session, city_data.slug)
        if existing_city:
            raise HTTPException(status_code=409, detail="Город с таким slug уже существует")

        city = City(
            name=city_data.name,
            slug=city_data.slug,
            is_active=city_data.is_active,
            sort_order=city_data.sort_order
        )
        return await CityRepository.create_city(session, city)

    @staticmethod
    async def get_city_by_id(session: AsyncSession, city_id: int) -> City:
        city = await CityRepository.get_city_by_id(session, city_id)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")
        return city

    @staticmethod
    async def get_city_by_slug(session: AsyncSession, slug: str) -> City:
        city = await CityRepository.get_city_by_slug(session, slug)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")
        return city

    @staticmethod
    async def get_all_cities(session: AsyncSession, active_only: bool = False) -> List[City]:
        return await CityRepository.get_all_cities(session, active_only)

    @staticmethod
    async def update_city(session: AsyncSession, city_id: int, city_data: CityUpdate) -> City:
        city = await CityRepository.get_city_by_id(session, city_id)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")

        if city_data.slug and city_data.slug != city.slug:
            existing_city = await CityRepository.get_city_by_slug(session, city_data.slug)
            if existing_city:
                raise HTTPException(status_code=409, detail="Город с таким slug уже существует")
            city.slug = city_data.slug

        if city_data.name is not None:
            city.name = city_data.name
        if city_data.is_active is not None:
            city.is_active = city_data.is_active
        if city_data.sort_order is not None:
            city.sort_order = city_data.sort_order

        return await CityRepository.update_city(session, city)

    @staticmethod
    async def delete_city(session: AsyncSession, city_id: int) -> None:
        city = await CityRepository.get_city_by_id(session, city_id)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")

        projects = await ProjectRepository.get_projects_by_city(session, city_id, published_only=False)
        if projects:
            raise HTTPException(
                status_code=400,
                detail=f"Невозможно удалить город. Существует {len(projects)} проект(ов) в этом городе"
            )

        await CityRepository.delete_city(session, city)


class ProjectService:
    """Сервис для работы с проектами"""

    @staticmethod
    async def create_project(session: AsyncSession, project_data: ProjectCreate) -> Project:
        existing_project = await ProjectRepository.get_project_by_slug(session, project_data.slug)
        if existing_project:
            raise HTTPException(status_code=409, detail="Проект с таким slug уже существует")

        city = await CityRepository.get_city_by_id(session, project_data.city_id)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")

        project = Project(
            title=project_data.title,
            slug=project_data.slug,
            subtitle=project_data.subtitle,
            description=project_data.description,
            city_id=project_data.city_id,
            address=project_data.address,
            project_class=project_data.project_class,
            status=project_data.status,
            implementation_stage=project_data.implementation_stage,
            completion_date=project_data.completion_date,
            sold_percent=project_data.sold_percent,
            images=project_data.images,
            is_published=project_data.is_published
        )
        return await ProjectRepository.create_project(session, project)

    @staticmethod
    async def get_project_by_id(session: AsyncSession, project_id: int) -> Project:
        project = await ProjectRepository.get_project_by_id(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        return project

    @staticmethod
    async def get_project_by_slug(session: AsyncSession, slug: str) -> Project:
        project = await ProjectRepository.get_project_by_slug(session, slug)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")
        return project

    @staticmethod
    async def get_all_projects(
        session: AsyncSession,
        published_only: bool = False,
        status: Optional[ProjectStatus] = None,
        city_id: Optional[int] = None
    ) -> List[Project]:
        return await ProjectRepository.get_all_projects(
            session,
            published_only=published_only,
            status=status,
            city_id=city_id
        )

    @staticmethod
    async def get_projects_by_city(
        session: AsyncSession,
        city_id: int,
        published_only: bool = True
    ) -> List[Project]:
        city = await CityRepository.get_city_by_id(session, city_id)
        if not city:
            raise HTTPException(status_code=404, detail="Город не найден")

        return await ProjectRepository.get_projects_by_city(session, city_id, published_only)

    @staticmethod
    async def update_project(
        session: AsyncSession,
        project_id: int,
        project_data: ProjectUpdate
    ) -> Project:
        project = await ProjectRepository.get_project_by_id(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        if project_data.slug and project_data.slug != project.slug:
            existing_project = await ProjectRepository.get_project_by_slug(session, project_data.slug)
            if existing_project:
                raise HTTPException(status_code=409, detail="Проект с таким slug уже существует")
            project.slug = project_data.slug

        if project_data.city_id and project_data.city_id != project.city_id:
            city = await CityRepository.get_city_by_id(session, project_data.city_id)
            if not city:
                raise HTTPException(status_code=404, detail="Город не найден")
            project.city_id = project_data.city_id

        if project_data.title is not None:
            project.title = project_data.title
        if project_data.subtitle is not None:
            project.subtitle = project_data.subtitle
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.address is not None:
            project.address = project_data.address
        if project_data.project_class is not None:
            project.project_class = project_data.project_class
        if project_data.status is not None:
            project.status = project_data.status
        if project_data.implementation_stage is not None:
            project.implementation_stage = project_data.implementation_stage
        if project_data.completion_date is not None:
            project.completion_date = project_data.completion_date
        if project_data.sold_percent is not None:
            project.sold_percent = project_data.sold_percent
        if project_data.images is not None:
            project.images = project_data.images
        if project_data.is_published is not None:
            project.is_published = project_data.is_published

        return await ProjectRepository.update_project(session, project)

    @staticmethod
    async def delete_project(session: AsyncSession, project_id: int) -> None:
        project = await ProjectRepository.get_project_by_id(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        await ProjectRepository.delete_project(session, project)

    @staticmethod
    async def toggle_publish(session: AsyncSession, project_id: int) -> Project:
        project = await ProjectRepository.get_project_by_id(session, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Проект не найден")

        project.is_published = not project.is_published
        return await ProjectRepository.update_project(session, project)
