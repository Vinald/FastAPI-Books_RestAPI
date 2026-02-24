import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.responses import ADMIN_RESPONSES
from app.core.security import get_admin_user
from app.models.user import User, UserRole
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    ShowUser,
    UserUpdateAdmin,
    UserCreateAdmin
)
from app.services.user_services import UserService

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

user_service = UserService()


@admin_router.post(
    "/users",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    summary="Create user with any role",
    description="Create a new user with any role (Admin only).",
    responses=ADMIN_RESPONSES
)
async def admin_create_user(
        user_data: UserCreateAdmin,
        session: AsyncSession = Depends(get_session),
        admin_user: User = Depends(get_admin_user)
) -> ShowUser:
    """Admin endpoint to create a user with any role."""
    new_user = await user_service.admin_create_user(user_data, session)
    return new_user


@admin_router.patch(
    "/users/{user_uuid}",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Update any user",
    description="Update any user including their role (Admin only).",
    responses=ADMIN_RESPONSES
)
async def admin_update_user(
        user_uuid: uuid.UUID,
        update_data: UserUpdateAdmin,
        session: AsyncSession = Depends(get_session),
        admin_user: User = Depends(get_admin_user)
) -> ShowUser:
    """Admin endpoint to update any user including role."""
    updated_user = await user_service.admin_update_user(user_uuid, update_data, session)
    return updated_user


@admin_router.delete(
    "/users/{user_uuid}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete any user",
    description="Delete any user (Admin only).",
    responses=ADMIN_RESPONSES
)
async def admin_delete_user(
        user_uuid: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        admin_user: User = Depends(get_admin_user)
) -> MessageResponse:
    """Admin endpoint to delete any user."""
    result = await user_service.admin_delete_user(user_uuid, session)
    return MessageResponse(**result)


@admin_router.patch(
    "/users/{user_uuid}/role",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Change user role",
    description="Change a user's role (Admin only).",
    responses=ADMIN_RESPONSES
)
async def admin_change_user_role(
        user_uuid: uuid.UUID,
        new_role: UserRole,
        session: AsyncSession = Depends(get_session),
        admin_user: User = Depends(get_admin_user)
) -> ShowUser:
    """Admin endpoint to change a user's role."""
    updated_user = await user_service.change_user_role(user_uuid, new_role, session)
    return updated_user


@admin_router.patch(
    "/users/{user_uuid}/activate",
    response_model=ShowUser,
    status_code=status.HTTP_200_OK,
    summary="Activate/Deactivate user",
    description="Activate or deactivate a user account (Admin only).",
    responses=ADMIN_RESPONSES
)
async def admin_toggle_user_active(
        user_uuid: uuid.UUID,
        is_active: bool,
        session: AsyncSession = Depends(get_session),
        admin_user: User = Depends(get_admin_user)
) -> ShowUser:
    """Admin endpoint to activate/deactivate a user."""
    updated_user = await user_service.toggle_user_active(user_uuid, is_active, session)
    return updated_user
