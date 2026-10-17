"""Optional real HTTP provider. Off by default. Not used by evals or CI."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from urllib.request import Request, urlopen

from governance_board.providers import ProviderDisabled, ProviderResult
from governance_board.retry import RetryError, call_with_retry

Transport = Callable[[str, dict[str, Any]], dict[str, Any]]


def urllib_transport(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:  # noqa: S310 - URL comes from env, default off
        parsed = json.loads(response.read().decode("utf-8"))
    if not isinstance(parsed, dict):
        raise OSError("real provider returned a non-object")
    return parsed


class RealProvider:
    name = "real"

    def __init__(
        self,
        *,
        enabled: bool,
        url: str,
        max_attempts: int,
        base_delay_s: float,
        backoff_cap_s: float,
        transport: Transport | None = None,
    ) -> None:
        self.enabled = enabled
        self.url = url
        self.max_attempts = max_attempts
        self.base_delay_s = base_delay_s
        self.backoff_cap_s = backoff_cap_s
        self._transport = transport or urllib_transport

    def complete(self, prompt: str) -> ProviderResult:
        if not self.enabled:
            raise ProviderDisabled("real provider is off; set GOVERNANCE_REAL_PROVIDER_ENABLED=1 to enable it")
        if not self.url:
            raise ProviderDisabled("GOVERNANCE_REAL_PROVIDER_URL is empty")
        payload = {"prompt": prompt}

        def attempt() -> dict[str, Any]:
            return self._transport(self.url, payload)

        try:
            raw = call_with_retry(
                attempt,
                max_attempts=self.max_attempts,
                base_delay_s=self.base_delay_s,
                backoff_cap_s=self.backoff_cap_s,
            )
        except RetryError as exc:
            raise OSError(str(exc)) from exc
        if not isinstance(raw, dict):
            raise OSError("real provider returned a non-object")
        text = raw.get("text")
        tokens_in = raw.get("tokens_in", 0)
        tokens_out = raw.get("tokens_out", 0)
        if not isinstance(text, str) or not isinstance(tokens_in, int) or not isinstance(tokens_out, int):
            raise OSError("real provider payload missing text or token counts")
        return ProviderResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, provider=self.name)
