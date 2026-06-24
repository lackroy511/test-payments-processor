import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.core.config.logger import configure_logging
from src.core.db.base import engine as sql_alchemy_engine

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    try:
        log.info("Payments API is starting...")
        configure_logging()
        yield
    finally:
        log.info("Payments API is shutting down...")
        await sql_alchemy_engine.dispose()
