from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import v1_router
from app.api.v2.routes import v2_router
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Setup logging
setup_logging(level="INFO")

# API Version Configuration
API_V1_PREFIX = "/api/v1"
API_V2_PREFIX = "/api/v2"
CURRENT_VERSION = "2.0.0"

description = """
## Book Management API

A RESTful API for managing books, users, and reviews.

### API Versions

- **V1** (`/api/v1`): Original API version with basic functionality
- **V2** (`/api/v2`): Enhanced API with pagination, filtering, and sorting support

### Features

- 📚 **Books**: Create, read, update, and delete books
- 👥 **Users**: User management with roles (user, admin)
- ⭐ **Reviews**: Book reviews with ratings
- 🔐 **Authentication**: JWT-based authentication with refresh tokens
- 📧 **Email Verification**: Email verification and password reset

### Versioning Strategy

This API uses URL path versioning. Each version is available at its own prefix:
- V1: `/api/v1/...`
- V2: `/api/v2/...`

V2 adds pagination support to list endpoints and enhanced filtering options.
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
        {"name": "Users", "description": "User management operations"},
        {"name": "Admin", "description": "Admin-only operations"},
        {"name": "Books", "description": "Book management operations"},
        {"name": "Reviews", "description": "Book review operations"},
    ]
)

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
app.include_router(v1_router, prefix=API_V1_PREFIX, tags=["V1"])
app.include_router(v2_router, prefix=API_V2_PREFIX, tags=["V2"])


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
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": CURRENT_VERSION}
