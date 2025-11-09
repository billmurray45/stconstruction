from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.projects.models import ProjectClass, ProjectStatus


class CityBase(BaseModel):
    name: str
    slug: str


class CityCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True
    sort_order: int = 0


class CityUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CityResponse(CityBase):
    id: int
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Project Schemas
class ProjectBase(BaseModel):
    title: str
    slug: str


class ProjectCreate(BaseModel):
    title: str
    slug: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    city_id: int
    address: str
    project_class: ProjectClass
    status: ProjectStatus = ProjectStatus.CURRENT
    implementation_stage: Optional[str] = None
    completion_date: Optional[str] = None
    sold_percent: int = 0
    images: Optional[dict] = None
    is_published: bool = False


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    city_id: Optional[int] = None
    address: Optional[str] = None
    project_class: Optional[ProjectClass] = None
    status: Optional[ProjectStatus] = None
    implementation_stage: Optional[str] = None
    completion_date: Optional[str] = None
    sold_percent: Optional[int] = None
    images: Optional[dict] = None
    is_published: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: int
    subtitle: Optional[str] = None
    description: Optional[str] = None
    city_id: int
    address: str
    project_class: ProjectClass
    status: ProjectStatus
    implementation_stage: Optional[str] = None
    completion_date: Optional[str] = None
    sold_percent: int
    images: Optional[dict] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
