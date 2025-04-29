from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.services.user_service import UserService
from app.utils.localization import get_localization_manager, get_translator, LocalizationManager
from pydantic import BaseModel
from typing import List, Optional
import pytz

router = APIRouter(prefix="/preferences", tags=["User Preferences"])

class LanguageUpdate(BaseModel):
    language: str


class TimezoneUpdate(BaseModel):
    timezone: str


class SupportedLanguage(BaseModel):
    code: str
    name: str


class SupportedTimezone(BaseModel):
    timezone: str
    name: str
    offset: str


class SupportedLanguagesResponse(BaseModel):
    languages: List[SupportedLanguage]


class SupportedTimezonesResponse(BaseModel):
    timezones: List[SupportedTimezone]


# Map of language codes to their full names
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "pt": "Português",
    "ru": "Русский",
    "zh": "中文"
}


@router.get("/languages", response_model=SupportedLanguagesResponse)
async def get_supported_languages(loc_manager: LocalizationManager = Depends(get_localization_manager)):
    """Get all supported languages in the application"""
    languages = []
    for lang_code in loc_manager.list_supported_languages():
        name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        languages.append(SupportedLanguage(code=lang_code, name=name))
    
    return SupportedLanguagesResponse(languages=languages)


@router.get("/timezones", response_model=SupportedTimezonesResponse)
async def get_supported_timezones():
    """Get all supported timezones in the application"""
    from datetime import datetime
    import pytz
    
    now = datetime.now(pytz.UTC)
    timezones = []
    
    # We'll use common timezones instead of all to keep the list manageable
    for tz_name in pytz.common_timezones:
        tz = pytz.timezone(tz_name)
        local_time = now.astimezone(tz)
        offset = local_time.strftime("%z")
        
        # Format offset for better readability (e.g., +0000 to UTC+00:00)
        offset_hours = offset[0:3]
        offset_minutes = offset[3:5]
        readable_offset = f"UTC{offset_hours}:{offset_minutes}"
        
        # For display, replace underscores with spaces and include offset
        display_name = tz_name.replace('_', ' ')
        
        timezones.append(SupportedTimezone(
            timezone=tz_name,
            name=display_name,
            offset=readable_offset
        ))
    
    return SupportedTimezonesResponse(timezones=timezones)


@router.put("/language", status_code=status.HTTP_200_OK)
async def update_language_preference(
    language_update: LanguageUpdate,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    loc_manager: LocalizationManager = Depends(get_localization_manager),
    t = Depends(get_translator)
):
    """Update the user's language preference"""
    if not loc_manager.is_supported_language(language_update.language):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Language '{language_update.language}' is not supported"
        )
    
    user_email = current_user["sub"]
    user = await UserService.get_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("user_not_found")
        )
    
    user.preferred_language = language_update.language
    db.add(user)
    await db.commit()
    
    # Update the language cookie
    response.set_cookie(
        key="preferred_language", 
        value=language_update.language, 
        max_age=86400 * 30  # 30 days
    )
    
    # Get the success message in the new language
    success_key = "language_switch_success"
    new_language_message = loc_manager.get_translation(success_key, language_update.language)
    
    return {"message": new_language_message}


@router.put("/timezone", status_code=status.HTTP_200_OK)
async def update_timezone_preference(
    timezone_update: TimezoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    t = Depends(get_translator)
):
    """Update the user's timezone preference"""
    try:
        # Validate the timezone
        pytz.timezone(timezone_update.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timezone '{timezone_update.timezone}' is not valid"
        )
    
    user_email = current_user["sub"]
    user = await UserService.get_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("user_not_found")
        )
    
    user.timezone = timezone_update.timezone
    db.add(user)
    await db.commit()
    
    return {"message": t("timezone_updated")}


@router.get("/current", status_code=status.HTTP_200_OK)
async def get_current_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    t = Depends(get_translator)
):
    """Get the user's current language and timezone preferences"""
    user_email = current_user["sub"]
    user = await UserService.get_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=t("user_not_found")
        )
    
    return {
        "language": user.preferred_language,
        "timezone": user.timezone
    }