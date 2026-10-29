"""
Custom exception classes for the application.

These are raised in services/repos and caught by the global
error handler in main.py, which converts them to proper HTTP responses.

Mapping:
    NotFound       → 404
    ConflictError  → 409
    ValidationFailed → 422
    Unauthorized   → 401
    Forbidden      → 403
"""

from fastapi import HTTPException, status


class NotFound(HTTPException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """Conflict — duplicate or state violation (409)."""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationFailed(HTTPException):
    """Business rule validation failed (422)."""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class Unauthorized(HTTPException):
    """Not logged in / bad or expired token (401)."""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class Forbidden(HTTPException):
    """Logged in but not allowed to do this (403)."""

    def __init__(self, detail: str = "You do not have permission to do this"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
