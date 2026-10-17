"""Deterministic fake provider. No network."""

from __future__ import annotations

from governance_board.providers import ProviderResult


class FakeProvider:
    name = "fake"

    def complete(self, prompt: str) -> ProviderResult:
        words = max(1, len(prompt.split()))
        return ProviderResult(
            text="simulated-fake-completion",
            tokens_in=words,
            tokens_out=4,
            provider=self.name,
        )
