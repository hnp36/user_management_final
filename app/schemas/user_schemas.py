from builtins import ValueError, any, bool, str
from pydantic import BaseModel, EmailStr, Field, validator, root_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid
import re
from app.models.user_model import UserRole
from app.utils.nickname_gen import generate_nickname


def validate_url(url: Optional[str]) -> Optional[str]:
    if url is None:
        return url
    url_regex = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
    if not re.match(url_regex, url):
        raise ValueError('Invalid URL format')
    return url


def validate_language_code(lang_code: Optional[str]) -> Optional[str]:
    if lang_code is None:
        return lang_code
    # Simple validation for language codes (can be expanded with more accurate validation)
    lang_regex = r'^[a-z]{2}(-[A-Z]{2})?$'
    if not re.match(lang_regex, lang_code):
        raise ValueError('Invalid language code format. Use format like "en" or "en-US"')
    return lang_code


class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example=generate_nickname())
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[str] = Field(None, example="https://github.com/johndoe")
    role: UserRole
    preferred_language: Optional[str] = Field("en", example="en")
    preferred_timezone: Optional[str] = Field("UTC", example="America/New_York")

    _validate_urls = validator('profile_picture_url', 'linkedin_profile_url', 'github_profile_url', pre=True, allow_reuse=True)(validate_url)
    _validate_language = validator('preferred_language', pre=True, allow_reuse=True)(validate_language_code)
 
    class Config:
        from_attributes = True


class UserCreate(UserBase):
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")
    preferred_language: Optional[str] = Field("en", example="en")
    preferred_timezone: Optional[str] = Field("UTC", example="America/New_York")


class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example="john_doe123")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[str] = Field(None, example="https://github.com/johndoe")
    role: Optional[str] = Field(None, example="AUTHENTICATED")
    preferred_language: Optional[str] = Field(None, example="fr")
    preferred_timezone: Optional[str] = Field(None, example="Europe/Paris")

    @root_validator(pre=True)
    def check_at_least_one_value(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values


class LanguagePreference(BaseModel):
    preferred_language: str = Field(..., example="fr")


class TimezonePreference(BaseModel):
    preferred_timezone: str = Field(..., example="Europe/Paris")


class UserResponse(UserBase):
    id: uuid.UUID = Field(..., example=uuid.uuid4())
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example=generate_nickname())    
    is_professional: Optional[bool] = Field(default=False, example=True)
    role: UserRole
    preferred_language: str = Field(..., example="en")
    preferred_timezone: str = Field(..., example="UTC")


class LoginRequest(BaseModel):
    email: str = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(None, example="The requested resource was not found.")


class UserListResponse(BaseModel):
    items: List[UserResponse] = Field(..., example=[{
        "id": uuid.uuid4(), "nickname": generate_nickname(), "email": "john.doe@example.com",
        "first_name": "John", "bio": "Experienced developer", "role": "AUTHENTICATED",
        "last_name": "Doe", "bio": "Experienced developer", "role": "AUTHENTICATED",
        "profile_picture_url": "https://example.com/profiles/john.jpg", 
        "linkedin_profile_url": "https://linkedin.com/in/johndoe", 
        "github_profile_url": "https://github.com/johndoe",
        "preferred_language": "en",
        "preferred_timezone": "UTC"
    }])
    total: int = Field(..., example=100)
    page: int = Field(..., example=1)
    size: int = Field(..., example=10)


class LanguageInfo(BaseModel):
    code: str = Field(..., example="en")
    name: str = Field(..., example="English")
    flag: str = Field(..., example="🇺🇸")
    rtl: str = Field(..., example=False)


class TimezoneInfo(BaseModel):
    code: str = Field(..., example="America/New_York")
    name: str = Field(..., example="Eastern Time (US & Canada)")