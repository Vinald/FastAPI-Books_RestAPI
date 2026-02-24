"""
Standard HTTP status codes and response schemas for API documentation.
"""
from typing import Dict, Any

from pydantic import BaseModel


# =============================================================================
# Response Schemas
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str

    class Config:
        json_schema_extra = {
            "example": {"detail": "Error message description"}
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    detail: list[dict[str, Any]]

    class Config:
        json_schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "field_name"],
                        "msg": "field required",
                        "type": "value_error.missing"
                    }
                ]
            }
        }


# =============================================================================
# HTTP Status Codes Reference
# =============================================================================

class HTTPStatus:
    """HTTP Status codes used in the API."""

    # Success codes (2xx)
    OK = 200  # GET, PATCH, DELETE success
    CREATED = 201  # POST success (resource created)
    NO_CONTENT = 204  # DELETE success (no response body)

    # Client error codes (4xx)
    BAD_REQUEST = 400  # Invalid input, duplicate resource
    UNAUTHORIZED = 401  # Missing or invalid authentication
    FORBIDDEN = 403  # Authenticated but not authorized
    NOT_FOUND = 404  # Resource not found
    METHOD_NOT_ALLOWED = 405  # HTTP method not supported
    CONFLICT = 409  # Resource conflict (e.g., duplicate)
    UNPROCESSABLE_ENTITY = 422  # Validation error
    TOO_MANY_REQUESTS = 429  # Rate limit exceeded

    # Server error codes (5xx)
    INTERNAL_SERVER_ERROR = 500  # Unexpected server error
    SERVICE_UNAVAILABLE = 503  # Service temporarily unavailable


# =============================================================================
# Common Response Definitions for OpenAPI
# =============================================================================

COMMON_RESPONSES: Dict[int, Dict[str, Any]] = {
    400: {
        "description": "Bad Request - Invalid input or duplicate resource",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "duplicate_email": {
                        "summary": "Duplicate email",
                        "value": {"detail": "User with email 'test@example.com' already exists"}
                    },
                    "duplicate_review": {
                        "summary": "Duplicate review",
                        "value": {"detail": "You have already reviewed this book"}
                    },
                    "invalid_input": {
                        "summary": "Invalid input",
                        "value": {"detail": "Current password is incorrect"}
                    }
                }
            }
        }
    },
    401: {
        "description": "Unauthorized - Authentication required or invalid",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "missing_token": {
                        "summary": "Missing token",
                        "value": {"detail": "Not authenticated"}
                    },
                    "invalid_credentials": {
                        "summary": "Invalid credentials",
                        "value": {"detail": "Invalid email or password"}
                    },
                    "token_expired": {
                        "summary": "Token expired",
                        "value": {"detail": "Token has expired"}
                    },
                    "invalid_token": {
                        "summary": "Invalid token",
                        "value": {"detail": "Invalid or malformed token"}
                    }
                }
            }
        }
    },
    403: {
        "description": "Forbidden - Not authorized to perform this action",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "not_owner": {
                        "summary": "Not owner",
                        "value": {"detail": "You can only modify your own reviews"}
                    },
                    "admin_required": {
                        "summary": "Admin required",
                        "value": {"detail": "Admin privileges required"}
                    },
                    "inactive_account": {
                        "summary": "Inactive account",
                        "value": {"detail": "Your account has been deactivated"}
                    }
                }
            }
        }
    },
    404: {
        "description": "Not Found - Resource does not exist",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "book_not_found": {
                        "summary": "Book not found",
                        "value": {"detail": "Book with identifier 'uuid' not found"}
                    },
                    "user_not_found": {
                        "summary": "User not found",
                        "value": {"detail": "User with identifier 'uuid' not found"}
                    },
                    "review_not_found": {
                        "summary": "Review not found",
                        "value": {"detail": "Review with identifier 'uuid' not found"}
                    }
                }
            }
        }
    },
    422: {
        "description": "Validation Error - Request body validation failed",
        "model": ValidationErrorResponse
    },
    500: {
        "description": "Internal Server Error - Unexpected server error",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "example": {"detail": "An unexpected error occurred"}
            }
        }
    },
    503: {
        "description": "Service Unavailable - External service is down",
        "model": ErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "redis_unavailable": {
                        "summary": "Redis unavailable",
                        "value": {
                            "detail": "Token revocation service is currently unavailable. Please try again later."}
                    }
                }
            }
        }
    }
}

# =============================================================================
# Route-specific Response Sets
# =============================================================================

# For routes that don't require authentication
PUBLIC_RESPONSES = {
    404: COMMON_RESPONSES[404],
    500: COMMON_RESPONSES[500]
}

# For routes that require authentication
AUTH_RESPONSES = {
    401: COMMON_RESPONSES[401],
    403: COMMON_RESPONSES[403],
    404: COMMON_RESPONSES[404],
    500: COMMON_RESPONSES[500]
}

# For routes that create resources
CREATE_RESPONSES = {
    400: COMMON_RESPONSES[400],
    401: COMMON_RESPONSES[401],
    403: COMMON_RESPONSES[403],
    422: COMMON_RESPONSES[422],
    500: COMMON_RESPONSES[500]
}

# For admin-only routes
ADMIN_RESPONSES = {
    400: COMMON_RESPONSES[400],
    401: COMMON_RESPONSES[401],
    403: COMMON_RESPONSES[403],
    404: COMMON_RESPONSES[404],
    422: COMMON_RESPONSES[422],
    500: COMMON_RESPONSES[500]
}

# =============================================================================
# Status Code Descriptions for Documentation
# =============================================================================

STATUS_DESCRIPTIONS = {
    # 2xx Success
    200: "OK - Request succeeded",
    201: "Created - Resource created successfully",
    204: "No Content - Request succeeded with no response body",

    # 4xx Client Errors
    400: "Bad Request - Invalid input data or business rule violation",
    401: "Unauthorized - Authentication required or token invalid/expired",
    403: "Forbidden - Authenticated but lacks permission",
    404: "Not Found - Requested resource does not exist",
    405: "Method Not Allowed - HTTP method not supported for this endpoint",
    409: "Conflict - Resource already exists or state conflict",
    422: "Unprocessable Entity - Request body validation failed",
    429: "Too Many Requests - Rate limit exceeded",

    # 5xx Server Errors
    500: "Internal Server Error - Unexpected server error",
    502: "Bad Gateway - Upstream server error",
    503: "Service Unavailable - Service temporarily down",
    504: "Gateway Timeout - Upstream server timeout"
}
