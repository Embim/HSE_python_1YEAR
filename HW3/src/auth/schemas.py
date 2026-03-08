from datetime import datetime

from pydantic import EmailStr, Field

from src.models import AppModel


class UserCreate(AppModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(AppModel):
    id: int
    username: str
    email: str
    created_at: datetime


class Token(AppModel):
    access_token: str
    token_type: str
