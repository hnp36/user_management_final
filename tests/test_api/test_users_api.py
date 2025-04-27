from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user_model import User, UserRole
from app.schemas.user_schemas import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password

class UserService:
    @staticmethod
    async def create(db: AsyncSession, *, user_data: UserCreate) -> User:
        """Create a new user in the database."""
        # Check if email already exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalars().first():
            raise ValueError("Email already exists")
        
        # Create new user
        db_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            nickname=user_data.nickname if user_data.nickname else None,
            role=user_data.role if user_data.role else UserRole.AUTHENTICATED
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def get(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()
    
    @staticmethod
    async def update(db: AsyncSession, *, user_id: UUID, user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user's information."""
        # Get the user to update
        user = await UserService.get(db, user_id)
        if not user:
            return None
        
        # Update password if provided
        if "password" in user_data:
            user_data["hashed_password"] = hash_password(user_data.pop("password"))
        
        # Update user fields
        update_stmt = update(User).where(User.id == user_id).values(**user_data)
        await db.execute(update_stmt)
        await db.commit()
        
        # Refresh and return updated user
        return await UserService.get(db, user_id)
    
    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> bool:
        """Delete a user by ID."""
        # Check if user exists
        user = await UserService.get(db, user_id)
        if not user:
            return False
        
        # Delete the user
        delete_stmt = delete(User).where(User.id == user_id)
        await db.execute(delete_stmt)
        await db.commit()
        return True
    
    @staticmethod
    async def authenticate(db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """Authenticate a user."""
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        
        # Check if account is locked
        if UserService.is_account_locked(user):
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            
            # Lock account if max attempts reached
            if user.failed_login_attempts >= 5:  # Assuming max attempts is 5
                user.is_locked = True
            
            await db.commit()
            return None
        
        # Reset failed login attempts on successful login
        if user.failed_login_attempts:
            user.failed_login_attempts = 0
            await db.commit()
        
        return user if user.is_verified else None
    
    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Check if a user account is locked."""
        return user.is_locked if user.is_locked is not None else False
    
    @staticmethod
    async def list_users(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        # This is the correct SQLAlchemy 2.0 syntax for select
        query = select(User).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_users(db: AsyncSession) -> int:
        """Count total number of users."""
        query = select(func.count()).select_from(User)
        result = await db.execute(query)
        return result.scalar_one()