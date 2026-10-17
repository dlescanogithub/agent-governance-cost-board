"""Seeded synthetic trace generator. No network. Numbers are simulated."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from governance_board.effects import EXTERNAL_EFFECTS, HARMFUL_EFFECTS
from governance_board.inventory import Inventory
from governance_board.trace import TraceEvent


class ProfileError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationMeta:
    seed: int
    start_date: str
    days: int
    runs_per_agent_per_day: int
    input_micro_usd_per_token: int
    output_micro_usd_per_token: int
    event_count: int
    label: str = "simulated"

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "start_date": self.start_date,
            "days": self.days,
            "runs_per_agent_per_day": self.runs_per_agent_per_day,
            "input_micro_usd_per_token": self.input_micro_usd_per_token,
            "output_micro_usd_per_token": self.output_micro_usd_per_token,
            "event_count": self.event_count,
            "label": self.label,
            "price_note": "simulated illustrative rate, not a vendor price [EST]",
        }


def load_profile(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ProfileError("generation profile must be a mapping")
    return loaded


def _lognormal(rng: random.Random, median: float, sigma: float) -> float:
    return math.exp(rng.gauss(math.log(median), sigma))


def _as_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ProfileError(f"{name} must be an integer")
    return value


def _as_float(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProfileError(f"{name} must be a number")
    return float(value)


def generate(inventory: Inventory, profile: dict[str, Any]) -> tuple[tuple[TraceEvent, ...], GenerationMeta]:
    seed = _as_int(profile.get("seed"), "seed")
    days = _as_int(profile.get("days"), "days")
    runs_per_day = _as_int(profile.get("runs_per_agent_per_day"), "runs_per_agent_per_day")
    start_raw = profile.get("start_date")
    if not isinstance(start_raw, str):
        raise ProfileError("start_date must be a string")
    start = datetime.strptime(start_raw, "%Y-%m-%d").date()
    pricing = profile.get("pricing")
    if not isinstance(pricing, dict):
        raise ProfileError("pricing must be a mapping")
    in_rate = _as_int(pricing.get("input_micro_usd_per_token"), "input_micro_usd_per_token")
    out_rate = _as_int(pricing.get("output_micro_usd_per_token"), "output_micro_usd_per_token")
    error_rate = _as_float(profile.get("error_rate", 0.02), "error_rate")
    profiles = profile.get("profiles")
    if not isinstance(profiles, dict):
        raise ProfileError("profiles must be a mapping")
    missing = [agent.id for agent in inventory.agents if agent.id not in profiles]
    if missing:
        raise ProfileError("missing profiles for " + ", ".join(missing))

    rng = random.Random(seed)
    events: list[TraceEvent] = []
    for agent in inventory.agents:
        spec = profiles[agent.id]
        if not isinstance(spec, dict):
            raise ProfileError(f"profile for {agent.id} must be a mapping")
        events.extend(
            _events_for_agent(
                rng,
                agent_id=agent.id,
                version=agent.version,
                spec=spec,
                start=start,
                days=days,
                runs_per_day=runs_per_day,
                in_rate=in_rate,
                out_rate=out_rate,
                error_rate=error_rate,
            )
        )
    meta = GenerationMeta(
        seed=seed,
        start_date=start_raw,
        days=days,
        runs_per_agent_per_day=runs_per_day,
        input_micro_usd_per_token=in_rate,
        output_micro_usd_per_token=out_rate,
        event_count=len(events),
    )
    return tuple(events), meta


def _events_for_agent(
    rng: random.Random,
    *,
    agent_id: str,
    version: str,
    spec: dict[str, Any],
    start: date,
    days: int,
    runs_per_day: int,
    in_rate: int,
    out_rate: int,
    error_rate: float,
) -> list[TraceEvent]:
    tokens_in_median = _as_float(spec.get("tokens_in_median"), "tokens_in_median")
    tokens_out_median = _as_float(spec.get("tokens_out_median"), "tokens_out_median")
    latency_median = _as_float(spec.get("latency_median_ms"), "latency_median_ms")
    sigma = _as_float(spec.get("sigma"), "sigma")
    internal = spec.get("internal_effect")
    external = spec.get("external_effect")
    external_p = _as_float(spec.get("external_probability", 0), "external_probability")
    if not isinstance(internal, str) or not internal:
        raise ProfileError(f"{agent_id} needs internal_effect")
    if internal in HARMFUL_EFFECTS or (isinstance(external, str) and external in HARMFUL_EFFECTS):
        raise ProfileError(f"{agent_id} profile uses a harmful effect")
    if isinstance(external, str) and external not in EXTERNAL_EFFECTS:
        raise ProfileError(f"{agent_id} external_effect {external} is not an external effect")
    spike = spec.get("spike")
    spike_date: date | None = None
    spike_mult = 1.0
    if isinstance(spike, dict):
        raw_day = spike.get("date")
        if not isinstance(raw_day, str):
            raise ProfileError(f"{agent_id} spike.date must be a string")
        spike_date = datetime.strptime(raw_day, "%Y-%m-%d").date()
        spike_mult = _as_float(spike.get("token_multiplier"), "token_multiplier")

    events: list[TraceEvent] = []
    for day_index in range(days):
        day = start + timedelta(days=day_index)
        for run_i in range(runs_per_day):
            tokens_in = max(1, int(round(_lognormal(rng, tokens_in_median, sigma))))
            tokens_out = max(1, int(round(_lognormal(rng, tokens_out_median, sigma))))
            latency = max(1, int(round(_lognormal(rng, latency_median, sigma))))
            roll_error = rng.random()
            roll_external = rng.random()
            roll_approval = rng.random()
            hour = 8 + int(rng.random() * 10)
            minute = int(rng.random() * 60)
            second = int(rng.random() * 60)
            if spike_date is not None and day == spike_date:
                tokens_in = max(1, int(round(tokens_in * spike_mult)))
                tokens_out = max(1, int(round(tokens_out * spike_mult)))
            cost = tokens_in * in_rate + tokens_out * out_rate
            status = "ok"
            approval = "none"
            effects: list[str] = [internal]
            if roll_error < error_rate:
                status = "error"
                approval = "none"
                effects = []
            elif isinstance(external, str) and external_p > 0 and roll_external < external_p:
                if roll_approval < 0.8:
                    approval = "approved"
                    effects = [internal, external]
                else:
                    status = "rejected"
                    approval = "rejected"
                    effects = []
            ts = datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=UTC)
            events.append(
                TraceEvent(
                    run_id=f"{agent_id}-{day.isoformat()}-{run_i:02d}",
                    agent_id=agent_id,
                    version=version,
                    ts=ts,
                    status=status,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_micro_usd=cost,
                    latency_ms=latency,
                    approval=approval,
                    effects=tuple(effects),
                )
            )
    return events
