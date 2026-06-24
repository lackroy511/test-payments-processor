from typing import Annotated

from fastapi import Header, HTTPException

from src.core.config.settings import settings


async def verify_api_key(
    x_api_key: Annotated[str, Header(alias=settings.access_api_name)],
) -> str:
    if x_api_key != settings.access_api_key:
        raise HTTPException(
            status_code=401,
            detail=f"{settings.access_api_name} is required or invalid",
        )
    return x_api_key
