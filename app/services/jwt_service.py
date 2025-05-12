from builtins import dict, str
import jwt
from datetime import datetime, timedelta
from settings.config import settings

def create_access_token(*, data: dict, expires_delta: timedelta = None):
    """
    Creates a JWT access token with optional expiration and language setting.
    Converts role to uppercase for consistency.
    """
    to_encode = data.copy()

    # Ensure role is uppercase if present
    if 'role' in to_encode:
        to_encode['role'] = to_encode['role'].upper()

    # Default expiration
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})

    # Default language fallback if not provided
    if "lang" not in to_encode:
        to_encode["lang"] = "en"

    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_token(token: str):
    """
    Decodes the JWT token and returns the payload, or None if invalid.
    """
    try:
        decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return decoded
    except jwt.PyJWTError:
        return None
