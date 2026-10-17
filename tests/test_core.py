from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

import pytest
from tests.helpers import agent, gate, inventory

from governance_board.config import ConfigError, load_settings
from governance_board.effects import HARMFUL_EFFECTS
from governance_board.inventory import (
    Budget,
    InventorySchemaError,
    Slo,
    load_inventory,
    parse_inventory,
)
from governance_board.logging_setup import JsonFormatter, log_event, setup_logging
from governance_board.policy import check_policy
from governance_board.retry import RetryError, call_with_retry
from governance_board.stats import percentile


def test_settings_defaults() -> None:
    settings = load_settings({})
    assert settings.today == date(2026, 10, 17)
    assert settings.offline
    assert settings.provider == "fake"


def test_settings_rejects_bad_values() -> None:
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_REAL_PROVIDER_ENABLED": "yes"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_TODAY": "17-10-2026"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_MAX_ATTEMPTS": "0"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_MAX_ATTEMPTS": "x"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_BACKOFF_CAP_S": "-1"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_BACKOFF_BASE_S": "nope"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_LOG_LEVEL": "LOUD"})
    with pytest.raises(ConfigError):
        load_settings({"GOVERNANCE_REVIEW_MAX_AGE_DAYS": "0"})


def test_settings_real_flag_is_explicit() -> None:
    settings = load_settings(
        {
            "GOVERNANCE_REAL_PROVIDER_ENABLED": "1",
            "GOVERNANCE_PROVIDER": "real",
            "GOVERNANCE_REAL_PROVIDER_URL": "http://127.0.0.1:9",
        }
    )
    assert settings.real_provider_enabled
    assert not settings.offline


def test_json_logging(capsys: pytest.CaptureFixture[str]) -> None:
    setup_logging("INFO")
    logger = logging.getLogger("governance_board.test")
    log_event(logger, logging.INFO, "hello", event="unit")
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logger.exception("failed")
    err = capsys.readouterr().err.strip().splitlines()
    first = json.loads(err[0])
    assert first["message"] == "hello"
    assert first["event"] == "unit"
    second = json.loads(err[1])
    assert "boom" in second["exc_info"]
    assert JsonFormatter().format(logging.LogRecord("n", logging.INFO, __file__, 1, "m", None, None))


def test_retry_caps_and_recovers() -> None:
    sleeps: list[float] = []

    def always_fail() -> object:
        raise OSError("down")

    with pytest.raises(RetryError) as caught:
        call_with_retry(
            always_fail,
            max_attempts=4,
            base_delay_s=10,
            backoff_cap_s=2,
            sleep=sleeps.append,
        )
    assert caught.value.attempts == 4
    assert sleeps == [2, 2, 2]

    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("later")
        return "ok"

    assert call_with_retry(flaky, max_attempts=3, base_delay_s=0, backoff_cap_s=0, sleep=lambda _d: None) == "ok"
    with pytest.raises(ValueError):
        call_with_retry(always_fail, max_attempts=0, base_delay_s=0, backoff_cap_s=0)
    with pytest.raises(ValueError):
        call_with_retry(always_fail, max_attempts=1, base_delay_s=-1, backoff_cap_s=0)

    def not_retryable() -> object:
        raise RuntimeError("no")

    with pytest.raises(RuntimeError):
        call_with_retry(not_retryable, max_attempts=2, base_delay_s=0, backoff_cap_s=0)


def test_percentile() -> None:
    assert percentile([10, 20, 30, 40], 50) == 25
    assert percentile([5], 95) == 5
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile([1], 101)


def test_fleet_inventory_and_policy() -> None:
    loaded = load_inventory(Path("inventory/fleet.yaml"))
    assert len(loaded.agents) == 12
    assert loaded.by_id()["refund-advisor"].risk_tier == "high"
    report = check_policy(
        loaded,
        today=date(2026, 10, 17),
        prompts={"intake-triage": "1.1.0", **{item.id: "1.1.0" for item in loaded.agents}},
    )
    assert report.ok


def test_policy_rules_fire() -> None:
    human = gate(
        id="human",
        kind="human",
        required=True,
        enforced_at="human_queue",
        effects_covered=("write_ledger_note",),
    )
    cases = inventory(
        agent(id="ghost", owner=""),
        agent(id="stale", last_review=date(2025, 1, 1)),
        agent(id="future", last_review=date(2026, 12, 1)),
        agent(
            id="high", risk_tier="high", backup_owner="", eval_evidence=("e",), data_classes=("financial_instruction",)
        ),
        agent(
            id="same-backup",
            risk_tier="high",
            owner="finance-ops",
            backup_owner="finance-ops",
            approval_gates=(human,),
            eval_evidence=("e",),
            data_classes=("financial_instruction",),
        ),
        agent(id="dup"),
        agent(id="dup"),
        agent(id="noclass", risk_tier="medium", data_classes=(), eval_evidence=()),
        agent(id="paid", provider="external-api"),
        agent(id="caps", budget=Budget(9, 1)),
        agent(id="slo", budget=Budget(10, 20), slo=Slo(100, 50)),
        agent(id="killed", kill_switch="engaged", status="active"),
        agent(id="missing-prompt", prompt_id="nope"),
        agent(id="old-prompt", prompt_id="kb-search", prompt_version="0.0.1"),
    )
    report = check_policy(cases, today=date(2026, 10, 17), prompts={"kb-search": "1.1.0"})
    rules = {item.rule for item in report.violations}
    assert {
        "owner_required",
        "review_fresh",
        "high_risk_human_gate",
        "high_risk_backup_owner",
        "unique_id",
        "tier_controls",
        "provider_allowlist",
        "cap_consistency",
        "kill_switch_status",
        "prompt_registered",
        "prompt_version_current",
    } <= rules
    assert not report.ok


def test_schema_errors() -> None:
    with pytest.raises(InventorySchemaError):
        parse_inventory(["nope"], source="mem")
    with pytest.raises(InventorySchemaError):
        parse_inventory({"schema_version": 1}, source="mem")


def test_harmful_set_is_closed() -> None:
    assert "transfer_funds" in HARMFUL_EFFECTS
