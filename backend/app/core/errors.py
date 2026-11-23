"""Application error types and consistent JSON error envelope."""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "Authentication is required."


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    message = "You do not have access to this resource."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "The request conflicts with existing state."


class EntitlementError(AppError):
    status_code = 403
    code = "ENTITLEMENT_REQUIRED"
    message = "This analysis requires VIP access or a token unlock."


def _envelope(code: str, message: str, details: dict[str, Any], request: Request) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(request.state, "request_id", None),
        }
    }


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = exc if isinstance(exc, AppError) else AppError()
    return JSONResponse(
        status_code=error.status_code,
        content=_envelope(error.code, str(error), error.details, request),
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    return JSONResponse(
        status_code=422,
        content=_envelope(
            "VALIDATION_ERROR",
            "The request payload is invalid.",
            {"errors": errors},
            request,
        ),
    )
