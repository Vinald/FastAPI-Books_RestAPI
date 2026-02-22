import uuid
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
    decode_token
)
from app.models.user import User
from app.schemas.auth import Token, RegisterRequest
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive"
            )

        # Create tokens (now returns tuple of token and jti)
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

    async def register(self, user_data: RegisterRequest, session: AsyncSession) -> User:
        """Register a new user."""
        # Check if email already exists
        existing_email = await self.user_service.get_user_by_email(user_data.email, session)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing_username = await self.user_service.get_user_by_username(user_data.username, session)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password and create user
        hashed_password = get_password_hash(user_data.password)

        # Create user
        user_dict = user_data.model_dump()
        user_dict["password"] = hashed_password

        new_user = User(**user_dict)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def logout(self, token: str) -> dict:
        """
        Logout by adding the current token to the blacklist.

        Args:
            token: The JWT access token to revoke

        Returns:
            Success message
        """
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")

            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token does not contain a JTI"
                )

            # Calculate remaining time until token expires
            import time
            current_time = int(time.time())
            expires_in = max(exp - current_time, 0) if exp else 3600

            # Add token to blacklist
            success = await add_token_to_blacklist(jti, expires_in)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to revoke token"
                )

            return {"message": "Successfully logged out"}

        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )

    async def logout_all_devices(self, user_uuid: str) -> dict:
        """
        Logout from all devices by blacklisting all tokens for a user.

        Args:
            user_uuid: The user's UUID

        Returns:
            Success message
        """
        # Blacklist all tokens for 7 days (max refresh token lifetime)
        expires_in = 7 * 24 * 60 * 60  # 7 days in seconds

        success = await blacklist_all_user_tokens(user_uuid, expires_in)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout from all devices"
            )

        return {"message": "Successfully logged out from all devices"}

    async def revoke_token(self, token: str) -> dict:
        """
        Revoke a specific token (admin functionality or self-revoke).

        Args:
            token: The JWT token to revoke

        Returns:
            Success message
        """
        return await self.logout(token)

    async def refresh_access_token(
            self,
            refresh_token: str,
            session: AsyncSession
    ) -> Token:
        """Refresh the access token using a refresh token."""
        try:
            payload = decode_token(refresh_token)

            # Check token type
            token_type = payload.get("type")
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            # Check if refresh token is blacklisted
            jti = payload.get("jti")
            if jti and await is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked"
                )

            user_uuid = payload.get("sub")
            if not user_uuid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            # Verify user exists
            user = await self.user_service.get_user_by_uuid(uuid.UUID(user_uuid), session)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account is inactive"
                )

            # Optionally: Revoke the old refresh token (rotation)
            if jti:
                exp = payload.get("exp")
                import time
                current_time = int(time.time())
                expires_in = max(exp - current_time, 0) if exp else 7 * 24 * 60 * 60
                await add_token_to_blacklist(jti, expires_in)

            # Create new tokens
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
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
