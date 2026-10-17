"""Kill switch and prompt/model rollback.

These commands rewrite YAML. They do not call a runtime and they do not
preserve comments. Default is to write a new file; pass in_place deliberately.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from governance_board.prompts import RegistryError, rollback


class ControlError(ValueError):
    pass


def kill_switch_blocks(kill_switch: str) -> bool:
    """An engaged kill switch blocks the run. The other fields do not matter."""
    if kill_switch not in {"engaged", "disengaged"}:
        raise ControlError(f"unknown kill_switch {kill_switch!r}")
    return kill_switch == "engaged"


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ControlError(f"{path} is not a mapping")
    return loaded


def engage_kill_switch(inventory: dict[str, Any], agent_id: str) -> dict[str, Any]:
    agents = inventory.get("agents")
    if not isinstance(agents, list):
        raise ControlError("inventory has no agents list")
    for agent in agents:
        if isinstance(agent, dict) and agent.get("id") == agent_id:
            agent["kill_switch"] = "engaged"
            agent["status"] = "disabled"
            return inventory
    raise ControlError(f"unknown agent_id {agent_id}")


def disengage_kill_switch(inventory: dict[str, Any], agent_id: str) -> dict[str, Any]:
    agents = inventory.get("agents")
    if not isinstance(agents, list):
        raise ControlError("inventory has no agents list")
    for agent in agents:
        if isinstance(agent, dict) and agent.get("id") == agent_id:
            agent["kill_switch"] = "disengaged"
            if agent.get("status") == "disabled":
                agent["status"] = "active"
            return inventory
    raise ControlError(f"unknown agent_id {agent_id}")


def rollback_agent(
    registry: dict[str, Any],
    inventory: dict[str, Any] | None,
    agent_id: str,
    to_version: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    try:
        updated = rollback(registry, agent_id, to_version)
    except RegistryError as exc:
        raise ControlError(str(exc)) from exc
    if inventory is None:
        return updated, None
    agents = inventory.get("agents")
    if not isinstance(agents, list):
        raise ControlError("inventory has no agents list")
    found = False
    model = _model_for(updated, agent_id, to_version)
    for agent in agents:
        if isinstance(agent, dict) and agent.get("id") == agent_id:
            agent["prompt_version"] = to_version
            agent["version"] = to_version
            if model is not None:
                agent["model"] = model
            found = True
    if not found:
        raise ControlError(f"agent {agent_id} is not in the inventory")
    return updated, inventory


def _model_for(registry: dict[str, Any], agent_id: str, version: str) -> str | None:
    prompts = registry.get("prompts")
    if not isinstance(prompts, list):
        return None
    for entry in prompts:
        if not isinstance(entry, dict) or entry.get("agent_id") != agent_id:
            continue
        versions = entry.get("versions")
        if not isinstance(versions, list):
            return None
        for item in versions:
            if isinstance(item, dict) and item.get("version") == version:
                model = item.get("model")
                return str(model) if isinstance(model, str) else None
    return None


def write_mapping(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
