from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Путь к файлу изображения
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Статус публикации
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Даты
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self):
        return f"<News ID: '{self.id}', Title: '{self.title}', Published: '{self.is_published}'>"
