import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.core.config.lifespan import lifespan
from src.core.config.settings import settings
from src.payments_api.common.exc.handlers import register_exception_handlers
from src.payments_api.api.router import router as main_router

log = logging.getLogger(__name__)

app = FastAPI(
    title="Payments API",
    docs_url="/api/payments/doc/",
    openapi_url="/api/payments/doc/openapi.json",
    description="Payments API",
    version="0.0.1",
    lifespan=lifespan,
)
app.include_router(main_router)
register_exception_handlers(app)


@app.middleware("http")
async def check_api_key(request: Request, call_next: Callable) -> Response:
    api_key = request.headers.get("X-API-Key")
    if not api_key or settings.access_api_key != api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "X-API-Key is required or invalid"},
        )

    return await call_next(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
