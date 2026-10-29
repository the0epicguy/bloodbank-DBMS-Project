"""
Custom exception classes for the application.

These are raised in services/repos and caught by the global
error handler in main.py, which converts them to proper HTTP responses.

Mapping:
    NotFound       → 404
    ConflictError  → 409
    ValidationFailed → 422
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
