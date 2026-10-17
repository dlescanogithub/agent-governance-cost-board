"""Seeded property checks. These are invariants over random inputs, not a spend study."""

from __future__ import annotations

import random
from datetime import date, datetime
from typing import Any

from governance_board.aggregate import aggregate
from governance_board.controls import kill_switch_blocks
from governance_board.evalkit.invariants import check_event, check_kill_switch
from governance_board.inventory import InventorySchemaError, parse_inventory
from governance_board.policy import PolicyReport, Violation, check_policy
from governance_board.prompts import current_versions, rollback
from governance_board.trace import TraceEvent

PROPERTY_SEED = 20261017
PROPERTY_TRIALS = 32
_TODAY = date(2026, 10, 17)
_TS = datetime(2026, 10, 10, 12, 0, 0)


def run_property_checks(
    *,
    seed: int = PROPERTY_SEED,
    trials: int = PROPERTY_TRIALS,
) -> list[str]:
    """Return human-readable failures. An empty list means the properties held."""
    rng = random.Random(seed)
    failures: list[str] = []
    failures.extend(_cap_breach_always_flagged(rng, trials))
    failures.extend(_kill_switch_always_blocks(rng, trials))
    failures.extend(_rollback_restores_previous(rng, trials))
    failures.extend(_owner_and_tier_required(rng, trials))
    return failures


def _event(*, run_id: str, cost: int, status: str = "ok", effects: tuple[str, ...] = ()) -> TraceEvent:
    return TraceEvent(
        run_id=run_id,
        agent_id="kb-search",
        version="1.1.0",
        ts=_TS,
        status=status,
        tokens_in=10,
        tokens_out=4,
        cost_micro_usd=cost,
        latency_ms=20,
        approval="none",
        effects=effects,
    )


def _inventory_with_cap(cap: int) -> Any:
    agent = _valid_agent()
    agent["budget"] = {"per_run_micro_usd": cap, "per_day_micro_usd": cap * 20}
    agent["slo"] = {"p95_latency_ms": 100_000, "cost_per_run_micro_usd": 2_000_000_000}
    return parse_inventory(
        {
            "schema_version": 1,
            "review_max_age_days": 90,
            "organization": "Harborline Cooperative",
            "agents": [agent],
        },
        source="property",
    )


def _cap_breach_always_flagged(rng: random.Random, trials: int) -> list[str]:
    failures: list[str] = []
    for index in range(trials):
        cap = rng.randint(1, 50_000)
        over = cap + rng.randint(1, 5_000)
        under = cap
        over_event = _event(run_id=f"over-{index}", cost=over, effects=("retrieve_kb_passage",))
        under_event = _event(run_id=f"under-{index}", cost=under, effects=("retrieve_kb_passage",))
        over_names = {item.name for item in check_event(over_event, per_run_cap_micro_usd=cap)}
        under_names = {item.name for item in check_event(under_event, per_run_cap_micro_usd=cap)}
        if "cost_within_cap" not in over_names:
            failures.append(f"cost {over} above cap {cap} was not flagged")
        if "cost_within_cap" in under_names:
            failures.append(f"cost {under} at cap {cap} was flagged")
        board = aggregate(_inventory_with_cap(cap), (over_event,))
        codes = {alert.code for alert in board.alerts}
        if "per_run_cap_exceeded" not in codes:
            failures.append(f"aggregator missed per-run cap {cap} for cost {over}")
        quiet = aggregate(_inventory_with_cap(cap), (under_event,))
        quiet_codes = {alert.code for alert in quiet.alerts}
        if "per_run_cap_exceeded" in quiet_codes:
            failures.append(f"aggregator flagged cost equal to cap {cap}")
    return failures


def _kill_switch_always_blocks(rng: random.Random, trials: int) -> list[str]:
    failures: list[str] = []
    for index in range(trials):
        status = rng.choice(["ok", "error", "rejected"])
        if not kill_switch_blocks("engaged"):
            failures.append("engaged kill switch did not block")
        if kill_switch_blocks("disengaged"):
            failures.append("disengaged kill switch blocked a run")
        leaked = _event(
            run_id=f"kill-{index}",
            cost=10,
            status=status,
            effects=("retrieve_kb_passage",) if rng.random() < 0.5 or status == "ok" else (),
        )
        if status != "ok" and not leaked.effects:
            leaked = _event(run_id=f"kill-{index}", cost=10, status="ok", effects=("retrieve_kb_passage",))
        blocked = check_kill_switch(leaked, kill_switch="engaged")
        if not any(item.name == "kill_switch_blocks" for item in blocked):
            failures.append(f"engaged kill switch allowed {leaked.status} with effects {leaked.effects}")
        open_run = _event(run_id=f"open-{index}", cost=10, status="ok", effects=("retrieve_kb_passage",))
        if check_kill_switch(open_run, kill_switch="disengaged"):
            failures.append("disengaged kill switch flagged a normal run")
    return failures


def _rollback_restores_previous(rng: random.Random, trials: int) -> list[str]:
    failures: list[str] = []
    for index in range(trials):
        _ = rng.random()
        previous = f"0.{index}.0"
        current = f"1.{index}.0"
        model_previous = f"sim-prev-{index}"
        registry = {
            "prompts": [
                {
                    "agent_id": "kb-search",
                    "versions": [
                        {
                            "version": previous,
                            "model": model_previous,
                            "provider": "sim",
                            "status": "previous",
                            "text": f"previous text {index}",
                        },
                        {
                            "version": current,
                            "model": "sim-balanced",
                            "provider": "sim",
                            "status": "current",
                            "text": f"current text {index}",
                        },
                    ],
                }
            ]
        }
        updated = rollback(registry, "kb-search", previous)
        if current_versions(updated)["kb-search"] != previous:
            failures.append(f"rollback left current at {current_versions(updated)['kb-search']}")
        versions = updated["prompts"][0]["versions"]
        by_version = {item["version"]: item for item in versions}
        if by_version[previous]["status"] != "current":
            failures.append("previous version was not marked current")
        if by_version[current]["status"] == "current":
            failures.append("old current version stayed current")
        if by_version[previous]["model"] != model_previous:
            failures.append("rollback dropped the previous model")
        if by_version[previous]["text"] != f"previous text {index}":
            failures.append("rollback dropped the previous prompt text")
    return failures


def _as_policy(raw: dict[str, Any]) -> PolicyReport:
    try:
        inventory = parse_inventory(raw, source="property")
    except InventorySchemaError as exc:
        return PolicyReport(tuple(Violation("schema", None, message) for message in exc.messages))
    return check_policy(inventory, today=_TODAY)


def _owner_and_tier_required(rng: random.Random, trials: int) -> list[str]:
    failures: list[str] = []
    for index in range(trials):
        owner_raw: dict[str, Any] = {
            "schema_version": 1,
            "review_max_age_days": 90,
            "organization": "Harborline Cooperative",
            "agents": [_valid_agent()],
        }
        owner_raw["agents"][0]["owner"] = rng.choice(["", "   "])
        owner_raw["agents"][0]["id"] = "kb-search"
        owner_report = _as_policy(owner_raw)
        if owner_report.ok or not any(item.rule == "owner_required" for item in owner_report.violations):
            failures.append(f"empty owner passed policy on trial {index}")
        tier_raw: dict[str, Any] = {
            "schema_version": 1,
            "review_max_age_days": 90,
            "organization": "Harborline Cooperative",
            "agents": [_valid_agent()],
        }
        del tier_raw["agents"][0]["risk_tier"]
        tier_report = _as_policy(tier_raw)
        if tier_report.ok or not any(item.rule == "schema" for item in tier_report.violations):
            failures.append(f"missing risk tier passed policy on trial {index}")
        good = _as_policy(
            {
                "schema_version": 1,
                "review_max_age_days": 90,
                "organization": "Harborline Cooperative",
                "agents": [_valid_agent()],
            }
        )
        if not good.ok:
            failures.append("valid low agent failed policy: " + "; ".join(item.rule for item in good.violations))
    return failures


def _valid_agent() -> dict[str, Any]:
    return {
        "id": "kb-search",
        "name": "Handbook search",
        "owner": "knowledge-steward",
        "backup_owner": "knowledge-backup",
        "version": "1.1.0",
        "model": "sim-small",
        "provider": "sim",
        "purpose": "Read the handbook",
        "data_classes": ["internal_ops"],
        "risk_tier": "low",
        "approval_gates": [
            {
                "id": "read-only",
                "kind": "none",
                "required": False,
                "enforced_at": "not_applicable",
                "effects_covered": [],
            }
        ],
        "budget": {"per_run_micro_usd": 50000, "per_day_micro_usd": 2000000},
        "slo": {"p95_latency_ms": 2500, "cost_per_run_micro_usd": 40000},
        "status": "active",
        "kill_switch": "disengaged",
        "last_review": "2026-09-01",
        "eval_evidence": ["evals/evidence/fleet.md#kb-search"],
        "prompt_id": "kb-search",
        "prompt_version": "1.1.0",
    }
