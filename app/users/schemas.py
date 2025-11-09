from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str


class RegisterForm(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserResponse(UserBase):
    id: int
    full_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
