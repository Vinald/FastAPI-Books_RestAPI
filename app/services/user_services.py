import uuid
from typing import Optional, List

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, UserUpdateAdmin, UserCreateAdmin, UserCreate


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

    @staticmethod
    async def create_user(user_data: UserCreate, session: AsyncSession) -> User:
        """Create a new user (public registration)."""
        # Check if email already exists
        existing_email = await UserService.get_user_by_email(user_data.email, session)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_username = await UserService.get_user_by_username(user_data.username, session)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user with default USER role
        user_dict = user_data.model_dump()
        user_dict["password"] = hashed_password
        user_dict["role"] = UserRole.USER  # Force USER role for public registration

        new_user = User(**user_dict)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def update_user(
            self,
            user_uuid: uuid.UUID,
            update_data: UserUpdate,
            session: AsyncSession,
            current_user: User
    ) -> User:
        """Update a user (self or admin)."""
        user_to_update = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        # Check if user is updating their own profile OR is an admin
        is_own_profile = user_to_update.uuid == current_user.uuid
        is_admin = current_user.role == UserRole.ADMIN

        if not is_own_profile and not is_admin:
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
        """Delete a user (self or admin)."""
        user_to_delete = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        # Check if user is deleting their own account OR is an admin
        is_own_account = user_to_delete.uuid == current_user.uuid
        is_admin = current_user.role == UserRole.ADMIN

        if not is_own_account and not is_admin:
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

    # =========================================================================
    # Admin-Only Methods
    # =========================================================================

    async def admin_create_user(
            self,
            user_data: UserCreateAdmin,
            session: AsyncSession
    ) -> User:
        """Admin: Create a user with any role."""
        # Check if email already exists
        existing_email = await self.get_user_by_email(user_data.email, session)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_username = await self.get_user_by_username(user_data.username, session)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user with specified role
        user_dict = user_data.model_dump()
        user_dict["password"] = hashed_password

        new_user = User(**user_dict)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def admin_update_user(
            self,
            user_uuid: uuid.UUID,
            update_data: UserUpdateAdmin,
            session: AsyncSession
    ) -> User:
        """Admin: Update any user including role."""
        user_to_update = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
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

    async def admin_delete_user(
            self,
            user_uuid: uuid.UUID,
            session: AsyncSession
    ) -> dict:
        """Admin: Delete any user."""
        user_to_delete = await self.get_user_by_uuid(user_uuid, session)

        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        await session.delete(user_to_delete)
        await session.commit()
        return {"message": f"User {user_uuid} deleted successfully"}

    async def change_user_role(
            self,
            user_uuid: uuid.UUID,
            new_role: UserRole,
            session: AsyncSession
    ) -> User:
        """Admin: Change a user's role."""
        user = await self.get_user_by_uuid(user_uuid, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        user.role = new_role
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def toggle_user_active(
            self,
            user_uuid: uuid.UUID,
            is_active: bool,
            session: AsyncSession
    ) -> User:
        """Admin: Activate or deactivate a user."""
        user = await self.get_user_by_uuid(user_uuid, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_uuid} not found"
            )

        user.is_active = is_active
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
