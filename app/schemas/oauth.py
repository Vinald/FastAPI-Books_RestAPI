"""
OAuth2 Social Login Schemas
"""
from typing import Optional

from pydantic import BaseModel, EmailStr


class OAuthUserInfo(BaseModel):
    """User info from OAuth provider"""
    provider: str
    provider_user_id: str
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    code: str
    state: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class OAuthProviderConfig(BaseModel):
    """OAuth provider configuration"""
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scopes: list[str]
