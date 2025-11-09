from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from .models import City, Project, ProjectStatus


class CityRepository:
    """Репозиторий для работы с городами"""

    @staticmethod
    async def create_city(session: AsyncSession, city: City) -> City:
        session.add(city)
        await session.commit()
        await session.refresh(city)
        return city

    @staticmethod
    async def get_city_by_id(session: AsyncSession, city_id: int) -> Optional[City]:
        result = await session.execute(select(City).where(City.id == city_id))
        return result.scalars().first()

    @staticmethod
    async def get_city_by_slug(session: AsyncSession, slug: str) -> Optional[City]:
        result = await session.execute(select(City).where(City.slug == slug))
        return result.scalars().first()

    @staticmethod
    async def get_all_cities(session: AsyncSession, active_only: bool = False) -> List[City]:
        query = select(City).order_by(City.sort_order)
        if active_only:
            query = query.where(City.is_active == True)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_city(session: AsyncSession, city: City) -> City:
        await session.commit()
        await session.refresh(city)
        return city

    @staticmethod
    async def delete_city(session: AsyncSession, city: City) -> None:
        await session.delete(city)
        await session.commit()


class ProjectRepository:
    """Репозиторий для работы с проектами"""

    @staticmethod
    async def create_project(session: AsyncSession, project: Project) -> Project:
        session.add(project)
        await session.commit()
        await session.refresh(project)
        await session.refresh(project, ["city"])
        return project

    @staticmethod
    async def get_project_by_id(session: AsyncSession, project_id: int) -> Optional[Project]:
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.city))
            .where(Project.id == project_id)
        )
        return result.scalars().first()

    @staticmethod
    async def get_project_by_slug(session: AsyncSession, slug: str) -> Optional[Project]:
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.city))
            .where(Project.slug == slug)
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_projects(
        session: AsyncSession,
        published_only: bool = False,
        status: Optional[ProjectStatus] = None,
        city_id: Optional[int] = None
    ) -> List[Project]:
        query = select(Project).options(selectinload(Project.city)).order_by(Project.created_at.desc())

        if published_only:
            query = query.where(Project.is_published == True)

        if status:
            query = query.where(Project.status == status)

        if city_id:
            query = query.where(Project.city_id == city_id)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_projects_by_city(
        session: AsyncSession,
        city_id: int,
        published_only: bool = True
    ) -> List[Project]:
        query = (
            select(Project)
            .options(selectinload(Project.city))
            .where(Project.city_id == city_id)
            .order_by(Project.created_at.desc())
        )

        if published_only:
            query = query.where(Project.is_published == True)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_project(session: AsyncSession, project: Project) -> Project:
        await session.commit()
        await session.refresh(project)
        await session.refresh(project, ["city"])
        return project

    @staticmethod
    async def delete_project(session: AsyncSession, project: Project) -> None:
        await session.delete(project)
        await session.commit()
