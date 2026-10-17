from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from tests.helpers import agent, inventory

from governance_board.aggregate import aggregate
from governance_board.effects import EXTERNAL_EFFECTS, HARMFUL_EFFECTS
from governance_board.evalkit.invariants import check_events
from governance_board.generate import ProfileError, generate, load_profile
from governance_board.inventory import load_inventory
from governance_board.policy import check_policy
from governance_board.prompts import current_versions, load_registry
from governance_board.report import alert_codes, render_html, render_markdown, write_report
from governance_board.stats import percentile
from governance_board.trace import (
    TraceError,
    dump_jsonl,
    iter_events,
    load_jsonl,
    loads_jsonl,
    parse_event,
)

ROOT = Path(".")


def test_alternate_trace_shape() -> None:
    events = load_jsonl(ROOT / "traces" / "runtime_evals_sample.jsonl")
    assert events[0].run_id == "alt-1"
    assert events[0].status == "ok"
    assert events[0].tokens_in == 80
    roundtrip = loads_jsonl(dump_jsonl(events))
    assert roundtrip[0].cost_micro_usd == 900
    assert list(iter_events(ROOT / "traces" / "runtime_evals_sample.jsonl"))[0].agent_id == "kb-search"


def test_trace_errors() -> None:
    with pytest.raises(TraceError):
        loads_jsonl("{")
    with pytest.raises(TraceError):
        loads_jsonl("[]\n")
    with pytest.raises(TraceError):
        parse_event(
            {
                "run_id": "x",
                "agent_id": "a",
                "version": "1",
                "ts": "yesterday",
                "status": "ok",
                "tokens_in": 1,
                "tokens_out": 1,
                "cost_micro_usd": 1,
                "latency_ms": 1,
                "approval": "none",
                "effects": [],
            }
        )
    with pytest.raises(TraceError):
        parse_event(
            {
                "run_id": "x",
                "agent_id": "a",
                "version": "1",
                "ts": "2026-10-01T00:00:00Z",
                "status": "nope",
                "tokens_in": 1,
                "tokens_out": 1,
                "cost_micro_usd": 1,
                "latency_ms": 1,
                "approval": "none",
                "effects": [],
            }
        )
    with pytest.raises(TraceError):
        parse_event(
            {
                "run_id": "x",
                "agent_id": "a",
                "version": "1",
                "ts": "2026-10-01T00:00:00Z",
                "status": "ok",
                "tokens_in": True,
                "tokens_out": 1,
                "cost_micro_usd": 1,
                "latency_ms": 1,
                "approval": "none",
                "effects": [],
            }
        )
    with pytest.raises(TraceError):
        parse_event(
            {
                "run_id": "x",
                "agent_id": "a",
                "version": "1",
                "ts": "2026-10-01T00:00:00Z",
                "status": "ok",
                "tokens_in": 1,
                "tokens_out": 1,
                "cost_micro_usd": 1,
                "latency_ms": 1,
                "approval": "maybe",
                "effects": "nope",
            }
        )
    assert loads_jsonl("\n") == ()
    with pytest.raises(TraceError):
        parse_event({"outcome": "failed"})


def test_generator_is_deterministic_and_safe() -> None:
    inv = load_inventory(ROOT / "inventory" / "fleet.yaml")
    profile = load_profile(ROOT / "traces" / "generation.yaml")
    first, meta = generate(inv, profile)
    second, _ = generate(inv, profile)
    assert dump_jsonl(first) == dump_jsonl(second)
    assert meta.event_count == 12 * 14 * 12
    assert meta.label == "simulated"
    harmful = [event for event in first if any(effect in HARMFUL_EFFECTS for effect in event.effects)]
    assert harmful == []
    unapproved = [
        event
        for event in first
        if any(effect in EXTERNAL_EFFECTS for effect in event.effects) and event.approval != "approved"
    ]
    assert unapproved == []
    prompts = current_versions(load_registry(ROOT / "prompts" / "registry.yaml"))
    assert check_policy(inv, today=date(2026, 10, 17), prompts=prompts).ok
    board = aggregate(inv, first)
    codes = set(alert_codes(board.alerts))
    assert "per_day_cap_exceeded" in codes
    assert "per_run_cap_exceeded" in codes
    assert "p95_latency_slo_breach" in codes
    refund = next(row for row in board.rollups if row.agent_id == "refund-advisor")
    bulletin = next(row for row in board.rollups if row.agent_id == "bulletin-draft")
    assert refund.max_day_cost_micro_usd > inv.by_id()["refund-advisor"].budget.per_day_micro_usd
    assert bulletin.latency_p95_ms is not None
    assert bulletin.latency_p95_ms > inv.by_id()["bulletin-draft"].slo.p95_latency_ms
    assert (
        percentile([float(event.latency_ms) for event in first if event.agent_id == "bulletin-draft"], 95)
        == bulletin.latency_p95_ms
    )
    committed = (ROOT / "traces" / "fleet.jsonl").read_text(encoding="utf-8")
    assert dump_jsonl(first) == committed


def test_profile_errors(tmp_path: Path) -> None:
    inv = inventory(agent())
    with pytest.raises(ProfileError):
        generate(inv, {"seed": 1})
    not_a_map = tmp_path / "bad.yaml"
    not_a_map.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ProfileError):
        load_profile(not_a_map)
    with pytest.raises(ProfileError):
        generate(
            inv,
            {
                "seed": 1,
                "days": 1,
                "runs_per_agent_per_day": 1,
                "start_date": "2026-10-01",
                "pricing": {"input_micro_usd_per_token": 1, "output_micro_usd_per_token": 1},
                "profiles": {},
            },
        )
    bad = {
        "seed": 1,
        "days": 1,
        "runs_per_agent_per_day": 1,
        "start_date": "2026-10-01",
        "pricing": {"input_micro_usd_per_token": 1, "output_micro_usd_per_token": 1},
        "profiles": {
            "kb-search": {
                "tokens_in_median": 10,
                "tokens_out_median": 4,
                "latency_median_ms": 10,
                "sigma": 0.1,
                "internal_effect": "transfer_funds",
            }
        },
    }
    with pytest.raises(ProfileError):
        generate(inv, bad)
    bad["profiles"]["kb-search"]["internal_effect"] = "draft_note"  # type: ignore[index]
    bad["profiles"]["kb-search"]["external_effect"] = "not-external"  # type: ignore[index]
    with pytest.raises(ProfileError):
        generate(inv, bad)


def test_unknown_agent_and_empty_window() -> None:
    inv = inventory(agent())
    board = aggregate(inv, ())
    assert board.rollups[0].alerts[0].code == "no_observations"
    event = parse_event(
        {
            "run_id": "u1",
            "agent_id": "not-in-inventory",
            "version": "1",
            "ts": "2026-10-01T00:00:00Z",
            "status": "error",
            "tokens_in": 1,
            "tokens_out": 1,
            "cost_micro_usd": 10,
            "latency_ms": 5,
            "approval": "none",
            "effects": [],
        }
    )
    board = aggregate(inv, (event,))
    assert "not-in-inventory" in board.unknown_agents
    assert any(alert.code == "unknown_agent" for alert in board.alerts)


def test_report_is_local(tmp_path: Path) -> None:
    inv = load_inventory(ROOT / "inventory" / "fleet.yaml")
    events, meta = generate(inv, load_profile(ROOT / "traces" / "generation.yaml"))
    board = aggregate(inv, events)
    html = render_html(board, generated_on="2026-10-17")
    assert "https://" not in html
    assert "http://" not in html
    assert "<script src" not in html
    assert "Simulated data" in html
    markdown = render_markdown(board, generated_on="2026-10-17")
    assert "refund-advisor" in markdown
    assert "simulated" in markdown
    write_report(board, tmp_path, generated_on="2026-10-17", extra={"meta": meta.to_dict()})
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "summary.json").exists()
    breaches = check_events(events[:3], caps={}, default_cap=10**12)
    assert breaches == []
