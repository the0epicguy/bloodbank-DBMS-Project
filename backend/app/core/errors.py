"""
Custom exception classes. Raised in services/repos, map to HTTP status codes.
    NotFound         → 404
    ConflictError    → 409
    ValidationFailed → 422
    Unauthorized     → 401
    Forbidden        → 403
"""

from fastapi import HTTPException, status


class NotFound(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationFailed(HTTPException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class Unauthorized(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class Forbidden(HTTPException):
    def __init__(self, detail: str = "You do not have permission to do this"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def register_exception_handlers(app):
    """Register global exception handlers on the FastAPI app."""
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected internal server error occurred."},
        )
