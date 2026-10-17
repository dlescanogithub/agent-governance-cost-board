"""Environment-only settings. This module does not read .env files."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime


class ConfigError(ValueError):
    """Raised when an environment variable cannot be parsed."""


@dataclass(frozen=True)
class Settings:
    log_level: str
    today: date
    review_max_age_days: int
    provider: str
    real_provider_enabled: bool
    real_provider_url: str
    max_attempts: int
    backoff_base_s: float
    backoff_cap_s: float

    @property
    def offline(self) -> bool:
        return (not self.real_provider_enabled) and self.provider != "real"


def _parse_date(value: str, name: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ConfigError(f"{name} must be YYYY-MM-DD, got {value!r}") from exc


def _parse_int(value: str, name: str, *, minimum: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}") from exc
    if parsed < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {parsed}")
    return parsed


def _parse_float(value: str, name: str, *, minimum: float) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {value!r}") from exc
    if parsed < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {parsed}")
    return parsed


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    flag = source.get("GOVERNANCE_REAL_PROVIDER_ENABLED", "0").strip()
    if flag not in {"0", "1"}:
        raise ConfigError("GOVERNANCE_REAL_PROVIDER_ENABLED must be 0 or 1")
    level = source.get("GOVERNANCE_LOG_LEVEL", "INFO").strip().upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        raise ConfigError(f"GOVERNANCE_LOG_LEVEL is not a known level: {level}")
    provider = source.get("GOVERNANCE_PROVIDER", "fake").strip().lower()
    return Settings(
        log_level=level,
        today=_parse_date(source.get("GOVERNANCE_TODAY", "2026-10-17"), "GOVERNANCE_TODAY"),
        review_max_age_days=_parse_int(
            source.get("GOVERNANCE_REVIEW_MAX_AGE_DAYS", "90"),
            "GOVERNANCE_REVIEW_MAX_AGE_DAYS",
            minimum=1,
        ),
        provider=provider,
        real_provider_enabled=flag == "1",
        real_provider_url=source.get("GOVERNANCE_REAL_PROVIDER_URL", "").strip(),
        max_attempts=_parse_int(
            source.get("GOVERNANCE_MAX_ATTEMPTS", "3"),
            "GOVERNANCE_MAX_ATTEMPTS",
            minimum=1,
        ),
        backoff_base_s=_parse_float(
            source.get("GOVERNANCE_BACKOFF_BASE_S", "0.05"),
            "GOVERNANCE_BACKOFF_BASE_S",
            minimum=0.0,
        ),
        backoff_cap_s=_parse_float(
            source.get("GOVERNANCE_BACKOFF_CAP_S", "2"),
            "GOVERNANCE_BACKOFF_CAP_S",
            minimum=0.0,
        ),
    )
