"""Secret scan shared across the portfolio repos.

This file is a vendored copy. Keep it identical to the other repos.
docs/PROVENANCE.md records the sha256 of this file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_BEGIN = "-----BEGIN "
_KIND = "(?:RSA |OPENSSH |EC )?"
_END = "PRIVATE KEY-----"

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("xai_key", re.compile(r"xai-[A-Za-z0-9_-]{20,}")),
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9]{20,}")),
    ("openai_key", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}")),
    ("elevenlabs_key", re.compile(r"sk_[A-Za-z0-9]{20,}")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer_token", re.compile(r"Bearer [A-Za-z0-9._~+/-]{20,}")),
    ("private_key", re.compile(_BEGIN + _KIND + _END)),
)

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "dist",
    "build",
    "demo-out",
}
SKIP_FILES = {".env.example"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "rule": self.rule}


def scan_text(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if "placeholder" in lowered or "example-not-a-secret" in lowered:
            continue
        for name, pattern in PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path=path, line=line_no, rule=name))
    return findings


def scan_path(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if root.is_file():
        return scan_text(str(root), root.read_text(encoding="utf-8", errors="replace"))
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(str(path), text))
    return findings
