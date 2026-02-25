import time
import uuid
from datetime import timedelta
from typing import Optional

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsException,
    InactiveUserException,
    DuplicateEmailException,
    DuplicateUsernameException,
    InvalidTokenException,
    TokenExpiredException,
    RedisUnavailableException,
    UserNotFoundException,
    ValidationException,
    EmailNotVerifiedException,
    InvalidVerificationTokenException,
    EmailAlreadyVerifiedException,
    EmailSendingException
)
from app.core.redis import (
    add_token_to_blacklist,
    is_token_blacklisted,
    blacklist_all_user_tokens
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_verification_token,
    verify_verification_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.models.user import User, UserRole
from app.schemas.auth import Token, RegisterRequest
from app.services.email_service import email_service
from app.services.user_services import UserService


class AuthService:
    def __init__(self):
        self.user_service = UserService()

    async def authenticate_user(
            self,
            email: EmailStr,
            password: str,
            session: AsyncSession
    ) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await self.user_service.get_user_by_email(email, session)
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user

    async def login(
            self,
            email: EmailStr,
            password: str,
            session: AsyncSession
    ) -> Token:
        """Login a user and return access and refresh tokens."""
        user = await self.authenticate_user(email, password, session)

        if not user:
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InactiveUserException()

        # Check if email is verified
        if not user.is_verified:
            raise EmailNotVerifiedException()

        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, _ = create_access_token(
            data={"sub": str(user.uuid)},
            expires_delta=access_token_expires
        )
        refresh_token, _ = create_refresh_token(
            data={"sub": str(user.uuid)}
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def register(
            self,
            user_data: RegisterRequest,
            session: AsyncSession,
            send_verification: bool = True
    ) -> User:
        """Register a new user and send verification email."""
        # Check if email already exists
        existing_email = await self.user_service.get_user_by_email(user_data.email, session)
        if existing_email:
            raise DuplicateEmailException(user_data.email)

        # Check if username already exists
        existing_username = await self.user_service.get_user_by_username(user_data.username, session)
        if existing_username:
            raise DuplicateUsernameException(user_data.username)

        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)

        new_user = User(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=hashed_password,
            role=UserRole.USER,
            is_active=True,
            is_verified=False  # Not verified until email confirmation
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Send verification email
        if send_verification:
            verification_token = create_verification_token(new_user.email)
            email_sent = await email_service.send_verification_email(
                email=new_user.email,
                username=new_user.username,
                verification_token=verification_token
            )
            if not email_sent:
                # Log warning but don't fail registration
                import logging
                logging.getLogger("bookapi.auth").warning(
                    f"Failed to send verification email to {new_user.email}"
                )

        return new_user

    async def verify_email(self, token: str, session: AsyncSession) -> dict:
        """Verify user's email address using the verification token."""
        # Decode and validate token
        email = verify_verification_token(token)
        if not email:
            raise InvalidVerificationTokenException()

        # Find user by email
        user = await self.user_service.get_user_by_email(email, session)
        if not user:
            raise UserNotFoundException(email)

        # Check if already verified
        if user.is_verified:
            raise EmailAlreadyVerifiedException()

        # Mark as verified
        user.is_verified = True
        session.add(user)
        await session.commit()

        return {"message": "Email verified successfully. You can now log in."}

    async def resend_verification_email(self, email: EmailStr, session: AsyncSession) -> dict:
        """Resend verification email to user."""
        user = await self.user_service.get_user_by_email(email, session)
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, a verification link has been sent."}

        if user.is_verified:
            raise EmailAlreadyVerifiedException()

        # Create and send new verification token
        verification_token = create_verification_token(email)
        email_sent = await email_service.send_verification_email(
            email=email,
            username=user.username,
            verification_token=verification_token
        )

        if not email_sent:
            raise EmailSendingException()

        return {"message": "If the email exists, a verification link has been sent."}

    async def forgot_password(self, email: EmailStr, session: AsyncSession) -> dict:
        """Send password reset email."""
        user = await self.user_service.get_user_by_email(email, session)

        # Always return same message to prevent email enumeration
        if not user:
            return {"message": "If the email exists, a password reset link has been sent."}

        # Create and send password reset token
        reset_token = create_password_reset_token(email)
        email_sent = await email_service.send_password_reset_email(
            email=email,
            username=user.username,
            reset_token=reset_token
        )

        if not email_sent:
            raise EmailSendingException()

        return {"message": "If the email exists, a password reset link has been sent."}

    async def reset_password(
            self,
            token: str,
            new_password: str,
            session: AsyncSession
    ) -> dict:
        """Reset user's password using reset token."""
        # Decode and validate token
        email = verify_password_reset_token(token)
        if not email:
            raise InvalidVerificationTokenException()

        # Find user by email
        user = await self.user_service.get_user_by_email(email, session)
        if not user:
            raise UserNotFoundException(email)

        # Update password
        user.password = get_password_hash(new_password)
        session.add(user)
        await session.commit()

        return {"message": "Password reset successfully. You can now log in with your new password."}

    @staticmethod
    async def logout(token: str) -> dict:
        """Logout by adding the current token to the blacklist."""
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")

            if not jti:
                raise ValidationException("Token does not contain a JTI")

            current_time = int(time.time())
            expires_in = max(exp - current_time, 0) if exp else 3600

            success = await add_token_to_blacklist(jti, expires_in)

            if not success:
                raise RedisUnavailableException()

            return {"message": "Successfully logged out"}

        except (ValidationException, RedisUnavailableException):
            raise
        except Exception:
            raise InvalidTokenException()

    @staticmethod
    async def logout_all_devices(user_uuid: str) -> dict:
        """Logout from all devices by blacklisting all tokens for a user."""
        expires_in = 7 * 24 * 60 * 60

        success = await blacklist_all_user_tokens(user_uuid, expires_in)

        if not success:
            raise RedisUnavailableException()

        return {"message": "Successfully logged out from all devices"}

    async def revoke_token(self, token: str) -> dict:
        """Revoke a specific token."""
        return await self.logout(token)

    async def refresh_access_token(
            self,
            refresh_token: str,
            session: AsyncSession
    ) -> Token:
        """Refresh the access token using a refresh token."""
        try:
            payload = decode_token(refresh_token)

            token_type = payload.get("type")
            if token_type != "refresh":
                raise InvalidTokenException()

            jti = payload.get("jti")
            if jti and await is_token_blacklisted(jti):
                raise TokenExpiredException()

            user_uuid = payload.get("sub")
            if not user_uuid:
                raise InvalidTokenException()

            user = await self.user_service.get_user_by_uuid(uuid.UUID(user_uuid), session)
            if not user:
                raise UserNotFoundException(user_uuid)

            if not user.is_active:
                raise InactiveUserException()

            if jti:
                exp = payload.get("exp")
                current_time = int(time.time())
                expires_in = max(exp - current_time, 0) if exp else 7 * 24 * 60 * 60
                await add_token_to_blacklist(jti, expires_in)

            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token, _ = create_access_token(
                data={"sub": str(user.uuid)},
                expires_delta=access_token_expires
            )
            new_refresh_token, _ = create_refresh_token(
                data={"sub": str(user.uuid)}
            )

            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )
        except (InvalidTokenException, TokenExpiredException, UserNotFoundException, InactiveUserException):
            raise
        except Exception:
            raise InvalidTokenException()
