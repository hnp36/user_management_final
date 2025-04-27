from typing import List, Optional, Dict, Any, Union
from uuid import UUID
import uuid
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import EmailStr, ValidationError

from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password
from app.dependencies import get_settings

class UserService:
    @staticmethod
    async def create(db: AsyncSession, user_data: Dict[str, Any], email_service=None) -> Optional[User]:
        """Create a new user in the database."""
        try:
            # Check if email already exists
            result = await db.execute(select(User).where(User.email == user_data["email"]))
            if result.scalars().first():
                return None
            
            # Validate input data (basic validation)
            if not user_data.get("email") or "@" not in user_data.get("email", ""):
                return None
            
            if not user_data.get("password") or len(user_data.get("password", "")) < 8:
                return None
            
            # Convert role string to enum if needed
            role = user_data.get("role")
            if isinstance(role, str):
                try:
                    role = UserRole[role]
                except KeyError:
                    role = UserRole.AUTHENTICATED
            elif role is None:
                role = UserRole.AUTHENTICATED
            
            # Create new user
            db_user = User(
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                nickname=user_data.get("nickname"),
                role=role,
                is_verified=False,
                verification_token=str(uuid.uuid4())
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            
            # Send verification email if email service is provided
            if email_service:
                await email_service.send_verification_email(
                    db_user.email, 
                    db_user.id, 
                    db_user.verification_token
                )
            
            return db_user
        except Exception as e:
            await db.rollback()
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: Union[UUID, str]) -> Optional[User]:
        """Get a user by ID."""
        try:
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return None
                    
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalars().first()
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email."""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalars().first()
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    async def get_by_nickname(db: AsyncSession, nickname: str) -> Optional[User]:
        """Get a user by nickname."""
        try:
            result = await db.execute(select(User).where(User.nickname == nickname))
            return result.scalars().first()
        except Exception as e:
            print(f"Error getting user by nickname: {e}")
            return None
    
    @staticmethod
    async def update(db: AsyncSession, user_id: Union[UUID, str], user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user's information."""
        try:
            # Convert string ID to UUID if needed
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return None
            
            # Get the user to update
            user = await UserService.get_by_id(db, user_id)
            if not user:
                return None
            
            # Basic validation
            if "email" in user_data and "@" not in user_data["email"]:
                return None
            
            # Update password if provided
            if "password" in user_data:
                user_data["hashed_password"] = hash_password(user_data.pop("password"))
            
            # Update user fields
            update_stmt = update(User).where(User.id == user_id).values(**user_data)
            await db.execute(update_stmt)
            await db.commit()
            
            # Refresh and return updated user
            user = await UserService.get_by_id(db, user_id)
            return user
        except Exception as e:
            await db.rollback()
            print(f"Error updating user: {e}")
            return None
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: Union[UUID, str]) -> bool:
        """Delete a user by ID."""
        try:
            # Convert string ID to UUID if needed
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return False
            
            # Check if user exists
            user = await UserService.get_by_id(db, user_id)
            if not user:
                return False
            
            # Delete the user
            delete_stmt = delete(User).where(User.id == user_id)
            await db.execute(delete_stmt)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"Error deleting user: {e}")
            return False
    
    @staticmethod
    async def login_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user and handle login attempts."""
        try:
            # Get user by email
            user = await UserService.get_by_email(db, email)
            if not user:
                return None
            
            # Check if account is locked
            if user.is_locked:
                return None
            
            # Check if user is verified
            if not user.is_verified:
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                # Increment failed login attempts
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                
                # Lock account if max attempts reached
                settings = get_settings()
                max_attempts = getattr(settings, 'max_login_attempts', 5)
                
                if user.failed_login_attempts >= max_attempts:
                    user.is_locked = True
                
                await db.commit()
                return None
            
            # Reset failed login attempts on successful login
            if user.failed_login_attempts:
                user.failed_login_attempts = 0
                await db.commit()
            
            return user
        except Exception as e:
            print(f"Error during login: {e}")
            return None
    
    @staticmethod
    async def is_account_locked(db: AsyncSession, email: str) -> bool:
        """Check if a user account is locked."""
        try:
            user = await UserService.get_by_email(db, email)
            if not user:
                return False
            return user.is_locked if user.is_locked is not None else False
        except Exception as e:
            print(f"Error checking if account is locked: {e}")
            return False
    
    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        try:
            query = select(User).offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    
    @staticmethod
    async def count_users(db: AsyncSession) -> int:
        """Count total number of users."""
        try:
            query = select(func.count()).select_from(User)
            result = await db.execute(query)
            return result.scalar_one()
        except Exception as e:
            print(f"Error counting users: {e}")
            return 0
    
    @staticmethod
    async def register_user(db: AsyncSession, user_data: Dict[str, Any], email_service=None) -> Optional[User]:
        """Register a new user and send verification email."""
        # This is similar to create but typically has additional registration-specific logic
        return await UserService.create(db, user_data, email_service)
    
    @staticmethod
    async def reset_password(db: AsyncSession, user_id: Union[UUID, str], new_password: str) -> bool:
        """Reset a user's password."""
        try:
            # Convert string ID to UUID if needed
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return False
            
            # Get the user
            user = await UserService.get_by_id(db, user_id)
            if not user:
                return False
            
            # Update password
            user.hashed_password = hash_password(new_password)
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"Error resetting password: {e}")
            return False
    
    @staticmethod
    async def verify_email_with_token(db: AsyncSession, user_id: Union[UUID, str], token: str) -> bool:
        """Verify a user's email with a token."""
        try:
            # Convert string ID to UUID if needed
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return False
            
            # Get the user
            user = await UserService.get_by_id(db, user_id)
            if not user or user.verification_token != token:
                return False
            
            # Verify the user
            user.is_verified = True
            user.verification_token = None
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"Error verifying email: {e}")
            return False
    
    @staticmethod
    async def unlock_user_account(db: AsyncSession, user_id: Union[UUID, str]) -> bool:
        """Unlock a user's account."""
        try:
            # Convert string ID to UUID if needed
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    return False
            
            # Get the user
            user = await UserService.get_by_id(db, user_id)
            if not user:
                return False
            
            # Unlock the account
            user.is_locked = False
            user.failed_login_attempts = 0
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            print(f"Error unlocking account: {e}")
            return False
    
    @staticmethod
    async def get(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Alias for get_by_id for compatibility with previous implementation."""
        return await UserService.get_by_id(db, user_id)