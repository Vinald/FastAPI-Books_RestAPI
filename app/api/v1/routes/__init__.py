"""
V1 API Routes Module
"""
from fastapi import APIRouter

from app.api.v1.routes import auth, user, admin, book, review

# Create v1 router
v1_router = APIRouter()

# Include all v1 routes
v1_router.include_router(auth.auth_router)
v1_router.include_router(user.user_router)
v1_router.include_router(admin.admin_router)
v1_router.include_router(book.book_router)
v1_router.include_router(review.review_router)
