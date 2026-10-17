"""Run YAML eval cases. A failing invariant is a failing gate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from governance_board.config import Settings
from governance_board.evalkit.invariants import InvariantBreach, check_events
from governance_board.trace import TraceEvent, parse_event


class EvalError(ValueError):
    pass


@dataclass(frozen=True)
class EvalResult:
    case_count: int
    breaches: tuple[InvariantBreach, ...]

    @property
    def ok(self) -> bool:
        return not self.breaches


def assert_offline(settings: Settings) -> None:
    if not settings.offline:
        raise EvalError("eval harness refused a real provider; unset GOVERNANCE_REAL_PROVIDER_ENABLED")


def _events_from_case(case: dict[str, Any]) -> tuple[TraceEvent, ...]:
    raw_events = case.get("events")
    if not isinstance(raw_events, list):
        raise EvalError(f"case {case.get('name')!r} needs an events list")
    events: list[TraceEvent] = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            raise EvalError("event must be a mapping")
        events.append(parse_event(raw))
    return tuple(events)


def _caps_from_case(case: dict[str, Any]) -> dict[str, int]:
    raw = case.get("per_run_caps", {})
    if not isinstance(raw, dict):
        raise EvalError("per_run_caps must be a mapping")
    caps: dict[str, int] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or isinstance(value, bool) or not isinstance(value, int):
            raise EvalError("per_run_caps values must be integers")
        caps[key] = value
    return caps


def run_document(document: dict[str, Any], *, settings: Settings) -> EvalResult:
    assert_offline(settings)
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvalError("eval file needs a non-empty cases list")
    breaches: list[InvariantBreach] = []
    for case in cases:
        if not isinstance(case, dict):
            raise EvalError("case must be a mapping")
        default_cap = case.get("default_cap", 10**12)
        if isinstance(default_cap, bool) or not isinstance(default_cap, int):
            raise EvalError("default_cap must be an integer")
        breaches.extend(
            check_events(
                _events_from_case(case),
                caps=_caps_from_case(case),
                default_cap=default_cap,
            )
        )
    return EvalResult(case_count=len(cases), breaches=tuple(breaches))


def run_path(path: Path, *, settings: Settings) -> EvalResult:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise EvalError(f"{path} is not a mapping")
    return run_document(loaded, settings=settings)
