"""Roll JSONL traces up to per-agent cost, latency, and approval stats."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from governance_board.inventory import Inventory
from governance_board.stats import percentile
from governance_board.trace import TraceEvent


@dataclass(frozen=True)
class Alert:
    code: str
    agent_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "agent_id": self.agent_id, "message": self.message}


@dataclass
class AgentRollup:
    agent_id: str
    runs: int
    errors: int
    cost_micro_usd_total: int
    cost_per_run_mean: float | None
    cost_per_run_p50: float | None
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    human_approval_rate: float | None
    rejection_rate: float | None
    max_day_cost_micro_usd: int
    budget_burn_ratio: float | None
    alerts: list[Alert] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "runs": self.runs,
            "errors": self.errors,
            "cost_micro_usd_total": self.cost_micro_usd_total,
            "cost_per_run_mean": self.cost_per_run_mean,
            "cost_per_run_p50": self.cost_per_run_p50,
            "latency_p50_ms": self.latency_p50_ms,
            "latency_p95_ms": self.latency_p95_ms,
            "human_approval_rate": self.human_approval_rate,
            "rejection_rate": self.rejection_rate,
            "max_day_cost_micro_usd": self.max_day_cost_micro_usd,
            "budget_burn_ratio": self.budget_burn_ratio,
            "alerts": [alert.to_dict() for alert in self.alerts],
        }


@dataclass
class Board:
    organization: str
    rollups: list[AgentRollup]
    daily_cost_micro_usd: dict[str, int]
    unknown_agents: list[str]

    @property
    def alerts(self) -> list[Alert]:
        found: list[Alert] = []
        for rollup in self.rollups:
            found.extend(rollup.alerts)
        return found

    def to_dict(self) -> dict[str, object]:
        return {
            "organization": self.organization,
            "label": "simulated",
            "rollups": [rollup.to_dict() for rollup in self.rollups],
            "daily_cost_micro_usd": self.daily_cost_micro_usd,
            "unknown_agents": self.unknown_agents,
            "alert_count": len(self.alerts),
        }


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def aggregate(inventory: Inventory, events: tuple[TraceEvent, ...]) -> Board:
    by_agent: dict[str, list[TraceEvent]] = defaultdict(list)
    daily: dict[str, int] = defaultdict(int)
    known = inventory.by_id()
    unknown: set[str] = set()
    for event in events:
        by_agent[event.agent_id].append(event)
        daily[event.ts.date().isoformat()] += event.cost_micro_usd
        if event.agent_id not in known:
            unknown.add(event.agent_id)

    rollups: list[AgentRollup] = []
    for agent in inventory.agents:
        rollups.append(_rollup_agent(agent.id, by_agent.get(agent.id, []), inventory))
    for agent_id in sorted(unknown):
        rollups.append(_rollup_agent(agent_id, by_agent[agent_id], inventory))
    return Board(
        organization=inventory.organization,
        rollups=rollups,
        daily_cost_micro_usd=dict(sorted(daily.items())),
        unknown_agents=sorted(unknown),
    )


def _rollup_agent(agent_id: str, events: list[TraceEvent], inventory: Inventory) -> AgentRollup:
    agent = inventory.by_id().get(agent_id)
    runs = len(events)
    if runs == 0:
        rollup = AgentRollup(
            agent_id=agent_id,
            runs=0,
            errors=0,
            cost_micro_usd_total=0,
            cost_per_run_mean=None,
            cost_per_run_p50=None,
            latency_p50_ms=None,
            latency_p95_ms=None,
            human_approval_rate=None,
            rejection_rate=None,
            max_day_cost_micro_usd=0,
            budget_burn_ratio=None,
        )
        rollup.alerts.append(Alert("no_observations", agent_id, "no trace events in the window"))
        return rollup

    costs = [float(event.cost_micro_usd) for event in events]
    latencies = [float(event.latency_ms) for event in events]
    total = sum(event.cost_micro_usd for event in events)
    approved = sum(1 for event in events if event.approval == "approved")
    rejected = sum(1 for event in events if event.status == "rejected" or event.approval == "rejected")
    errors = sum(1 for event in events if event.status == "error")
    by_day: dict[date, int] = defaultdict(int)
    for event in events:
        by_day[event.ts.date()] += event.cost_micro_usd
    max_day = max(by_day.values()) if by_day else 0
    per_day_cap = agent.budget.per_day_micro_usd if agent else 0
    burn = (max_day / per_day_cap) if agent and per_day_cap else None
    rollup = AgentRollup(
        agent_id=agent_id,
        runs=runs,
        errors=errors,
        cost_micro_usd_total=total,
        cost_per_run_mean=total / runs,
        cost_per_run_p50=percentile(costs, 50),
        latency_p50_ms=percentile(latencies, 50),
        latency_p95_ms=percentile(latencies, 95),
        human_approval_rate=_rate(approved, runs),
        rejection_rate=_rate(rejected, runs),
        max_day_cost_micro_usd=max_day,
        budget_burn_ratio=burn,
    )
    if agent is None:
        rollup.alerts.append(Alert("unknown_agent", agent_id, "traces exist for an agent not in inventory"))
        return rollup
    _apply_threshold_alerts(
        rollup,
        events,
        agent.budget.per_run_micro_usd,
        agent.budget.per_day_micro_usd,
        by_day,
        agent.slo.p95_latency_ms,
        agent.slo.cost_per_run_micro_usd,
    )
    return rollup


def _apply_threshold_alerts(
    rollup: AgentRollup,
    events: list[TraceEvent],
    per_run_cap: int,
    per_day_cap: int,
    by_day: dict[date, int],
    p95_slo: int,
    cost_slo: int,
) -> None:
    over_run = [event for event in events if event.cost_micro_usd > per_run_cap]
    if over_run:
        rollup.alerts.append(
            Alert(
                "per_run_cap_exceeded",
                rollup.agent_id,
                f"{len(over_run)} runs over the per-run cap of {per_run_cap} micro-USD",
            )
        )
    over_days = [day for day, cost in sorted(by_day.items()) if cost > per_day_cap]
    if over_days:
        rollup.alerts.append(
            Alert(
                "per_day_cap_exceeded",
                rollup.agent_id,
                "daily cost exceeded the per-day cap on " + ", ".join(day.isoformat() for day in over_days),
            )
        )
    if rollup.latency_p95_ms is not None and rollup.latency_p95_ms > p95_slo:
        rollup.alerts.append(
            Alert(
                "p95_latency_slo_breach",
                rollup.agent_id,
                f"p95 latency {rollup.latency_p95_ms:.1f} ms > SLO {p95_slo} ms",
            )
        )
    if rollup.cost_per_run_mean is not None and rollup.cost_per_run_mean > cost_slo:
        rollup.alerts.append(
            Alert(
                "cost_per_run_slo_breach",
                rollup.agent_id,
                f"mean cost/run {rollup.cost_per_run_mean:.1f} micro-USD > SLO {cost_slo}",
            )
        )
