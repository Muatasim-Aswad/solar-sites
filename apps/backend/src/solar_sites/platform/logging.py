import json
import logging
from time import perf_counter

from starlette.types import Scope

http_logger = logging.getLogger("solar_sites.http")


def configure_logging() -> None:
    logger = logging.getLogger("solar_sites")
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        logger.addHandler(logging.StreamHandler())


def log_request_exception(scope: Scope, request_id: str) -> None:
    http_logger.exception(
        json.dumps(
            {
                "event": "request_exception",
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
            }
        )
    )


def log_request_completed(
    scope: Scope, request_id: str, status: int | None, started_at: float
) -> None:
    http_logger.info(
        json.dumps(
            {
                "event": "request_completed",
                "request_id": request_id,
                "method": scope["method"],
                "path": scope["path"],
                "status": status,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            }
        )
    )
