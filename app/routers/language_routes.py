# app/routers/language_routes.py

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from app.database import get_db
from app.utils.i18n import get_available_languages, is_supported_language
from app.dependencies import get_current_user
from app.models.user_model import User
from app.services.user_service import UserService

router = APIRouter(
    prefix="/languages",
    tags=["languages"],
)

@router.get("/", response_model=List[Dict[str, str]])
async def get_languages():
    """
    Get list of available languages
    """
    return get_available_languages()

@router.put("/preference")
async def set_language_preference(
    language_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set language preference for the current user
    """
    # Ensure `_` for translation is available
    _ = request.state.gettext if hasattr(request.state, "gettext") else lambda x: x  # Fallback to no-op if gettext isn't available

    if not is_supported_language(language_code):
        raise HTTPException(status_code=400, detail=_("Unsupported language"))

    # Update user's preferred language
    updated_user = await UserService.update(
        db, 
        current_user.id, 
        {"preferred_language": language_code}
    )
    
    if updated_user:
        return {
            "success": True, 
            "message": _("Language preference updated successfully"),
            "language_code": language_code
        }
    else:
        raise HTTPException(status_code=500, detail=_("Failed to update language preference"))
