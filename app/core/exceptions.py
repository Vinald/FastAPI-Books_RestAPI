"""
Custom exception classes and error handling for the API.
"""
from typing import Any, Optional

from fastapi import HTTPException, status


class BookAPIException(HTTPException):
    """Base exception for BookAPI."""

    def __init__(
            self,
            status_code: int,
            detail: str,
            headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(BookAPIException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with identifier '{identifier}' not found"
        )


class BookNotFoundException(NotFoundException):
    """Book not found exception."""

    def __init__(self, book_id: Any):
        super().__init__(resource="Book", identifier=book_id)


class UserNotFoundException(NotFoundException):
    """User not found exception."""

    def __init__(self, user_id: Any):
        super().__init__(resource="User", identifier=user_id)


class ReviewNotFoundException(NotFoundException):
    """Review not found exception."""

    def __init__(self, review_id: Any):
        super().__init__(resource="Review", identifier=review_id)


class DuplicateResourceException(BookAPIException):
    """Resource already exists exception."""

    def __init__(self, resource: str, field: str, value: Any):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{resource} with {field} '{value}' already exists"
        )


class DuplicateEmailException(DuplicateResourceException):
    """Email already registered."""

    def __init__(self, email: str):
        super().__init__(resource="User", field="email", value=email)


class DuplicateUsernameException(DuplicateResourceException):
    """Username already taken."""

    def __init__(self, username: str):
        super().__init__(resource="User", field="username", value=username)


class DuplicateReviewException(BookAPIException):
    """User already reviewed this book."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this book"
        )


class UnauthorizedException(BookAPIException):
    """Authentication required exception."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidCredentialsException(UnauthorizedException):
    """Invalid login credentials."""

    def __init__(self):
        super().__init__(detail="Invalid email or password")


class TokenExpiredException(UnauthorizedException):
    """Token has expired."""

    def __init__(self):
        super().__init__(detail="Token has expired")


class InvalidTokenException(UnauthorizedException):
    """Invalid token."""

    def __init__(self):
        super().__init__(detail="Invalid or malformed token")


class EmailNotVerifiedException(BookAPIException):
    """Email not verified exception."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email address before logging in"
        )


class InvalidVerificationTokenException(BookAPIException):
    """Invalid or expired verification token."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


class EmailAlreadyVerifiedException(BookAPIException):
    """Email already verified."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )


class EmailSendingException(BookAPIException):
    """Failed to send email."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send email. Please try again later."
        )


class ForbiddenException(BookAPIException):
    """Access forbidden exception."""

    def __init__(self, detail: str = "You don't have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class OwnershipRequiredException(ForbiddenException):
    """Resource ownership required."""

    def __init__(self, resource: str):
        super().__init__(detail=f"You can only modify your own {resource}")


class AdminRequiredException(ForbiddenException):
    """Admin role required."""

    def __init__(self):
        super().__init__(detail="Admin privileges required")


class InactiveUserException(ForbiddenException):
    """User account is inactive."""

    def __init__(self):
        super().__init__(detail="Your account has been deactivated")


class ValidationException(BookAPIException):
    """Validation error exception."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class PasswordValidationException(ValidationException):
    """Password validation failed."""

    def __init__(self, detail: str = "Password does not meet requirements"):
        super().__init__(detail=detail)


class IncorrectPasswordException(BookAPIException):
    """Current password is incorrect."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )


class ServiceUnavailableException(BookAPIException):
    """External service unavailable."""

    def __init__(self, service: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is currently unavailable. Please try again later."
        )


class RedisUnavailableException(ServiceUnavailableException):
    """Redis service unavailable."""

    def __init__(self):
        super().__init__(service="Token revocation service")
