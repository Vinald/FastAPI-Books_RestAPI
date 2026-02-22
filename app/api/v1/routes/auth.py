from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_active_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import Token, RegisterRequest, RefreshTokenRequest, MessageResponse
from app.schemas.user import ShowUser
from app.services.auth_services import AuthService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

auth_service = AuthService()


@auth_router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password, returns JWT tokens."
)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session)
) -> Token:
    """Login with email (as username) and password."""
    return await auth_service.login(
        email=form_data.username,  # OAuth2 spec uses 'username' field
        password=form_data.password,
        session=session
    )


@auth_router.post(
    "/register",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account."
)
async def register(
        user_data: RegisterRequest,
        session: AsyncSession = Depends(get_session)
) -> ShowUser:
    """Register a new user."""
    return await auth_service.register(user_data, session)


@auth_router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Get a new access token using a refresh token. The old refresh token will be revoked."
)
async def refresh_token(
        token_data: RefreshTokenRequest,
        session: AsyncSession = Depends(get_session)
) -> Token:
    """Refresh access token using refresh token."""
    return await auth_service.refresh_access_token(token_data.refresh_token, session)


@auth_router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Revoke the current access token. The token will be blacklisted and cannot be used again."
)
async def logout(
        token: str = Depends(oauth2_scheme),
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Logout by revoking the current token."""
    result = await auth_service.logout(token)
    return MessageResponse(**result)


@auth_router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout from all devices",
    description="Revoke all tokens for the current user. User will be logged out from all devices."
)
async def logout_all_devices(
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Logout from all devices by invalidating all tokens."""
    result = await auth_service.logout_all_devices(str(current_user.uuid))
    return MessageResponse(**result)
