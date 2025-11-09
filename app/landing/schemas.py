from pydantic import BaseModel, ConfigDict
from typing import Optional


class SiteSettingsBase(BaseModel):
    company_name: Optional[str] = "Standart Construction"
    logo_path: Optional[str] = None

    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email_general: Optional[str] = None
    email_orders: Optional[str] = None

    addresses: Optional[dict] = None

    social_instagram: Optional[str] = None
    social_facebook: Optional[str] = None
    social_whatsapp: Optional[str] = None
    social_telegram: Optional[str] = None
    social_youtube: Optional[str] = None

    working_hours: Optional[str] = None
    inn: Optional[str] = None
    bin: Optional[str] = None
    legal_address: Optional[str] = None

    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

    stats_projects_completed: Optional[int] = 0
    stats_clients: Optional[int] = 0
    stats_years_experience: Optional[int] = 0


class SiteSettingsUpdate(SiteSettingsBase):
    pass


class SiteSettingsResponse(SiteSettingsBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
