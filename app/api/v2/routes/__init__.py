"""
V2 API Routes Module

This module contains V2 API routes with enhanced features:
- Pagination support
- Advanced filtering
- Improved response schemas
- Rate limiting metadata
"""
from fastapi import APIRouter

from app.api.v2.routes import auth, user, admin, book, review

# Create v2 router
v2_router = APIRouter()

# Include all v2 routes
v2_router.include_router(auth.auth_router)
v2_router.include_router(user.user_router)
v2_router.include_router(admin.admin_router)
v2_router.include_router(book.book_router)
v2_router.include_router(review.review_router)
