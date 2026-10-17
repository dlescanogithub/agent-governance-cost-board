"""Keep the suite offline. A socket connect is a test failure."""

from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def guard(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise RuntimeError("network disabled in tests")

    monkeypatch.setattr(socket.socket, "connect", guard)
