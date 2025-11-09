import enum

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, DateTime, Text, Boolean, Integer, Enum, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectClass(str, enum.Enum):
    """Класс проекта"""
    ECONOMY = "economy"
    COMFORT = "comfort"
    BUSINESS = "business"
    PREMIUM = "premium"
    ELITE = "elite"


class ProjectStatus(str, enum.Enum):
    """Статус проекта"""
    CURRENT = "current"
    COMPLETED = "completed"
    PLANNED = "planned"


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="city")

    def __repr__(self):
        return f"<City ID: '{self.id}', Name: '{self.name}', Slug: '{self.slug}'>"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Основная информация
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Локация
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Характеристики
    project_class: Mapped[ProjectClass] = mapped_column(Enum(ProjectClass), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.CURRENT)

    # Дополнительная информация
    implementation_stage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completion_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sold_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Изображения (массив путей)
    images: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Публикация
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Даты
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    city: Mapped["City"] = relationship("City", back_populates="projects")

    def __repr__(self):
        return (f"<Project ID: '{self.id}', Title: '{self.title}', "
                f"City: '{self.city.name if self.city else None}', Published: '{self.is_published}'>")
