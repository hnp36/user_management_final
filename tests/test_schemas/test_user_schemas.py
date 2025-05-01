from pydantic import BaseModel, EmailStr, HttpUrl, validator, root_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re

COMMON_PASSWORDS = {"password123a!", "12345678", "qwerty", "password", "admin123", "letmein"}

class UserBase(BaseModel):
    nickname: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    bio: Optional[str] = None
    profile_picture_url: Optional[HttpUrl] = None
    linkedin_profile_url: Optional[HttpUrl] = None
    github_profile_url: Optional[HttpUrl] = None

    @validator("nickname")
    def validate_nickname(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", v):
            raise ValueError("Nickname must be 3-20 characters and contain only letters, numbers, underscores, or hyphens.")
        return v


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must include at least one number.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must include at least one special character")
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Password is too common and easily guessable.")
    return password


class UserCreate(UserBase):
    password: str

    _validate_password = validator("password", allow_reuse=True)(validate_password)


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    nickname: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    profile_picture_url: Optional[HttpUrl]
    linkedin_profile_url: Optional[HttpUrl]
    github_profile_url: Optional[HttpUrl]
    password: Optional[str]

    @validator("nickname")
    def validate_nickname(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", v):
            raise ValueError("Nickname must be 3-20 characters and contain only letters, numbers, underscores, or hyphens.")
        return v

    @validator("password")
    def validate_optional_password(cls, v):
        if v is not None:
            return validate_password(v)
        return v


class UserResponse(BaseModel):
    id: UUID
    nickname: str
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    links: List[dict]
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
