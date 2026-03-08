"""
V2 API Module

Enhanced API version with:
- Pagination support for list endpoints
- Search and filtering capabilities
- Sorting options
"""
from app.api.v2.routes import v2_router

__all__ = ["v2_router"]
