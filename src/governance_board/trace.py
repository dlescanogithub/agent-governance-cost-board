"""JSONL trace events.

Native records use the keys documented in docs/architecture.md.
`normalize_raw` also accepts a small alternate shape (trace_id, nested usage)
so a file dropped in from another local eval harness can be aggregated.
That alternate map was not verified against a private source repo; see
docs/PROVENANCE.md.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class TraceError(ValueError):
    pass


@dataclass(frozen=True)
class TraceEvent:
    run_id: str
    agent_id: str
    version: str
    ts: datetime
    status: str
    tokens_in: int
    tokens_out: int
    cost_micro_usd: int
    latency_ms: int
    approval: str
    effects: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ts"] = self.ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        payload["effects"] = list(self.effects)
        return payload


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TraceError(f"{key} must be a non-empty string")
    return value


def _require_int(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TraceError(f"{key} must be an integer >= 0")
    return value


def _parse_ts(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TraceError(f"ts is not ISO-8601: {value!r}") from exc
    return parsed


def normalize_raw(raw: dict[str, Any]) -> dict[str, Any]:
    """Fold alternate keys into the native event shape."""
    usage_raw = raw.get("usage")
    cost_raw = raw.get("cost")
    usage = usage_raw if isinstance(usage_raw, dict) else {}
    cost = cost_raw if isinstance(cost_raw, dict) else {}
    status = raw.get("status", raw.get("outcome"))
    if status == "success":
        status = "ok"
    elif status in {"failure", "failed"}:
        status = "error"
    effects = raw.get("effects", raw.get("tool_effects", []))
    tokens_in = raw.get("tokens_in", usage.get("prompt_tokens", usage.get("input_tokens")))
    tokens_out = raw.get("tokens_out", usage.get("completion_tokens", usage.get("output_tokens")))
    cost_micro = raw.get("cost_micro_usd", cost.get("micro_usd"))
    return {
        "run_id": raw.get("run_id", raw.get("trace_id")),
        "agent_id": raw.get("agent_id", raw.get("agent")),
        "version": raw.get("version", raw.get("agent_version", "unknown")),
        "ts": raw.get("ts", raw.get("timestamp")),
        "status": status,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_micro_usd": cost_micro,
        "latency_ms": raw.get("latency_ms", raw.get("elapsed_ms")),
        "approval": raw.get("approval", raw.get("human_approval", "none")),
        "effects": effects,
    }


def parse_event(raw: dict[str, Any]) -> TraceEvent:
    data = normalize_raw(raw)
    status = _require_str(data, "status")
    approval = _require_str(data, "approval")
    if status not in {"ok", "error", "rejected"}:
        raise TraceError(f"status {status!r} is not ok|error|rejected")
    if approval not in {"none", "approved", "rejected"}:
        raise TraceError(f"approval {approval!r} is not none|approved|rejected")
    effects_raw = data.get("effects")
    if not isinstance(effects_raw, list) or not all(isinstance(item, str) for item in effects_raw):
        raise TraceError("effects must be a list of strings")
    ts_raw = data.get("ts")
    if not isinstance(ts_raw, str):
        raise TraceError("ts must be a string")
    return TraceEvent(
        run_id=_require_str(data, "run_id"),
        agent_id=_require_str(data, "agent_id"),
        version=_require_str(data, "version"),
        ts=_parse_ts(ts_raw),
        status=status,
        tokens_in=_require_int(data, "tokens_in"),
        tokens_out=_require_int(data, "tokens_out"),
        cost_micro_usd=_require_int(data, "cost_micro_usd"),
        latency_ms=_require_int(data, "latency_ms"),
        approval=approval,
        effects=tuple(effects_raw),
    )


def loads_jsonl(text: str) -> tuple[TraceEvent, ...]:
    events: list[TraceEvent] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceError(f"line {line_no}: invalid JSON") from exc
        if not isinstance(raw, dict):
            raise TraceError(f"line {line_no}: event must be an object")
        try:
            events.append(parse_event(raw))
        except TraceError as exc:
            raise TraceError(f"line {line_no}: {exc}") from exc
    return tuple(events)


def load_jsonl(path: Path) -> tuple[TraceEvent, ...]:
    return loads_jsonl(path.read_text(encoding="utf-8"))


def dump_jsonl(events: Iterable[TraceEvent]) -> str:
    return "".join(json.dumps(event.to_dict(), sort_keys=True) + "\n" for event in events)


def iter_events(path: Path) -> Iterator[TraceEvent]:
    yield from load_jsonl(path)
