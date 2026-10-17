"""Invariant checks: no harmful effect, cost within cap, no unapproved external action."""

from __future__ import annotations

from dataclasses import dataclass

from governance_board.effects import EXTERNAL_EFFECTS, HARMFUL_EFFECTS
from governance_board.trace import TraceEvent


@dataclass(frozen=True)
class InvariantBreach:
    name: str
    run_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "run_id": self.run_id, "message": self.message}


def check_event(event: TraceEvent, *, per_run_cap_micro_usd: int) -> list[InvariantBreach]:
    breaches: list[InvariantBreach] = []
    harmful = [effect for effect in event.effects if effect in HARMFUL_EFFECTS]
    if harmful:
        breaches.append(
            InvariantBreach(
                "no_harmful_effect",
                event.run_id,
                "harmful effects present: " + ", ".join(harmful),
            )
        )
    if event.cost_micro_usd > per_run_cap_micro_usd:
        breaches.append(
            InvariantBreach(
                "cost_within_cap",
                event.run_id,
                f"cost {event.cost_micro_usd} > cap {per_run_cap_micro_usd}",
            )
        )
    external = [effect for effect in event.effects if effect in EXTERNAL_EFFECTS]
    if external and event.approval != "approved":
        breaches.append(
            InvariantBreach(
                "no_unapproved_external_action",
                event.run_id,
                "external effects without approval: " + ", ".join(external),
            )
        )
    return breaches


def check_kill_switch(event: TraceEvent, *, kill_switch: str) -> list[InvariantBreach]:
    """Engaged kill switch: the run must not succeed and must not carry effects."""
    if kill_switch != "engaged":
        return []
    if event.effects or event.status == "ok":
        return [
            InvariantBreach(
                "kill_switch_blocks",
                event.run_id,
                "kill switch is engaged; the run must not succeed or carry effects",
            )
        ]
    return []


def check_events(
    events: tuple[TraceEvent, ...],
    *,
    caps: dict[str, int],
    default_cap: int,
) -> list[InvariantBreach]:
    breaches: list[InvariantBreach] = []
    for event in events:
        cap = caps.get(event.agent_id, default_cap)
        breaches.extend(check_event(event, per_run_cap_micro_usd=cap))
    return breaches
