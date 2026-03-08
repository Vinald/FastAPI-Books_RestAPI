"""
API Module

This module contains all API versions:
- V1: Original API with basic functionality
- V2: Enhanced API with pagination, filtering, and sorting
"""
from app.api.v1.routes import v1_router
from app.api.v2.routes import v2_router

__all__ = ["v1_router", "v2_router"]
