"""Central exception handlers — no stack traces or secrets in API responses."""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(self, status_code: int = 500, detail: str = "Internal server error"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class AuthenticationError(AppException):
    """Authentication failure."""

    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(status_code=401, detail=detail)


class AuthorizationError(AppException):
    """Authorization failure."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)


class ValidationError(AppException):
    """Validation failure."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)


class TenantAccessError(AppException):
    """Cross-tenant access attempt."""

    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application error",
            extra={"status_code": exc.status_code, "detail": exc.detail, "path": str(request.url)},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            extra={"path": str(request.url), "method": request.method},
        )
        # Never leak stack traces or internal details
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
