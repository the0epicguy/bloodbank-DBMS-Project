"""
core/errors.py
Custom exception classes and FastAPI global exception handlers.

All services raise one of: NotFoundError, ConflictError, ValidationError,
BusinessRuleError, or UnauthorizedError.  The handlers below translate them
to the correct HTTP status codes with a consistent JSON body:

    { "detail": "Human-readable error message" }

Register in main.py:
    from app.core.errors import register_exception_handlers
    register_exception_handlers(app)
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Domain exception hierarchy
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base class for all application-level errors."""
    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist in the database."""
    status_code = 404
    detail = "Resource not found."


class ConflictError(AppError):
    """
    Raised when an operation would violate a uniqueness constraint —
    e.g. duplicate phone number, issuing an already-issued blood unit.
    """
    status_code = 409
    detail = "Resource already exists or is in a conflicting state."


class ValidationError(AppError):
    """
    Raised when input data fails domain-level validation that Pydantic
    cannot enforce — e.g. blood group incompatibility.
    """
    status_code = 422
    detail = "Validation failed."


class BusinessRuleError(AppError):
    """
    Raised when a business rule is violated — e.g. donor not eligible,
    attempting to cancel a fulfilled request.
    """
    status_code = 400
    detail = "Business rule violation."


class UnauthorizedError(AppError):
    """Raised when the caller lacks the required role or permission."""
    status_code = 403
    detail = "You do not have permission to perform this action."


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach all custom exception handlers to the FastAPI application.
    Call this once in main.py after creating the app instance.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.detail})

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.detail})

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": exc.detail})
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
