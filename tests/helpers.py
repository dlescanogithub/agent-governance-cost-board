from __future__ import annotations

from datetime import date

from governance_board.inventory import Agent, ApprovalGate, Budget, Inventory, Slo


def gate(**kwargs: object) -> ApprovalGate:
    data: dict[str, object] = {
        "id": "gate",
        "kind": "none",
        "required": False,
        "enforced_at": "not_applicable",
        "effects_covered": (),
    }
    data.update(kwargs)
    effects = data["effects_covered"]
    assert isinstance(effects, tuple)
    return ApprovalGate(
        id=str(data["id"]),
        kind=str(data["kind"]),
        required=bool(data["required"]),
        enforced_at=str(data["enforced_at"]),
        effects_covered=effects,
    )


def agent(**kwargs: object) -> Agent:
    data: dict[str, object] = {
        "id": "kb-search",
        "name": "Handbook search",
        "owner": "knowledge-steward",
        "backup_owner": "knowledge-backup",
        "version": "1.1.0",
        "model": "sim-small",
        "provider": "sim",
        "purpose": "Read the handbook",
        "data_classes": ("internal_ops",),
        "risk_tier": "low",
        "approval_gates": (gate(),),
        "budget": Budget(50_000, 2_000_000),
        "slo": Slo(2500, 40_000),
        "status": "active",
        "kill_switch": "disengaged",
        "last_review": date(2026, 9, 1),
        "eval_evidence": ("evals/evidence/fleet.md#kb-search",),
        "prompt_id": "kb-search",
        "prompt_version": "1.1.0",
    }
    data.update(kwargs)
    return Agent(
        id=str(data["id"]),
        name=str(data["name"]),
        owner=str(data["owner"]),
        backup_owner=str(data["backup_owner"]),
        version=str(data["version"]),
        model=str(data["model"]),
        provider=str(data["provider"]),
        purpose=str(data["purpose"]),
        data_classes=data["data_classes"],  # type: ignore[arg-type]
        risk_tier=str(data["risk_tier"]),
        approval_gates=data["approval_gates"],  # type: ignore[arg-type]
        budget=data["budget"],  # type: ignore[arg-type]
        slo=data["slo"],  # type: ignore[arg-type]
        status=str(data["status"]),
        kill_switch=str(data["kill_switch"]),
        last_review=data["last_review"],  # type: ignore[arg-type]
        eval_evidence=data["eval_evidence"],  # type: ignore[arg-type]
        prompt_id=str(data["prompt_id"]),
        prompt_version=str(data["prompt_version"]),
    )


def inventory(*agents: Agent, max_age: int = 90) -> Inventory:
    return Inventory(
        schema_version=1,
        review_max_age_days=max_age,
        organization="Harborline Cooperative",
        agents=agents,
        source="test",
    )
