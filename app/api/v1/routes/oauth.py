"""
OAuth2 Social Login Routes

Google and GitHub OAuth2 authentication endpoints.
"""
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User, UserRole
from app.schemas.auth import Token
from app.services.oauth_service import oauth_service
from app.services.user_services import UserService

logger = logging.getLogger("bookapi.oauth")

oauth_router = APIRouter(
    prefix="/oauth",
    tags=["OAuth2 Social Login"],
)

user_service = UserService()


@oauth_router.get(
    "/{provider}/authorize",
    summary="Start OAuth flow",
    description="Redirect user to OAuth provider for authentication."
)
async def oauth_authorize(
        provider: str,
        redirect_uri: Optional[str] = Query(default=None, description="Frontend redirect URI after login")
):
    """
    Start the OAuth2 flow by redirecting to the provider's authorization page.

    Supported providers: google, github
    """
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}. Supported: google, github"
        )

    # Generate state for CSRF protection (can include redirect_uri)
    state = secrets.token_urlsafe(32)

    # In production, store state in session/cache with redirect_uri
    # For simplicity, we'll just use it for CSRF protection

    try:
        auth_url = oauth_service.get_authorization_url(provider, state=state)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"OAuth authorize error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@oauth_router.get(
    "/{provider}/callback",
    response_model=Token,
    summary="OAuth callback",
    description="Handle OAuth callback and create/login user."
)
async def oauth_callback(
        provider: str,
        code: str = Query(..., description="Authorization code from provider"),
        state: Optional[str] = Query(default=None, description="State parameter for CSRF protection"),
        session: AsyncSession = Depends(get_session)
):
    """
    Handle the OAuth2 callback from the provider.

    This endpoint:
    1. Exchanges the authorization code for an access token
    2. Fetches user info from the provider
    3. Creates a new user or logs in existing user
    4. Returns JWT tokens
    """
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}"
        )

    try:
        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token(provider, code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token"
            )

        # Get user info from provider
        user_info = await oauth_service.get_user_info(provider, access_token)

        if not user_info.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by OAuth provider"
            )

        # Check if user exists
        existing_user = await user_service.get_user_by_email(user_info.email, session)

        if existing_user:
            # User exists, log them in
            user = existing_user
            logger.info(f"OAuth login: existing user {user.email} via {provider}")
        else:
            # Create new user
            # Generate unique username if not provided or taken
            base_username = user_info.username or user_info.email.split("@")[0]
            username = base_username
            counter = 1

            while await user_service.get_user_by_username(username, session):
                username = f"{base_username}{counter}"
                counter += 1

            # Create user without password (OAuth users)
            from app.core.security import get_password_hash

            # Generate a random password for OAuth users (they won't use it)
            random_password = secrets.token_urlsafe(32)

            user = User(
                username=username,
                email=user_info.email,
                first_name=user_info.first_name,
                last_name=user_info.last_name,
                password=get_password_hash(random_password),
                role=UserRole.USER,
                is_active=True,
                is_verified=True,  # OAuth users are automatically verified
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"OAuth signup: new user {user.email} created via {provider}")

        # Generate JWT tokens
        token_data = {
            "sub": user.email,
            "uuid": str(user.uuid),
            "role": user.role.value
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}"
        )


@oauth_router.get(
    "/providers",
    summary="List available OAuth providers",
    description="Get list of configured OAuth providers."
)
async def list_providers():
    """Get list of available OAuth providers."""
    providers = []

    if getattr(settings, "GOOGLE_CLIENT_ID", None):
        providers.append({
            "name": "google",
            "display_name": "Google",
            "authorize_url": "/api/v1/oauth/google/authorize"
        })

    if getattr(settings, "GITHUB_CLIENT_ID", None):
        providers.append({
            "name": "github",
            "display_name": "GitHub",
            "authorize_url": "/api/v1/oauth/github/authorize"
        })

    return {
        "providers": providers,
        "message": "Use the authorize_url to start OAuth flow"
    }
