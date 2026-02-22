import uuid
from typing import Optional, List

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserUpdate


class UserService:
    @staticmethod
    async def get_all_users(session: AsyncSession) -> List[User]:
        """Get all users."""
        statement = select(User).order_by(desc(User.created_at))
        result = await session.execute(statement)
        users = result.scalars().all()
        return list(users)

    @staticmethod
    async def get_user_by_uuid(user_uuid: uuid.UUID, session: AsyncSession) -> Optional[User]:
        """Get a user by UUID."""
        statement = select(User).where(User.uuid == user_uuid).options(selectinload(User.books))
        result = await session.execute(statement)
        user = result.scalars().first()
        return user

    @staticmethod
    async def get_user_by_email(email: EmailStr, session: AsyncSession) -> Optional[User]:
        """Get a user by email."""
        statement = select(User).where(User.email == email)
        result = await session.execute(statement)
        user = result.scalars().first()
        return user

    @staticmethod
    async def get_user_by_username(username: str, session: AsyncSession) -> Optional[User]:
        """Get a user by username."""
        statement = select(User).where(User.username == username)
        result = await session.execute(statement)
        user = result.scalars().first()
        return user

    async def update_user(
            self,
            user_uuid: uuid.UUID,
            update_data: UserUpdate,
            session: AsyncSession,
            current_user: User
    ) -> User:
        """Update a user."""
        user_to_update = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        # Check if user is updating their own profile
        if user_to_update.uuid != current_user.uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile"
            )

        update_data_dict = update_data.model_dump(exclude_unset=True)

        # Check if email is being updated and if it's already taken
        if "email" in update_data_dict:
            existing_user = await self.get_user_by_email(update_data_dict["email"], session)
            if existing_user and existing_user.uuid != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Check if username is being updated and if it's already taken
        if "username" in update_data_dict:
            existing_user = await self.get_user_by_username(update_data_dict["username"], session)
            if existing_user and existing_user.uuid != user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )

        for key, value in update_data_dict.items():
            setattr(user_to_update, key, value)

        session.add(user_to_update)
        await session.commit()
        await session.refresh(user_to_update)
        return user_to_update

    async def delete_user(
            self,
            user_uuid: uuid.UUID,
            session: AsyncSession,
            current_user: User
    ) -> dict:
        """Delete a user."""
        user_to_delete = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        # Check if user is deleting their own account
        if user_to_delete.uuid != current_user.uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own account"
            )

        await session.delete(user_to_delete)
        await session.commit()
        return {"message": f"User {user_uuid} deleted successfully"}

    async def change_password(
            self,
            user_uuid: uuid.UUID,
            current_password: str,
            new_password: str,
            session: AsyncSession,
            current_user: User
    ) -> dict:
        """Change user password."""
        user = await self.get_user_by_uuid(user_uuid, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user is changing their own password
        if user.uuid != current_user.uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password"
            )

        # Verify current password
        if not verify_password(current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash and set new password
        user.password = get_password_hash(new_password)
        session.add(user)
        await session.commit()

        return {"message": "Password changed successfully"}
