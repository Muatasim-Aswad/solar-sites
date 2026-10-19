from typing import Literal

Code = Literal[
    "VALIDATION_ERROR",
    "UNAUTHENTICATED",
    "INVALID_CREDENTIALS",
    "EMAIL_EXISTS",
    "CSRF_FAILED",
    "ORIGIN_FORBIDDEN",
    "HOST_FORBIDDEN",
    "NOT_FOUND",
    "METHOD_NOT_ALLOWED",
    "REQUEST_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE",
    "PVGIS_NO_DATA",
    "PVGIS_UNAVAILABLE",
    "PVGIS_INVALID_RESPONSE",
    "INTERNAL_ERROR",
    "HTTP_ERROR",
]


class AppError(Exception):
    def __init__(self, code: Code, message: str) -> None:
        super().__init__(message)
        self.code: Code = code
        self.message = message
