from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from governance_board.aggregate import aggregate
from governance_board.cli import main
from governance_board.evalkit.properties import run_property_checks
from governance_board.ingest import load_runtime_evals, loads_runtime_evals
from governance_board.inventory import load_inventory
from governance_board.report import render_html
from governance_board.trace import TraceError

ROOT = Path(".")
CLOCK = datetime(2026, 10, 17, 12, 0, 0)


def test_runtime_evals_sample_is_labelled_and_loads() -> None:
    path = ROOT / "traces" / "samples" / "runtime_evals_sample.jsonl"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# SAMPLE:")
    assert "Not a capture" in text
    events = load_runtime_evals(path, default_ts=CLOCK)
    assert [event.agent_id for event in events] == ["kb-search", "safety-checklist", "meeting-notes"]
    assert events[2].status == "ok"
    assert events[0].run_id == "sample-run-1"


def test_runtime_evals_validation() -> None:
    with pytest.raises(TraceError):
        loads_runtime_evals('{"run_id": "x"}\n', default_ts=CLOCK)
    with pytest.raises(TraceError):
        loads_runtime_evals(
            '{"run_id":"r","step":"kb-search","tokens_in":1,"tokens_out":1,'
            '"cost_micro_usd":-1,"latency_ms":1,"outcome":"ok"}\n',
            default_ts=CLOCK,
        )
    with pytest.raises(TraceError):
        loads_runtime_evals(
            '{"run_id":"r","step":"kb-search","tokens_in":1,"tokens_out":1,'
            '"cost_micro_usd":1,"latency_ms":1,"outcome":"ok","extra":1}\n',
            default_ts=CLOCK,
        )
    with pytest.raises(TraceError):
        loads_runtime_evals("# only a comment\n", default_ts=CLOCK)
    missing_clock = loads_runtime_evals(
        '{"run_id":"r","step":"kb-search","tokens_in":1,"tokens_out":1,'
        '"cost_micro_usd":1,"latency_ms":1,"outcome":"rejected"}\n',
        default_ts=CLOCK,
    )
    assert missing_clock[0].ts == CLOCK
    assert missing_clock[0].status == "rejected"
    assert missing_clock[0].version == "unknown"


def test_property_checks_hold() -> None:
    assert run_property_checks() == []


def test_ingested_board_names_its_source(tmp_path: Path) -> None:
    out = tmp_path / "ingested"
    code = main(
        [
            "report",
            "--inventory",
            "inventory/fleet.yaml",
            "--traces",
            "traces/samples/runtime_evals_sample.jsonl",
            "--out",
            str(out),
            "--generated-on",
            "2026-10-17",
            "--source",
            "ingested-runtime-evals",
        ]
    )
    assert code == 0
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "Source: ingested runtime-evals JSONL" in html
    assert "not a measurement" in html
    assert "simulated generator" not in html
    page = render_html(
        aggregate(
            load_inventory(ROOT / "inventory" / "fleet.yaml"),
            load_runtime_evals(ROOT / "traces" / "samples" / "runtime_evals_sample.jsonl", default_ts=CLOCK),
        ),
        generated_on="2026-10-17",
        source="ingested-runtime-evals",
    )
    assert "ingested runtime-evals JSONL" in page
