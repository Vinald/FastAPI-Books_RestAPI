"""
OAuth2 Social Login Service

Handles Google and GitHub OAuth2 authentication.
"""
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.schemas.oauth import OAuthUserInfo

logger = logging.getLogger("bookapi.oauth")


class OAuthService:
    """Service for handling OAuth2 social login."""

    # OAuth provider configurations
    PROVIDERS = {
        "google": {
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"],
        },
        "github": {
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
            "email_url": "https://api.github.com/user/emails",
            "scopes": ["read:user", "user:email"],
        },
    }

    def __init__(self):
        self.google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
        self.google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
        self.github_client_id = getattr(settings, "GITHUB_CLIENT_ID", None)
        self.github_client_secret = getattr(settings, "GITHUB_CLIENT_SECRET", None)
        self.redirect_base_url = getattr(settings, "OAUTH_REDIRECT_BASE_URL", "http://localhost:8000")

    def get_authorization_url(self, provider: str, state: Optional[str] = None) -> str:
        """
        Get the authorization URL for a provider.

        Args:
            provider: OAuth provider (google, github)
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect the user to
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        config = self.PROVIDERS[provider]
        redirect_uri = f"{self.redirect_base_url}/api/v1/oauth/{provider}/callback"

        params = {
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": " ".join(config["scopes"]),
        }

        if state:
            params["state"] = state

        if provider == "google":
            params["client_id"] = self.google_client_id
            params["access_type"] = "offline"
            params["prompt"] = "consent"
        elif provider == "github":
            params["client_id"] = self.github_client_id

        return f"{config['authorize_url']}?{urlencode(params)}"

    async def exchange_code_for_token(
            self,
            provider: str,
            code: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            provider: OAuth provider
            code: Authorization code from callback

        Returns:
            Token response from provider
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        config = self.PROVIDERS[provider]
        redirect_uri = f"{self.redirect_base_url}/api/v1/oauth/{provider}/callback"

        data = {
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        headers = {}

        if provider == "google":
            data["client_id"] = self.google_client_id
            data["client_secret"] = self.google_client_secret
        elif provider == "github":
            data["client_id"] = self.github_client_id
            data["client_secret"] = self.github_client_secret
            headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                config["token_url"],
                data=data,
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise Exception(f"Failed to exchange code for token: {response.text}")

            return response.json()

    async def get_user_info(
            self,
            provider: str,
            access_token: str
    ) -> OAuthUserInfo:
        """
        Get user info from OAuth provider.

        Args:
            provider: OAuth provider
            access_token: Access token from token exchange

        Returns:
            User info from provider
        """
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}")

        config = self.PROVIDERS[provider]

        headers = {"Authorization": f"Bearer {access_token}"}

        if provider == "github":
            headers["Authorization"] = f"token {access_token}"
            headers["Accept"] = "application/json"

        async with httpx.AsyncClient() as client:
            # Get user profile
            response = await client.get(
                config["userinfo_url"],
                headers=headers
            )

            if response.status_code != 200:
                logger.error(f"User info request failed: {response.text}")
                raise Exception(f"Failed to get user info: {response.text}")

            user_data = response.json()

            # Parse provider-specific response
            if provider == "google":
                return OAuthUserInfo(
                    provider="google",
                    provider_user_id=str(user_data["id"]),
                    email=user_data["email"],
                    username=user_data.get("email", "").split("@")[0],
                    first_name=user_data.get("given_name"),
                    last_name=user_data.get("family_name"),
                    avatar_url=user_data.get("picture")
                )

            elif provider == "github":
                # GitHub might not return email in profile, need to fetch separately
                email = user_data.get("email")

                if not email:
                    # Fetch emails separately
                    email_response = await client.get(
                        config["email_url"],
                        headers=headers
                    )

                    if email_response.status_code == 200:
                        emails = email_response.json()
                        # Get primary email
                        for e in emails:
                            if e.get("primary"):
                                email = e.get("email")
                                break
                        if not email and emails:
                            email = emails[0].get("email")

                # Parse name
                name = user_data.get("name", "")
                name_parts = name.split(" ", 1) if name else ["", ""]
                first_name = name_parts[0] if name_parts else None
                last_name = name_parts[1] if len(name_parts) > 1 else None

                return OAuthUserInfo(
                    provider="github",
                    provider_user_id=str(user_data["id"]),
                    email=email,
                    username=user_data.get("login"),
                    first_name=first_name,
                    last_name=last_name,
                    avatar_url=user_data.get("avatar_url")
                )

        raise ValueError(f"Unknown provider: {provider}")


# Global OAuth service instance
oauth_service = OAuthService()
