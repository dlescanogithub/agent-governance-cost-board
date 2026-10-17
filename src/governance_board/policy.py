"""Policy-as-code checks for an agent inventory.

The tier rubric lives in docs/RISK_RUBRIC.md. This module enforces the matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from governance_board.effects import ALLOWED_PROVIDERS
from governance_board.inventory import Agent, Inventory

HUMAN_ENFORCEMENT = frozenset({"runtime_effect_check", "human_queue"})


@dataclass(frozen=True)
class Violation:
    rule: str
    agent_id: str | None
    message: str

    def to_dict(self) -> dict[str, str | None]:
        return {"rule": self.rule, "agent_id": self.agent_id, "message": self.message}


@dataclass(frozen=True)
class PolicyReport:
    violations: tuple[Violation, ...]

    @property
    def ok(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "violations": [item.to_dict() for item in self.violations],
        }


def _violation(rule: str, agent_id: str | None, message: str) -> Violation:
    return Violation(rule=rule, agent_id=agent_id, message=message)


def _has_enforced_human_gate(agent: Agent) -> bool:
    return any(
        gate.kind == "human" and gate.required and gate.enforced_at in HUMAN_ENFORCEMENT
        for gate in agent.approval_gates
    )


def check_policy(
    inventory: Inventory,
    *,
    today: date,
    prompts: dict[str, str] | None = None,
) -> PolicyReport:
    """Return every rule breach. `prompts` maps prompt_id to the current version."""
    found: list[Violation] = []
    seen: set[str] = set()
    for agent in inventory.agents:
        if agent.id in seen:
            found.append(_violation("unique_id", agent.id, "duplicate agent id"))
        seen.add(agent.id)
        found.extend(_check_agent(agent, today=today, max_age=inventory.review_max_age_days))
        if prompts is not None:
            current = prompts.get(agent.prompt_id)
            if current is None:
                found.append(
                    _violation(
                        "prompt_registered",
                        agent.id,
                        f"prompt_id {agent.prompt_id!r} is not in the registry",
                    )
                )
            elif current != agent.prompt_version:
                found.append(
                    _violation(
                        "prompt_version_current",
                        agent.id,
                        f"inventory prompt_version {agent.prompt_version} != registry current {current}",
                    )
                )
    found.sort(key=lambda item: (item.agent_id or "", item.rule, item.message))
    return PolicyReport(violations=tuple(found))


def _check_agent(agent: Agent, *, today: date, max_age: int) -> list[Violation]:
    found: list[Violation] = []
    if not agent.owner.strip():
        found.append(_violation("owner_required", agent.id, "owner is empty"))
    if agent.budget.per_run_micro_usd <= 0 or agent.budget.per_day_micro_usd <= 0:
        found.append(_violation("budget_required", agent.id, "per-run and per-day caps must be > 0"))
    if agent.budget.per_run_micro_usd > agent.budget.per_day_micro_usd:
        found.append(
            _violation(
                "cap_consistency",
                agent.id,
                "per-run cap is greater than per-day cap",
            )
        )
    if agent.slo.cost_per_run_micro_usd > agent.budget.per_run_micro_usd:
        found.append(
            _violation(
                "cap_consistency",
                agent.id,
                "SLO cost/run is greater than the per-run cap",
            )
        )
    age = (today - agent.last_review).days
    if age < 0:
        found.append(_violation("review_fresh", agent.id, "last_review is after the injected today"))
    elif age > max_age:
        found.append(
            _violation(
                "review_fresh",
                agent.id,
                f"last review is {age} days old; max is {max_age}",
            )
        )
    if agent.provider not in ALLOWED_PROVIDERS:
        found.append(
            _violation(
                "provider_allowlist",
                agent.id,
                f"provider {agent.provider!r} is not in {sorted(ALLOWED_PROVIDERS)}",
            )
        )
    if agent.kill_switch == "engaged" and agent.status != "disabled":
        found.append(
            _violation(
                "kill_switch_status",
                agent.id,
                "kill_switch engaged requires status disabled",
            )
        )
    if agent.risk_tier in {"medium", "high"}:
        if not agent.data_classes:
            found.append(_violation("tier_controls", agent.id, f"{agent.risk_tier} tier needs data_classes"))
        if not agent.eval_evidence:
            found.append(_violation("tier_controls", agent.id, f"{agent.risk_tier} tier needs eval_evidence"))
    if agent.risk_tier == "high":
        if not _has_enforced_human_gate(agent):
            found.append(
                _violation(
                    "high_risk_human_gate",
                    agent.id,
                    "high tier needs a required human gate enforced at runtime_effect_check or human_queue",
                )
            )
        if not agent.backup_owner.strip():
            found.append(_violation("high_risk_backup_owner", agent.id, "high tier needs a backup owner"))
        elif agent.backup_owner.strip() == agent.owner.strip():
            found.append(
                _violation(
                    "high_risk_backup_owner",
                    agent.id,
                    "backup owner must be a different role than owner",
                )
            )
    return found


def render_text(report: PolicyReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [f"policy: {status}", f"violations: {len(report.violations)}"]
    for item in report.violations:
        who = item.agent_id or "-"
        lines.append(f"- [{item.rule}] {who}: {item.message}")
    return "\n".join(lines) + "\n"
