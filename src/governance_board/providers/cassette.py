"""Replay a JSON cassette of provider responses. No network."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from governance_board.providers import CassetteMiss, ProviderResult


class CassetteProvider:
    name = "cassette"

    def __init__(self, path: Path) -> None:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("responses"), dict):
            raise ValueError("cassette must be an object with a responses object")
        self._responses: dict[str, dict[str, object]] = loaded["responses"]

    @staticmethod
    def key_for(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def complete(self, prompt: str) -> ProviderResult:
        key = self.key_for(prompt)
        item = self._responses.get(key)
        if item is None:
            raise CassetteMiss(key)
        text = item.get("text")
        tokens_in = item.get("tokens_in")
        tokens_out = item.get("tokens_out")
        if not isinstance(text, str) or not isinstance(tokens_in, int) or not isinstance(tokens_out, int):
            raise ValueError("cassette entry is missing text or token counts")
        return ProviderResult(text=text, tokens_in=tokens_in, tokens_out=tokens_out, provider=self.name)
