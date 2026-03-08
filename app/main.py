import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.api.v1.routes import v1_router
from app.api.v1.routes.files import file_router
from app.api.v1.routes.oauth import oauth_router
from app.api.v1.routes.websocket import ws_router
from app.api.v2.routes import v2_router
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import limiter, custom_rate_limit_handler

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger("bookapi")

# Try to import GraphQL (optional feature)
GRAPHQL_AVAILABLE = False
try:
    from strawberry.fastapi import GraphQLRouter

    GRAPHQL_AVAILABLE = True
except ImportError:
    logger.warning("Strawberry GraphQL not available. GraphQL endpoint disabled.")

# API Version Configuration
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"
CURRENT_VERSION = "3.0.0"

description = """
## Book Management API

A full-featured RESTful API for managing books, users, and reviews.

### API Versions

- **V1** (`/api/v1`): Original API with basic functionality
- **V2** (`/api/v2`): Enhanced API with pagination, filtering, and sorting

### Features

- 📚 **Books**: Create, read, update, and delete books
- 👥 **Users**: User management with roles (user, admin)
- ⭐ **Reviews**: Book reviews with ratings
- 🔐 **Authentication**: JWT-based authentication with refresh tokens
- 📧 **Email Verification**: Email verification and password reset
- 🔒 **OAuth2 Social Login**: Google and GitHub authentication
- 📁 **File Upload/Download**: Image and document handling with streaming
- 🔌 **WebSockets**: Real-time communication
- 📊 **GraphQL**: Alternative GraphQL API at `/graphql`
- ⚡ **Rate Limiting**: Request throttling for API protection
- 🚀 **Background Tasks**: Async task processing with Celery

### Versioning Strategy

This API uses URL path versioning:
- V1: `/api/v1/...`
- V2: `/api/v2/...`
- GraphQL: `/graphql`
- WebSocket: `/ws/connect`
"""

app = FastAPI(
    title="Book Management API",
    description=description,
    version=CURRENT_VERSION,
    terms_of_service="http://vinald.me",
    contact={
        "name": "Vinald",
        "email": "vinaldtest@gmail.com",
        "url": "http://vinald.me",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {"name": "Authentication", "description": "Auth operations including login, register, and token management"},
        {"name": "OAuth2 Social Login", "description": "Google and GitHub OAuth2 authentication"},
        {"name": "Users", "description": "User management operations"},
        {"name": "Admin", "description": "Admin-only operations"},
        {"name": "Books", "description": "Book management operations"},
        {"name": "Reviews", "description": "Book review operations"},
        {"name": "Files", "description": "File upload and download operations"},
        {"name": "WebSocket", "description": "Real-time communication endpoints"},
    ]
)

# Add rate limiter state
app.state.limiter = limiter

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Add Middleware (order matters - first added is outermost)
# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Version Routers
app.include_router(v1_router, prefix=API_V1_PREFIX)
app.include_router(v2_router, prefix=API_V2_PREFIX)

# Include additional routers
app.include_router(ws_router)  # WebSocket routes
app.include_router(file_router, prefix=API_V1_PREFIX)  # File routes
app.include_router(oauth_router, prefix=API_V1_PREFIX)  # OAuth routes


# Setup GraphQL
async def get_context(request: Request):
    """Get GraphQL context with database session and user."""
    from app.core.database import get_session
    from app.core.security import get_current_user_optional

    # Get database session
    session_gen = get_session()
    session = await session_gen.__anext__()

    # Try to get current user from token
    user = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            user = await get_current_user_optional(token, session)
        except Exception:
            pass

    return {"session": session, "user": user, "request": request}


# Import GraphQL schema
from app.graphql.schema import schema

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

# Mount static files for uploads
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Book Management API",
        "current_version": CURRENT_VERSION,
        "api_versions": {
            "v1": {
                "prefix": API_V1_PREFIX,
                "status": "stable",
                "description": "Original API version"
            },
            "v2": {
                "prefix": API_V2_PREFIX,
                "status": "stable",
                "description": "Enhanced API with pagination support"
            }
        },
        "features": {
            "graphql": "/graphql",
            "websocket": "/ws/connect",
            "oauth_providers": "/api/v1/oauth/providers",
            "file_upload": f"{API_V1_PREFIX}/files/upload"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": CURRENT_VERSION}
