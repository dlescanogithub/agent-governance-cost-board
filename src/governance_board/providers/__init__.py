"""Model providers. The real adapter is off unless an env flag says otherwise."""

from __future__ import annotations

from dataclasses import dataclass


class ProviderDisabled(RuntimeError):
    pass


class CassetteMiss(KeyError):
    pass


@dataclass(frozen=True)
class ProviderResult:
    text: str
    tokens_in: int
    tokens_out: int
    provider: str
