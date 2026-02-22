import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.models.user import User, UserRole

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1.0/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    """
    Create a JWT access token with a unique JTI (JWT ID).

    Args:
        data: Payload data (usually contains 'sub' with user UUID)
        expires_delta: Optional custom expiration time

    Returns:
        Tuple of (encoded_jwt, jti) - the token and its unique ID for revocation
    """
    to_encode = data.copy()

    # Generate unique token ID for revocation tracking
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),  # Issued at
        "jti": jti,  # JWT ID for revocation
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    """
    Create a JWT refresh token with a unique JTI.

    Args:
        data: Payload data (usually contains 'sub' with user UUID)
        expires_delta: Optional custom expiration time

    Returns:
        Tuple of (encoded_jwt, jti) - the token and its unique ID for revocation
    """
    to_encode = data.copy()

    # Generate unique token ID for revocation tracking
    jti = str(uuid.uuid4())

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # Refresh tokens last 7 days

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": jti,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, jti


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)
) -> User:
    """Get the current authenticated user from the JWT token."""
    # Import here to avoid circular imports
    from app.core.redis import is_token_blacklisted, is_user_token_blacklisted

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_uuid: str = payload.get("sub")
        jti: str = payload.get("jti")
        iat: int = payload.get("iat")

        if user_uuid is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    # Check if this specific token is blacklisted
    if jti and await is_token_blacklisted(jti):
        raise revoked_exception

    # Check if all user tokens before a certain time are blacklisted (logout all devices)
    if iat and await is_user_token_blacklisted(user_uuid, iat):
        raise revoked_exception

    # Get user from database
    statement = select(User).where(User.uuid == uuid.UUID(user_uuid))
    result = await session.execute(statement)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


# =============================================================================
# Role-Based Access Control (RBAC) Dependencies
# =============================================================================

class RoleChecker:
    """
    Dependency class for checking user roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(RoleChecker([UserRole.ADMIN]))):
            ...
    """

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        return current_user


# Pre-configured role checkers for common use cases
require_admin = RoleChecker([UserRole.ADMIN])
require_moderator = RoleChecker([UserRole.MODERATOR, UserRole.ADMIN])
require_user = RoleChecker([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])


async def get_admin_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_moderator_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependency that requires at least moderator role."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator access required"
        )
    return current_user


def check_resource_ownership_or_admin(
        resource_owner_id: int,
        current_user: User
) -> bool:
    """
    Check if user owns the resource or is an admin.

    Args:
        resource_owner_id: The owner's user ID
        current_user: The current authenticated user

    Returns:
        True if user owns resource or is admin

    Raises:
        HTTPException: If user doesn't have access
    """
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.id == resource_owner_id:
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You don't have permission to access this resource"
    )
