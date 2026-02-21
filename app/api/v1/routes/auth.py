from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.auth import Token, RegisterRequest, RefreshTokenRequest
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
    description="Get a new access token using a refresh token."
)
async def refresh_token(
        token_data: RefreshTokenRequest,
        session: AsyncSession = Depends(get_session)
) -> Token:
    """Refresh access token using refresh token."""
    return await auth_service.refresh_access_token(token_data.refresh_token, session)
