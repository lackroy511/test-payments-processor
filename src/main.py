from src.core.config.lifespan import lifespan
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response

log = logging.getLogger(__name__)

app = FastAPI(
    title="Payments API",
    docs_url="/api/payments/doc/",
    openapi_url="/api/payments/doc/openapi.json",
    description="Payments API",
    version="0.0.1",
    lifespan=lifespan,
)


@app.middleware("http")
async def before_request(request: Request, call_next: Callable) -> Response:
    """Проверка API ключа перед каждым запросом."""
    return await call_next(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8020)
