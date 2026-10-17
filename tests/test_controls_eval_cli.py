from __future__ import annotations

import json
from pathlib import Path

import pytest

from governance_board.cli import main
from governance_board.config import load_settings
from governance_board.controls import (
    ControlError,
    disengage_kill_switch,
    engage_kill_switch,
    rollback_agent,
)
from governance_board.evalkit.runner import EvalError, run_path
from governance_board.prompts import RegistryError, current_versions, load_registry, rollback
from governance_board.providers import CassetteMiss, ProviderDisabled
from governance_board.providers.cassette import CassetteProvider
from governance_board.providers.fake import FakeProvider
from governance_board.providers.real import RealProvider, urllib_transport

ROOT = Path(".")


def test_registry_rollback_and_errors(tmp_path: Path) -> None:
    registry = load_registry(ROOT / "prompts" / "registry.yaml")
    assert current_versions(registry)["refund-advisor"] == "1.1.0"
    updated = rollback(registry, "refund-advisor", "1.0.0")
    assert current_versions(updated)["refund-advisor"] == "1.0.0"
    with pytest.raises(RegistryError):
        rollback(updated, "missing", "1.0.0")
    with pytest.raises(RegistryError):
        rollback(updated, "refund-advisor", "9.9.9")
    with pytest.raises(RegistryError):
        load_registry(ROOT / "inventory" / "fleet.yaml")
    broken = {"prompts": [{"agent_id": "a", "versions": [{"version": "1", "status": "previous"}]}]}
    with pytest.raises(RegistryError):
        current_versions(broken)
    inventory = {
        "agents": [{"id": "refund-advisor", "prompt_version": "1.1.0", "version": "1.1.0", "model": "sim-balanced"}]
    }
    _, inv = rollback_agent(load_registry(ROOT / "prompts" / "registry.yaml"), inventory, "refund-advisor", "1.0.0")
    assert inv is not None
    assert inv["agents"][0]["model"] == "sim-small"
    assert inv["agents"][0]["prompt_version"] == "1.0.0"
    with pytest.raises(ControlError):
        engage_kill_switch({"agents": []}, "nope")
    killed = engage_kill_switch(
        {"agents": [{"id": "kb-search", "status": "active", "kill_switch": "disengaged"}]}, "kb-search"
    )
    assert killed["agents"][0]["status"] == "disabled"
    back = disengage_kill_switch(killed, "kb-search")
    assert back["agents"][0]["status"] == "active"
    with pytest.raises(ControlError):
        rollback_agent({"prompts": []}, None, "kb-search", "1.0.0")
    with pytest.raises(ControlError):
        rollback_agent(load_registry(ROOT / "prompts" / "registry.yaml"), {"agents": []}, "kb-search", "1.0.0")


def test_providers(tmp_path: Path) -> None:
    fake = FakeProvider().complete("one two three")
    assert fake.provider == "fake"
    assert fake.tokens_in == 3
    key = CassetteProvider.key_for("hello")
    cassette = tmp_path / "cassette.json"
    cassette.write_text(
        json.dumps({"responses": {key: {"text": "from-cassette", "tokens_in": 2, "tokens_out": 3}}}),
        encoding="utf-8",
    )
    assert CassetteProvider(cassette).complete("hello").text == "from-cassette"
    with pytest.raises(CassetteMiss):
        CassetteProvider(cassette).complete("other")
    with pytest.raises(ValueError):
        _write_bad(tmp_path)
    off = RealProvider(enabled=False, url="", max_attempts=2, base_delay_s=0, backoff_cap_s=0)
    with pytest.raises(ProviderDisabled):
        off.complete("hi")
    empty = RealProvider(enabled=True, url="", max_attempts=1, base_delay_s=0, backoff_cap_s=0)
    with pytest.raises(ProviderDisabled):
        empty.complete("hi")

    def transport(url: str, payload: dict[str, object]) -> dict[str, object]:
        assert url == "http://example.invalid"
        assert payload["prompt"] == "hi"
        return {"text": "remote", "tokens_in": 1, "tokens_out": 2}

    live = RealProvider(
        enabled=True,
        url="http://example.invalid",
        max_attempts=2,
        base_delay_s=0,
        backoff_cap_s=0,
        transport=transport,
    )
    assert live.complete("hi").text == "remote"

    calls = {"n": 0}

    def flaky(url: str, payload: dict[str, object]) -> dict[str, object]:
        del url, payload
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("blip")
        return {"text": "retried", "tokens_in": 1, "tokens_out": 1}

    retried = RealProvider(
        enabled=True,
        url="http://example.invalid",
        max_attempts=2,
        base_delay_s=0,
        backoff_cap_s=0,
        transport=flaky,
    )
    assert retried.complete("hi").text == "retried"
    with pytest.raises(OSError):
        RealProvider(
            enabled=True,
            url="http://example.invalid",
            max_attempts=1,
            base_delay_s=0,
            backoff_cap_s=0,
            transport=lambda _u, _p: {"text": 1},
        ).complete("hi")


def _write_bad(tmp_path: Path) -> CassetteProvider:
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    return CassetteProvider(path)


def test_urllib_transport_with_fake_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *args: object) -> bool:
            return False

        def read(self) -> bytes:
            return b'{"text": "body", "tokens_in": 4, "tokens_out": 5}'

    monkeypatch.setattr("governance_board.providers.real.urlopen", lambda *a, **k: _Response())
    parsed = urllib_transport("http://example.invalid/v1", {"prompt": "x"})
    assert parsed["text"] == "body"


def test_eval_gate() -> None:
    settings = load_settings({})
    passed = run_path(ROOT / "evals" / "suite.yaml", settings=settings)
    assert passed.ok
    failed = run_path(ROOT / "evals" / "regression.yaml", settings=settings)
    assert not failed.ok
    names = {item.name for item in failed.breaches}
    assert names == {"no_harmful_effect", "cost_within_cap", "no_unapproved_external_action"}
    with pytest.raises(EvalError):
        run_path(ROOT / "evals" / "suite.yaml", settings=load_settings({"GOVERNANCE_REAL_PROVIDER_ENABLED": "1"}))


def test_cli_happy_and_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(ROOT)
    assert main(["version"]) == 0
    assert (
        main(
            [
                "policy",
                "--inventory",
                "inventory/fleet.yaml",
                "--prompts",
                "prompts/registry.yaml",
                "--today",
                "2026-10-17",
            ]
        )
        == 0
    )
    assert main(["policy", "--inventory", "inventory/violating.yaml", "--today", "2026-10-17", "--json"]) == 1
    assert main(["policy", "--inventory", "missing.yaml"]) == 2
    assert main(["eval", "--suite", "evals/suite.yaml"]) == 0
    assert main(["eval-regression", "--suite", "evals/regression.yaml"]) == 1
    assert main(["secretscan", "--root", "."]) == 0
    out = tmp_path / "traces.jsonl"
    assert (
        main(
            [
                "generate-traces",
                "--inventory",
                "inventory/fleet.yaml",
                "--profile",
                "traces/generation.yaml",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    assert out.exists()
    report_dir = tmp_path / "board"
    assert (
        main(
            [
                "report",
                "--inventory",
                "inventory/fleet.yaml",
                "--traces",
                str(out),
                "--out",
                str(report_dir),
                "--generated-on",
                "2026-10-17",
                "--source",
                "simulated-generator",
            ]
        )
        == 0
    )
    html = (report_dir / "index.html").read_text(encoding="utf-8")
    assert "Source: simulated generator" in html
    assert "not a measurement" in html
    assert (report_dir / "index.html").exists()
    demo_dir = tmp_path / "demo"
    assert main(["demo", "--root", ".", "--out", str(demo_dir), "--today", "2026-10-17"]) == 0
    killed = tmp_path / "killed.yaml"
    assert (
        main(
            [
                "kill-switch",
                "--inventory",
                "inventory/fleet.yaml",
                "--agent-id",
                "refund-advisor",
                "--output",
                str(killed),
            ]
        )
        == 0
    )
    text = killed.read_text(encoding="utf-8")
    assert "engaged" in text
    rolled = tmp_path / "registry.yaml"
    inv_out = tmp_path / "inv.yaml"
    assert (
        main(
            [
                "rollback",
                "--registry",
                "prompts/registry.yaml",
                "--registry-output",
                str(rolled),
                "--agent-id",
                "refund-advisor",
                "--to-version",
                "1.0.0",
                "--inventory",
                "inventory/fleet.yaml",
                "--inventory-output",
                str(inv_out),
            ]
        )
        == 0
    )
    assert "1.0.0" in inv_out.read_text(encoding="utf-8")
    assert (
        main(
            [
                "rollback",
                "--registry",
                "prompts/registry.yaml",
                "--registry-output",
                str(tmp_path / "r2.yaml"),
                "--agent-id",
                "refund-advisor",
                "--to-version",
                "1.0.0",
                "--inventory",
                "inventory/fleet.yaml",
            ]
        )
        == 2
    )
    assert (
        main(
            [
                "kill-switch",
                "--inventory",
                "inventory/fleet.yaml",
                "--agent-id",
                "missing-agent",
                "--output",
                str(tmp_path / "x.yaml"),
            ]
        )
        == 2
    )
    monkeypatch.setenv("GOVERNANCE_REAL_PROVIDER_ENABLED", "1")
    assert main(["eval"]) == 2
    with pytest.raises(SystemExit) as help_exit:
        main(["--help"])
    assert help_exit.value.code == 0
