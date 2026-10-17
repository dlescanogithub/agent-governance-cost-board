"""Lightweight secret scan for the repo and for CI.

This is a pattern scan, not a guarantee. It does not phone home.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    (
        "assigned_secret",
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9/+=]{16,}['\"]"),
    ),
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
        if "placeholder" in line.lower() or "example-not-a-secret" in line.lower():
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
