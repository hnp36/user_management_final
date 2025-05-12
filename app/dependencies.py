from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Database
from app.utils.template_manager import TemplateManager
from app.services.email_service import EmailService
from app.services.jwt_service import decode_token
from settings.config import Settings
from typing import Dict

# Remove unnecessary imports from builtins
# from builtins import Exception, dict, str  # No need to import these explicitly

def get_settings() -> Settings:
    """Return application settings."""
    return Settings()

def get_email_service() -> EmailService:
    """Return EmailService instance."""
    template_manager = TemplateManager()
    return EmailService(template_manager=template_manager)

async def get_db() -> AsyncSession:
    """Dependency that provides a database session for each request."""
    async_session_factory = Database.get_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# OAuth2PasswordBearer instance for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, str]:
    """
    Dependency to extract the current user from the JWT token.
    Returns user information such as user_id and role.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    user_role: str = payload.get("role")
    if user_id is None or user_role is None:
        raise credentials_exception

    return {"user_id": user_id, "role": user_role}

def require_role(roles: str):
    """
    Dependency to enforce that the current user has one of the required roles.
    If the user does not have the required role, raises an HTTP 403 Forbidden error.
    """
    def role_checker(current_user: Dict[str, str] = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return current_user
    return role_checker
