"""Load and schema-validate an agent inventory YAML file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


class InventorySchemaError(ValueError):
    def __init__(self, messages: list[str]) -> None:
        super().__init__("; ".join(messages))
        self.messages = messages


@dataclass(frozen=True)
class ApprovalGate:
    id: str
    kind: str
    required: bool
    enforced_at: str
    effects_covered: tuple[str, ...]


@dataclass(frozen=True)
class Budget:
    per_run_micro_usd: int
    per_day_micro_usd: int


@dataclass(frozen=True)
class Slo:
    p95_latency_ms: int
    cost_per_run_micro_usd: int


@dataclass(frozen=True)
class Agent:
    id: str
    name: str
    owner: str
    backup_owner: str
    version: str
    model: str
    provider: str
    purpose: str
    data_classes: tuple[str, ...]
    risk_tier: str
    approval_gates: tuple[ApprovalGate, ...]
    budget: Budget
    slo: Slo
    status: str
    kill_switch: str
    last_review: date
    eval_evidence: tuple[str, ...]
    prompt_id: str
    prompt_version: str


@dataclass(frozen=True)
class Inventory:
    schema_version: int
    review_max_age_days: int
    organization: str
    agents: tuple[Agent, ...]
    source: str

    def by_id(self) -> dict[str, Agent]:
        return {agent.id: agent for agent in self.agents}


def schema_document() -> dict[str, Any]:
    text = files("governance_board.schema").joinpath("inventory.schema.json").read_text(encoding="utf-8")
    loaded: dict[str, Any] = json.loads(text)
    return loaded


def validator() -> Draft202012Validator:
    return Draft202012Validator(schema_document())


def format_schema_error(error: ValidationError) -> str:
    path = getattr(error, "json_path", None) or "$"
    return f"{path}: {error.message}"


def _coerce(value: Any) -> Any:
    """Turn YAML dates into the strings the JSON Schema expects."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _coerce(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_coerce(item) for item in value]
    return value


def load_raw(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return _coerce(yaml.safe_load(text))


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_agent(raw: dict[str, Any]) -> Agent:
    gates = tuple(
        ApprovalGate(
            id=str(gate["id"]),
            kind=str(gate["kind"]),
            required=bool(gate["required"]),
            enforced_at=str(gate["enforced_at"]),
            effects_covered=tuple(str(item) for item in gate["effects_covered"]),
        )
        for gate in raw["approval_gates"]
    )
    budget = Budget(
        per_run_micro_usd=int(raw["budget"]["per_run_micro_usd"]),
        per_day_micro_usd=int(raw["budget"]["per_day_micro_usd"]),
    )
    slo = Slo(
        p95_latency_ms=int(raw["slo"]["p95_latency_ms"]),
        cost_per_run_micro_usd=int(raw["slo"]["cost_per_run_micro_usd"]),
    )
    return Agent(
        id=str(raw["id"]),
        name=str(raw["name"]),
        owner=str(raw["owner"]),
        backup_owner=str(raw["backup_owner"]),
        version=str(raw["version"]),
        model=str(raw["model"]),
        provider=str(raw["provider"]),
        purpose=str(raw["purpose"]),
        data_classes=tuple(str(item) for item in raw["data_classes"]),
        risk_tier=str(raw["risk_tier"]),
        approval_gates=gates,
        budget=budget,
        slo=slo,
        status=str(raw["status"]),
        kill_switch=str(raw["kill_switch"]),
        last_review=_parse_date(str(raw["last_review"])),
        eval_evidence=tuple(str(item) for item in raw["eval_evidence"]),
        prompt_id=str(raw["prompt_id"]),
        prompt_version=str(raw["prompt_version"]),
    )


def parse_inventory(raw: Any, *, source: str) -> Inventory:
    errors = [format_schema_error(error) for error in validator().iter_errors(raw)]
    if errors or not isinstance(raw, dict):
        if not isinstance(raw, dict):
            errors = ["$: inventory must be a mapping", *errors]
        raise InventorySchemaError(sorted(errors))
    agents = tuple(_parse_agent(item) for item in raw["agents"])
    return Inventory(
        schema_version=int(raw["schema_version"]),
        review_max_age_days=int(raw["review_max_age_days"]),
        organization=str(raw["organization"]),
        agents=agents,
        source=source,
    )


def load_inventory(path: Path) -> Inventory:
    return parse_inventory(load_raw(path), source=str(path))
