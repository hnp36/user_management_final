# app/routers/timezone_routes.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from app.database import get_db
from app.utils.datetime_utils import get_available_timezones, is_valid_timezone
from app.dependencies import get_current_user
from app.models.user_model import User
from app.services.user_service import UserService

router = APIRouter(  # Changed from 'router' to 'timezone_router'
    prefix="/timezones",
    tags=["timezones"],
)

@router.get("/", response_model=List[Dict[str, str]])  # Also update here
async def get_timezones():
    """
    Get list of available timezones.
    """
    return get_available_timezones()

@router.put("/preference")  # And here
async def set_timezone_preference(
    timezone: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set timezone preference for the current user.
    """
    _ = request.state.gettext  # Get translator
    
    if not is_valid_timezone(timezone):
        return {"success": False, "message": _("Invalid timezone")}

    # Update user's preferred timezone
    updated_user = await UserService.update(
        db, 
        current_user.id, 
        {"preferred_timezone": timezone}
    )
    
    if updated_user:
        return {
            "success": True, 
            "message": _("Timezone preference updated successfully"),
            "timezone": timezone
        }
    else:
        return {"success": False, "message": _("Failed to update timezone preference")}