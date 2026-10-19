import json
import logging
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from solar_sites.shared.errors import AppError, Code

logger = logging.getLogger("solar_sites.http")

STATUSES: dict[Code, int] = {
    "VALIDATION_ERROR": 422,
    "UNAUTHENTICATED": 401,
    "INVALID_CREDENTIALS": 401,
    "EMAIL_EXISTS": 409,
    "CSRF_FAILED": 403,
    "ORIGIN_FORBIDDEN": 403,
    "HOST_FORBIDDEN": 400,
    "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405,
    "REQUEST_TOO_LARGE": 413,
    "UNSUPPORTED_MEDIA_TYPE": 415,
    "PVGIS_NO_DATA": 422,
    "PVGIS_UNAVAILABLE": 503,
    "PVGIS_INVALID_RESPONSE": 502,
    "INTERNAL_ERROR": 500,
    "HTTP_ERROR": 400,
}


class ValidationIssue(BaseModel):
    field: str
    message: str
    type: str


class ErrorBody(BaseModel):
    status: int
    code: Code
    message: str
    request_id: str
    issues: list[ValidationIssue] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    status: {"model": ErrorEnvelope, "description": description}
    for status, description in {
        400: "Invalid host or request",
        401: "Sign in required or invalid credentials",
        403: "Origin or CSRF check failed",
        404: "Resource not found",
        405: "Method not allowed",
        408: "Request body timed out",
        409: "Email already registered",
        413: "Request body too large",
        415: "JSON body required",
        422: "Invalid fields or no solar data",
        500: "Unexpected server error",
        502: "Invalid solar data response",
        503: "Solar data temporarily unavailable",
    }.items()
}


def error_response(
    request_id: str,
    code: Code,
    message: str,
    *,
    status: int | None = None,
    issues: list[ValidationIssue] | None = None,
    exception: Exception | None = None,
) -> JSONResponse:
    status = status or STATUSES[code]
    level = logging.ERROR if status >= 500 else logging.INFO
    logger.log(
        level,
        json.dumps(
            {"event": "request_error", "request_id": request_id, "code": code, "status": status}
        ),
        exc_info=exception,
    )
    data = ErrorEnvelope(
        error=ErrorBody(
            status=status, code=code, message=message, request_id=request_id, issues=issues
        )
    )
    return JSONResponse(data.model_dump(exclude_none=True), status_code=status)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def application_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(
            request.state.request_id,
            exc.code,
            exc.message,
            exception=exc if STATUSES[exc.code] >= 500 else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        issues = [
            ValidationIssue(
                field=".".join(str(part) for part in issue["loc"][1:]) or "body",
                message=issue["msg"],
                type=issue["type"],
            )
            for issue in exc.errors()
        ]
        return error_response(
            request.state.request_id,
            "VALIDATION_ERROR",
            "Please check the submitted fields.",
            issues=issues,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        code: Literal["NOT_FOUND", "METHOD_NOT_ALLOWED", "HTTP_ERROR"] = "HTTP_ERROR"
        message = "The request could not be processed."
        if exc.status_code == 404:
            code, message = "NOT_FOUND", "Resource not found."
        elif exc.status_code == 405:
            code, message = "METHOD_NOT_ALLOWED", "Method not allowed."
        response = error_response(request.state.request_id, code, message, status=exc.status_code)
        if exc.headers:
            response.headers.update(exc.headers)
        return response
