"""Versioned prompt registry stored as YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class RegistryError(ValueError):
    pass


def load_registry(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict) or not isinstance(loaded.get("prompts"), list):
        raise RegistryError("registry must be a mapping with a prompts list")
    return loaded


def current_versions(registry: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    prompts = registry.get("prompts")
    if not isinstance(prompts, list):
        raise RegistryError("prompts must be a list")
    for entry in prompts:
        if not isinstance(entry, dict):
            raise RegistryError("prompt entry must be a mapping")
        agent_id = entry.get("agent_id")
        versions = entry.get("versions")
        if not isinstance(agent_id, str) or not isinstance(versions, list):
            raise RegistryError("prompt entry needs agent_id and versions")
        current = [item for item in versions if isinstance(item, dict) and item.get("status") == "current"]
        if len(current) != 1:
            raise RegistryError(f"{agent_id} must have exactly one current version")
        version = current[0].get("version")
        if not isinstance(version, str):
            raise RegistryError(f"{agent_id} current version is missing")
        found[agent_id] = version
    return found


def rollback(registry: dict[str, Any], agent_id: str, to_version: str) -> dict[str, Any]:
    prompts = registry.get("prompts")
    if not isinstance(prompts, list):
        raise RegistryError("prompts must be a list")
    matched = False
    for entry in prompts:
        if not isinstance(entry, dict) or entry.get("agent_id") != agent_id:
            continue
        matched = True
        versions = entry.get("versions")
        if not isinstance(versions, list):
            raise RegistryError("versions must be a list")
        known = [item for item in versions if isinstance(item, dict) and item.get("version") == to_version]
        if len(known) != 1:
            raise RegistryError(f"{agent_id} has no version {to_version}")
        for item in versions:
            if isinstance(item, dict) and item.get("status") == "current":
                item["status"] = "previous"
        known[0]["status"] = "current"
    if not matched:
        raise RegistryError(f"unknown agent_id {agent_id}")
    return registry


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
