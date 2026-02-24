from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import book, auth, user, admin, review
from app.core.logging_config import setup_logging
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Setup logging
setup_logging(level="INFO")

version = "v1.0"
description = f"API version {version} - A simple book management API built with FastAPI and SQLAlchemy"

app = FastAPI(
    title="Book Management API",
    description=description,
    version=version,
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

# Include routers
app.include_router(auth.auth_router, prefix=f"/api/{version}")
app.include_router(user.user_router, prefix=f"/api/{version}")
app.include_router(admin.admin_router, prefix=f"/api/{version}")
app.include_router(book.book_router, prefix=f"/api/{version}")
app.include_router(review.review_router, prefix=f"/api/{version}")
