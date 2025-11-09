from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NewsBase(BaseModel):
    title: str
    slug: str


class NewsCreate(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    content: Optional[str] = None
    image_path: Optional[str] = None
    is_published: bool = False


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    image_path: Optional[str] = None
    is_published: Optional[bool] = None


class NewsResponse(NewsBase):
    id: int
    description: Optional[str] = None
    content: Optional[str] = None
    image_path: Optional[str] = None
    is_published: bool
    published_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
