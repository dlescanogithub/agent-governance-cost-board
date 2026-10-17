"""Secret-scanner cases. Tokens are built from pieces so this file has no literal key."""

from __future__ import annotations

import hashlib
from pathlib import Path

from governance_board.secretscan import scan_path, scan_text

ROOT = Path(".")


def _piece(prefix: str, body: str) -> str:
    return prefix + body


def test_each_key_shape_is_detected() -> None:
    cases = [
        ("xai_key", _piece("xai-", "a" * 20)),
        ("openai_key", _piece("sk-", "b" * 20)),
        ("openai_key", _piece("sk-proj-", "c" * 20)),
        ("anthropic_key", _piece("sk-ant-", "d" * 20)),
        ("elevenlabs_key", _piece("sk_", "e" * 20)),
        ("github_token", _piece("ghp_", "f" * 20)),
        ("github_pat", _piece("github_pat_", "g" * 22)),
        ("aws_access_key", _piece("AKIA", "A" * 16)),
        ("bearer_token", _piece("Bearer ", "h" * 20)),
        ("private_key", _piece("-----BEGIN ", "PRIVATE KEY-----")),
        ("private_key", _piece("-----BEGIN ", "RSA PRIVATE KEY-----")),
        ("private_key", _piece("-----BEGIN ", "OPENSSH PRIVATE KEY-----")),
        ("private_key", _piece("-----BEGIN ", "EC PRIVATE KEY-----")),
    ]
    for rule, text in cases:
        found = scan_text("mem", text)
        assert [item.rule for item in found] == [rule]


def test_short_or_marked_lines_are_ignored() -> None:
    negatives = [
        _piece("xai-", "a" * 19),
        _piece("sk-", "b" * 19),
        _piece("sk-proj-", "c" * 19),
        _piece("sk-ant-", "d" * 19),
        _piece("sk_", "e" * 19),
        _piece("ghp_", "f" * 19),
        _piece("github_pat_", "g" * 19),
        _piece("AKIA", "A" * 15),
        _piece("Bearer ", "h" * 19),
        "BEGIN PRIVATE KEY",
        "placeholder " + _piece("sk-", "b" * 20),
        "example-not-a-secret " + _piece("ghp_", "f" * 20),
    ]
    for text in negatives:
        assert scan_text("mem", text) == []


def test_repo_scan_and_binary_skip(tmp_path: Path) -> None:
    assert scan_path(ROOT) == []
    dirty = tmp_path / "notes.txt"
    dirty.write_text(_piece("AKIA", "A" * 16) + "\n", encoding="utf-8")
    binary = tmp_path / "image.png"
    binary.write_bytes(b"\xff" + _piece("AKIA", "A" * 16).encode("ascii"))
    found = scan_path(tmp_path)
    assert [item.rule for item in found] == ["aws_access_key"]
    assert all(not item.path.endswith("image.png") for item in found)


def test_secretscan_sha256_matches_provenance() -> None:
    digest = hashlib.sha256((ROOT / "src/governance_board/secretscan.py").read_bytes()).hexdigest()
    text = (ROOT / "docs/PROVENANCE.md").read_text(encoding="utf-8")
    assert f"sha256: {digest}" in text
