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

@auth_router.post(
    "/verify-email",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user's email address using the verification token sent to their email.",
    responses={
        400: {"description": "Invalid or expired verification token, or email already verified"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def verify_email(
        request: VerifyEmailRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """
    Verify email address with the token received via email.

    The verification token is sent to the user's email after registration.
    This endpoint validates the token and marks the user's email as verified.
    """
    result = await auth_service.verify_email(request.token, session)
    return MessageResponse(**result)


@auth_router.post(
    "/resend-verification",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
    description="Resend the email verification link. Use this if the original email was not received.",
    responses={
        400: {"description": "Email already verified"},
        503: {"description": "Email service unavailable"},
        500: COMMON_RESPONSES[500]
    }
)
async def resend_verification_email(
        request: ResendVerificationRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """
    Resend the verification email to the user.

    For security reasons, this endpoint returns a success message regardless
    of whether the email exists in the system.
    """
    result = await auth_service.resend_verification_email(request.email, session)
    return MessageResponse(**result)


# =============================================================================
# Password Reset Endpoints
# =============================================================================

@auth_router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send a password reset link to the user's email address.",
    responses={
        503: {"description": "Email service unavailable"},
        500: COMMON_RESPONSES[500]
    }
)
async def forgot_password(
        request: ForgotPasswordRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """
    Request a password reset email.

    For security reasons, this endpoint returns a success message regardless
    of whether the email exists in the system.
    """
    result = await auth_service.forgot_password(request.email, session)
    return MessageResponse(**result)


@auth_router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset the user's password using the token received via email.",
    responses={
        400: {"description": "Invalid or expired reset token"},
        404: {"description": "User not found"},
        500: COMMON_RESPONSES[500]
    }
)
async def reset_password(
        request: ResetPasswordRequest,
        session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """
    Reset password using the token received via email.

    The reset token is valid for 1 hour after it was generated.
    """
    result = await auth_service.reset_password(
        token=request.token,
        new_password=request.new_password,
        session=session
    )
    return MessageResponse(**result)
