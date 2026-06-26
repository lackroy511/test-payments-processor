import asyncio
import logging
from functools import wraps
from typing import Any, Callable

log = logging.getLogger(__name__)


class Backoff:
    def __init__(
        self,
        exceptions: tuple[type[Exception], ...],
        max_retries: int = 3,
        start_delay: float = 0.1,
        factor: float = 2.0,
        max_delay: float = 5.0,
    ) -> None:
        self.exceptions = exceptions
        self.max_retries = max_retries
        self.start_delay = start_delay
        self.factor = factor
        self.max_delay = max_delay

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            delay = self.start_delay
            attempt = 0

            while True:
                try:
                    return await func(*args, **kwargs)
                except self.exceptions:
                    attempt += 1
                    if attempt >= self.max_retries:
                        log.exception("Error after %d retries:", attempt)
                        raise

                    await asyncio.sleep(delay)
                    delay = min(delay * self.factor, self.max_delay)

        return wrapper
