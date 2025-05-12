from builtins import Exception, bool, classmethod, int, str
from datetime import datetime, timezone
import secrets
from typing import Optional, Dict, List
from pydantic import ValidationError
from sqlalchemy import func, update, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_email_service, get_settings
from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.nickname_gen import generate_nickname
from app.utils.security import generate_verification_token, hash_password, verify_password
from uuid import UUID
from app.services.email_service import EmailService
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class UserService:
    @classmethod
    async def _execute_query(cls, session: AsyncSession, query):
        try:
            result = await session.execute(query)
            await session.commit()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            return None

    @classmethod
    async def _fetch_user(cls, session: AsyncSession, **filters) -> Optional[User]:
        query = select(User).filter_by(**filters)
        result = await cls._execute_query(session, query)
        return result.scalars().first() if result else None

    @classmethod
    async def get_by_id(cls, session: AsyncSession, user_id: UUID) -> Optional[User]:
        return await cls._fetch_user(session, id=user_id)

    @classmethod
    async def get_by_nickname(cls, session: AsyncSession, nickname: str) -> Optional[User]:
        return await cls._fetch_user(session, nickname=nickname)

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> Optional[User]:
        return await cls._fetch_user(session, email=email)
    
    @staticmethod
    async def count(session: AsyncSession) -> int:
        result = await session.execute(select([User]).count())  # Counting users in the User table
        return result.scalar()
    
    @classmethod
    async def create(cls, session: AsyncSession, user_data: Dict[str, str], email_service: EmailService) -> Optional[User]:
        try:
            validated_data = UserCreate(**user_data).model_dump()

            # Ensure preferred_language exists
            if "preferred_language" not in validated_data:
                validated_data["preferred_language"] = "en"

            # Check if email already exists
            existing_user = await cls.get_by_email(session, validated_data["email"])
            if existing_user:
                logger.error(f"User with email {validated_data['email']} already exists.")
                # Raise a specific exception for email already exists
                raise ValueError("Email already exists")

            # Handle nickname generation early
            nickname = validated_data.get("nickname")
            if not nickname:
                nickname = generate_nickname()
                while await cls.get_by_nickname(session, nickname):
                    nickname = generate_nickname()
                validated_data["nickname"] = nickname

            # Hash password
            validated_data["hashed_password"] = hash_password(validated_data.pop("password"))

            # Determine user role
            user_count = await cls.count(session)
            role = UserRole.ADMIN if user_count == 0 else UserRole.ANONYMOUS
            validated_data["role"] = role

            # Email verification
            if role == UserRole.ADMIN:
                validated_data["email_verified"] = True
            else:
                validated_data["verification_token"] = generate_verification_token()

            # Only keep fields that exist in User model
            allowed_fields = {
                "email", "hashed_password", "first_name", "last_name",
                "bio", "profile_picture_url", "linkedin_profile_url",
                "github_profile_url", "role", "preferred_language",
                "preferred_timezone", "nickname", "email_verified", "verification_token"
            }
            validated_data = {k: v for k, v in validated_data.items() if k in allowed_fields}

            # Create new user
            new_user = User(**validated_data)

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            # Send verification email if not admin
            if not new_user.email_verified:
                await email_service.send_verification_email(new_user)

            logger.info(f"User {new_user.email} created successfully.")
            return new_user

        except ValueError as e:
            # This will catch our custom "Email already exists" error
            logger.error(f"Value error during user creation: {str(e)}")
            if "Email already exists" in str(e):
                # Allow caller to handle this specific error
                raise
            return None
        except ValidationError as e:
            logger.error(f"Validation error during user creation: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error during user creation: {e}")
            await session.rollback()
            return None