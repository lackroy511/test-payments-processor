import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.payments_api.common.exc.exceptions import BaseAppError

log = logging.getLogger(__name__)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("Unexpected error:", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error",
        },
    )


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, BaseAppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
            },
        )

    raise exc


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, unexpected_error_handler)
    app.add_exception_handler(BaseAppError, app_error_handler)
