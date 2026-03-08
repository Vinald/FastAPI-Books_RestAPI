"""
V2 Auth Routes

Authentication routes (same as V1, as auth typically doesn't change between versions)
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.responses import CREATE_RESPONSES, COMMON_RESPONSES
from app.core.security import get_current_active_user, oauth2_scheme
from app.models.user import User
from app.schemas.auth import (
    Token,
    RegisterRequest,
    RefreshTokenRequest,
    MessageResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.schemas.user import ShowUser
from app.services.auth_services import AuthService

auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_service = AuthService()


@auth_router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password, returns JWT tokens.",
    responses={
        401: COMMON_RESPONSES[401],
        403: COMMON_RESPONSES[403],
        500: COMMON_RESPONSES[500]
    }
)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session)
) -> Token:
    """Login with email (as username) and password."""
    return await auth_service.login(
        email=form_data.username,
        password=form_data.password,
        session=session
    )


@auth_router.post(
    "/register",
    response_model=ShowUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account.",
    responses=CREATE_RESPONSES
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
    description="Get a new access token using a refresh token. The old refresh token will be revoked.",
    responses={
        401: COMMON_RESPONSES[401],
        403: COMMON_RESPONSES[403],
        500: COMMON_RESPONSES[500]
    }
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
    description="Revoke the current access token. The token will be blacklisted and cannot be used again.",
    responses={
        401: COMMON_RESPONSES[401],
        503: COMMON_RESPONSES[503],
        500: COMMON_RESPONSES[500]
    }
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
    description="Revoke all tokens for the current user. User will be logged out from all devices.",
    responses={
        401: COMMON_RESPONSES[401],
        503: COMMON_RESPONSES[503],
        500: COMMON_RESPONSES[500]
    }
)
async def logout_all_devices(
        current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """Logout from all devices by invalidating all tokens."""
    result = await auth_service.logout_all_devices(str(current_user.uuid))
    return MessageResponse(**result)


# =============================================================================
# Email Verification Endpoints
# =============================================================================

@auth_router.get(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address via link",
    description="Verify user's email address by clicking the verification link sent to their email.",
    responses={
        400: {"description": "Invalid or expired verification token, or email already verified"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def verify_email_via_link(
        token: str,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Verify email using the token from the verification link."""
    result = await auth_service.verify_email(token, session)
    return MessageResponse(**result)


@auth_router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user's email address using a verification token.",
    responses={
        400: {"description": "Invalid or expired verification token, or email already verified"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def verify_email(
        verify_data: VerifyEmailRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Verify email using a verification token from request body."""
    result = await auth_service.verify_email(verify_data.token, session)
    return MessageResponse(**result)


@auth_router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
    description="Resend the email verification link to the user's email address.",
    responses={
        400: {"description": "Email already verified"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def resend_verification(
        resend_data: ResendVerificationRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Resend verification email."""
    result = await auth_service.resend_verification_email(resend_data.email, session)
    return MessageResponse(**result)


# =============================================================================
# Password Reset Endpoints
# =============================================================================

@auth_router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset link to be sent to the user's email.",
    responses={
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def forgot_password(
        forgot_data: ForgotPasswordRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Request password reset email."""
    result = await auth_service.forgot_password(forgot_data.email, session)
    return MessageResponse(**result)


@auth_router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset user's password using a reset token.",
    responses={
        400: {"description": "Invalid or expired reset token"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def reset_password(
        reset_data: ResetPasswordRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Reset password using reset token."""
    result = await auth_service.reset_password(
        token=reset_data.token,
        new_password=reset_data.new_password,
        session=session
    )
    return MessageResponse(**result)
