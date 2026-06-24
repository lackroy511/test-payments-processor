import logging

from fastapi import Depends, FastAPI

from src.core.config.lifespan import lifespan
from src.payments_api.api.router import router as main_router
from src.payments_api.common.deps.api_key import verify_api_key
from src.payments_api.common.exc.handlers import register_exception_handlers

log = logging.getLogger(__name__)

app = FastAPI(
    title="Payments API",
    docs_url="/api/payments/doc/",
    openapi_url="/api/payments/doc/openapi.json",
    description="Payments API",
    version="0.0.1",
    lifespan=lifespan,
)
app.include_router(main_router, dependencies=[Depends(verify_api_key)])
register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
