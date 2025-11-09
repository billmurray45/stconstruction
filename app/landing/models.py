from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SiteSettings(Base):
    __tablename__ = "site_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Основная информация
    company_name: Mapped[str] = mapped_column(String(255), default="Standart Construction")
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Контактные данные
    phone_primary: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email_general: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_orders: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    addresses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Социальные сети
    social_instagram: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    social_facebook: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    social_whatsapp: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    social_telegram: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    social_youtube: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Рабочее время и юридическая информация
    working_hours: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    inn: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    legal_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # SEO настройки для главной страницы
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Статистика для главной
    stats_projects_completed: Mapped[Optional[int]] = mapped_column(default=0, nullable=True)
    stats_clients: Mapped[Optional[int]] = mapped_column(default=0, nullable=True)
    stats_years_experience: Mapped[Optional[int]] = mapped_column(default=0, nullable=True)

    # Технические поля
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SiteSettings(company={self.company_name})>"
