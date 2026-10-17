"""Bounded retries with a capped exponential backoff."""

from __future__ import annotations

import time
from collections.abc import Callable


class RetryError(RuntimeError):
    def __init__(self, attempts: int, last: BaseException) -> None:
        super().__init__(f"failed after {attempts} attempts: {last}")
        self.attempts = attempts
        self.last = last


def call_with_retry(
    fn: Callable[[], object],
    *,
    max_attempts: int,
    base_delay_s: float,
    backoff_cap_s: float,
    sleep: Callable[[float], None] = time.sleep,
    retry_on: tuple[type[BaseException], ...] = (OSError, TimeoutError),
) -> object:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if base_delay_s < 0 or backoff_cap_s < 0:
        raise ValueError("delays must be >= 0")
    last: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            last = exc
            if attempt == max_attempts:
                break
            delay = min(backoff_cap_s, base_delay_s * (2 ** (attempt - 1)))
            sleep(delay)
    assert last is not None
    raise RetryError(max_attempts, last) from last
