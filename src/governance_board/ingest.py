"""Load JSONL in the runtime-evals trace shape.

Required fields: run_id, step, tokens_in, tokens_out, cost_micro_usd, latency_ms, outcome.
See docs/TRACE_INGEST.md for the mapping onto the board event.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from governance_board.trace import TraceError, TraceEvent, _parse_ts, _require_int, _require_str

SOURCE_GENERATED = "simulated-generator"
SOURCE_INGESTED = "ingested-runtime-evals"
SOURCES = frozenset({SOURCE_GENERATED, SOURCE_INGESTED})

_REQUIRED = (
    "run_id",
    "step",
    "tokens_in",
    "tokens_out",
    "cost_micro_usd",
    "latency_ms",
    "outcome",
)
_OPTIONAL = frozenset({"ts", "agent_id", "version", "approval", "effects"})
_ALLOWED = frozenset(_REQUIRED) | _OPTIONAL

_OUTCOME_TO_STATUS = {
    "ok": "ok",
    "success": "ok",
    "error": "error",
    "failure": "error",
    "failed": "error",
    "rejected": "rejected",
}


def _reject_unknown(raw: dict[str, Any]) -> None:
    unknown = sorted(set(raw) - _ALLOWED)
    if unknown:
        raise TraceError("unknown fields: " + ", ".join(unknown))


def event_from_runtime_evals(raw: dict[str, Any], *, default_ts: datetime) -> TraceEvent:
    """Validate one runtime-evals object and map it to a board event."""
    if not isinstance(raw, dict):
        raise TraceError("event must be an object")
    _reject_unknown(raw)
    missing = [key for key in _REQUIRED if key not in raw]
    if missing:
        raise TraceError("missing fields: " + ", ".join(missing))
    outcome = raw.get("outcome")
    if not isinstance(outcome, str) or outcome not in _OUTCOME_TO_STATUS:
        raise TraceError(f"outcome {outcome!r} is not a known runtime-evals outcome")
    step = _require_str(raw, "step")
    agent_raw = raw.get("agent_id", step)
    if not isinstance(agent_raw, str) or not agent_raw.strip():
        raise TraceError("agent_id must be a non-empty string when present")
    if agent_raw != step:
        raise TraceError("agent_id must match step when both are set")
    approval = raw.get("approval", "none")
    if approval not in {"none", "approved", "rejected"}:
        raise TraceError(f"approval {approval!r} is not none|approved|rejected")
    effects_raw = raw.get("effects", [])
    if not isinstance(effects_raw, list) or not all(isinstance(item, str) for item in effects_raw):
        raise TraceError("effects must be a list of strings")
    version = raw.get("version", "unknown")
    if not isinstance(version, str) or not version.strip():
        raise TraceError("version must be a non-empty string when present")
    ts_raw = raw.get("ts")
    if ts_raw is None:
        ts = default_ts
    elif isinstance(ts_raw, str):
        ts = _parse_ts(ts_raw)
    else:
        raise TraceError("ts must be a string when present")
    return TraceEvent(
        run_id=_require_str(raw, "run_id"),
        agent_id=step,
        version=version,
        ts=ts,
        status=_OUTCOME_TO_STATUS[outcome],
        tokens_in=_require_int(raw, "tokens_in"),
        tokens_out=_require_int(raw, "tokens_out"),
        cost_micro_usd=_require_int(raw, "cost_micro_usd"),
        latency_ms=_require_int(raw, "latency_ms"),
        approval=str(approval),
        effects=tuple(effects_raw),
    )


def loads_runtime_evals(text: str, *, default_ts: datetime) -> tuple[TraceEvent, ...]:
    events: list[TraceEvent] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise TraceError(f"line {line_no}: invalid JSON") from exc
        try:
            events.append(event_from_runtime_evals(raw, default_ts=default_ts))
        except TraceError as exc:
            raise TraceError(f"line {line_no}: {exc}") from exc
    if not events:
        raise TraceError("no events in runtime-evals file")
    return tuple(events)


def load_runtime_evals(path: Path, *, default_ts: datetime) -> tuple[TraceEvent, ...]:
    return loads_runtime_evals(path.read_text(encoding="utf-8"), default_ts=default_ts)
