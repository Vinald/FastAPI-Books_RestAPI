import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import UserNotFoundException
from app.core.responses import PUBLIC_RESPONSES, AUTH_RESPONSES
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    ShowUser,
    UserWithBooks,
    UserUpdate,
    PasswordChange
)
from app.services.user_services import UserService

user_router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

user_service = UserService()


@user_router.get(
    "/me",
    response_model=UserWithBooks,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get the currently authenticated user's profile with their books.",
    responses=AUTH_RESPONSES
)
async def get_me(
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(get_session)
) -> UserWithBooks:
    """Get current authenticated user."""
    user = await user_service.get_user_by_uuid(current_user.uuid, session)
    return user


@user_router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the current user's password.",
    responses=AUTH_RESPONSES
)
async def change_password(
        password_data: PasswordChange,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Change current user's password."""
    result = await user_service.change_password(
        user_uuid=current_user.uuid,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
        session=session,
        current_user=current_user
    )
    return MessageResponse(**result)


@user_router.get(
    "/",
    response_model=List[ShowUser],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve a list of all registered users.",
    responses={500: PUBLIC_RESPONSES[500]}
)
async def get_all_users(
        session: AsyncSession = Depends(get_session)
) -> List[ShowUser]:
    """Get all users."""
    users = await user_service.get_all_users(session)
    return users


@user_router.get(
    "/email/{email}",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Get user by email",
    description="Retrieve a specific user by their email address.",
    responses=PUBLIC_RESPONSES
)
async def get_user_by_email(
        email: str,
        session: AsyncSession = Depends(get_session)
) -> ShowUser:
    """Get a user by email."""
    user = await user_service.get_user_by_email(email, session)
    if not user:
        raise UserNotFoundException(email)
    return user


@user_router.get(
    "/{user_uuid}",
    response_model=UserWithBooks,
    status_code=status.HTTP_200_OK,
    summary="Get user by UUID",
    description="Retrieve a specific user by their UUID, including their books.",
    responses=PUBLIC_RESPONSES
)
async def get_user_by_uuid(
        user_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session)
) -> UserWithBooks:
    """Get a user by UUID."""
    user = await user_service.get_user_by_uuid(user_uuid, session)
    if not user:
        raise UserNotFoundException(user_uuid)
    return user


@user_router.patch(
    "/{user_uuid}",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Update an existing user's information (can only update own profile, admins can update anyone).",
    responses=AUTH_RESPONSES
)
async def update_user(
        user_uuid: uuid.UUID,
        update_data: UserUpdate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> ShowUser:
    """Update a user."""
    updated_user = await user_service.update_user(
        user_uuid, update_data, session, current_user
    )
    return updated_user


@user_router.delete(
    "/{user_uuid}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    description="Delete a user from the database (can only delete own account, admins can delete anyone).",
    responses=AUTH_RESPONSES
)
async def delete_user(
        user_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Delete a user."""
    result = await user_service.delete_user(user_uuid, session, current_user)
    return MessageResponse(**result)
