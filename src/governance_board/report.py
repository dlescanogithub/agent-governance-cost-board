"""Static HTML and Markdown reports. No CDN, no network, inline CSS and SVG."""

from __future__ import annotations

import html
import json
from pathlib import Path

from governance_board.aggregate import Alert, Board
from governance_board.ingest import SOURCE_GENERATED, SOURCE_INGESTED


def source_banner(source: str) -> str:
    if source == SOURCE_GENERATED:
        return (
            "SIMULATED / illustrative example. Source: simulated generator. "
            "A spike is planted in traces/generation.yaml so a cap alert can be shown. "
            "This page demonstrates policy-as-code, budget caps, the kill switch, and prompt rollback. "
            "It is not a measurement."
        )
    if source == SOURCE_INGESTED:
        return (
            "Source: ingested runtime-evals JSONL. "
            "Figures are the rows in that file. A hand-written sample is still a sample, not a measurement. "
            "This page demonstrates the same board on an ingested file."
        )
    raise ValueError(f"unknown source {source}")


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _usd(micro: float | int | None) -> str:
    if micro is None:
        return "—"
    return f"${micro / 1_000_000:.4f}"


def _num(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def _pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def render_markdown(board: Board, *, generated_on: str, source: str) -> str:
    lines = [
        f"# Cost and governance board — {board.organization}",
        "",
        f"Date label: {generated_on}.",
        "",
        source_banner(source),
        "",
        f"Alerts: **{len(board.alerts)}**.",
        "",
        "| Agent | Runs | Cost total | Mean cost | p50 ms | p95 ms | Approval | Rejection | Max day burn | Alerts |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in board.rollups:
        alert_text = ", ".join(item.code for item in row.alerts) or "—"
        cells = [
            row.agent_id,
            str(row.runs),
            _usd(row.cost_micro_usd_total),
            _usd(row.cost_per_run_mean),
            _num(row.latency_p50_ms),
            _num(row.latency_p95_ms),
            _pct(row.human_approval_rate),
            _pct(row.rejection_rate),
            _pct(row.budget_burn_ratio),
            alert_text,
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## Alerts", ""])
    if not board.alerts:
        lines.append("No cap or SLO alerts in this window.")
    else:
        for alert in board.alerts:
            lines.append(f"- `{alert.code}` **{alert.agent_id}**: {alert.message}")
    if source == SOURCE_GENERATED:
        cost_heading = "Daily fleet cost (simulated illustrative example)"
    else:
        cost_heading = "Daily fleet cost (ingested file)"
    lines.extend(["", f"## {cost_heading}", ""])
    lines.append("| Day | Cost |")
    lines.append("| --- | ---: |")
    for day, cost in board.daily_cost_micro_usd.items():
        lines.append(f"| {day} | {_usd(cost)} |")
    lines.append("")
    return "\n".join(lines)


def _bar_chart(title: str, rows: list[tuple[str, float]], unit: str) -> str:
    if not rows:
        return f"<p>No data for {_esc(title)}.</p>"
    width = 720
    label_w = 180
    bar_h = 18
    gap = 8
    max_value = max(value for _, value in rows) or 1.0
    height = 36 + len(rows) * (bar_h + gap)
    parts = [
        f'<svg role="img" aria-label="{_esc(title)}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<text x="0" y="16" font-size="14" font-family="sans-serif">{_esc(title)}</text>',
    ]
    for index, (label, value) in enumerate(rows):
        y = 28 + index * (bar_h + gap)
        bar_w = (width - label_w - 80) * (value / max_value)
        parts.append(f'<text x="0" y="{y + 13}" font-size="12" font-family="sans-serif">{_esc(label)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" fill="#0f6e6b"></rect>')
        value_label = _esc(f"{value:.0f} {unit}")
        parts.append(
            f'<text x="{label_w + bar_w + 6:.1f}" y="{y + 13}" font-size="12" '
            f'font-family="sans-serif">{value_label}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_html(board: Board, *, generated_on: str, source: str) -> str:
    alert_rows = (
        "".join(
            f"<li><code>{_esc(alert.code)}</code> <strong>{_esc(alert.agent_id)}</strong> — {_esc(alert.message)}</li>"
            for alert in board.alerts
        )
        or "<li>No cap or SLO alerts in this window.</li>"
    )
    body_rows = []
    for row in board.rollups:
        alert_text = ", ".join(item.code for item in row.alerts) or "—"
        cells = [
            _esc(row.agent_id),
            str(row.runs),
            _esc(_usd(row.cost_micro_usd_total)),
            _esc(_usd(row.cost_per_run_mean)),
            _esc(_num(row.latency_p50_ms)),
            _esc(_num(row.latency_p95_ms)),
            _esc(_pct(row.human_approval_rate)),
            _esc(_pct(row.rejection_rate)),
            _esc(_pct(row.budget_burn_ratio)),
            _esc(alert_text),
        ]
        body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>")
    cost_bars = [
        (row.agent_id, row.cost_per_run_mean or 0.0) for row in board.rollups if row.cost_per_run_mean is not None
    ]
    latency_bars = [
        (row.agent_id, row.latency_p95_ms or 0.0) for row in board.rollups if row.latency_p95_ms is not None
    ]
    daily_bars = [(day, float(cost)) for day, cost in board.daily_cost_micro_usd.items()]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Governance cost board — {_esc(board.organization)}</title>
<style>
body {{ font-family: Palatino, Georgia, serif; margin: 2rem; color: #1c2430; background: #f6f4ef; }}
h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
p, li, td, th {{ line-height: 1.4; }}
.banner {{ background: #efe6c9; border: 1px solid #c8b56a; padding: 0.6rem 0.8rem; }}
table {{ border-collapse: collapse; width: 100%; background: white; margin: 1rem 0 2rem; }}
th, td {{ border: 1px solid #d5d0c6; padding: 0.35rem 0.45rem; font-size: 0.92rem; text-align: left; }}
th {{ background: #e7efe9; }}
code {{ font-family: ui-monospace, monospace; }}
</style>
</head>
<body>
<h1>Governance and cost board</h1>
<p>{_esc(board.organization)} · {_esc(generated_on)}</p>
<p class="banner">{_esc(source_banner(source))}
This page is a static report. It is not a certification, not legal advice,
and it does not claim NIST or EU AI Act compliance.</p>
<h2>Alerts ({len(board.alerts)})</h2>
<ul>
{alert_rows}
</ul>
<h2>Per agent</h2>
<table>
<thead><tr>
<th>Agent</th><th>Runs</th><th>Cost total</th><th>Cost/run mean</th>
<th>Latency p50 ms</th><th>Latency p95 ms</th><th>Approval rate</th>
<th>Rejection rate</th><th>Max day / cap</th><th>Alerts</th>
</tr></thead>
<tbody>
{"".join(body_rows)}
</tbody>
</table>
<h2>Charts</h2>
{_bar_chart("Mean cost per run (micro-USD)", cost_bars, "µUSD")}
{_bar_chart("Latency p95 (ms)", latency_bars, "ms")}
{_bar_chart("Fleet cost by day (micro-USD)", daily_bars, "µUSD")}
</body>
</html>
"""


def write_report(
    board: Board,
    out_dir: Path,
    *,
    generated_on: str,
    source: str,
    extra: dict[str, object] | None = None,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(
        render_markdown(board, generated_on=generated_on, source=source),
        encoding="utf-8",
    )
    (out_dir / "index.html").write_text(
        render_html(board, generated_on=generated_on, source=source),
        encoding="utf-8",
    )
    summary: dict[str, object] = {
        "source": source,
        "illustrative": source == SOURCE_GENERATED,
        "generated_on": generated_on,
        "organization": board.organization,
        "alert_count": len(board.alerts),
        "alerts": [alert.to_dict() for alert in board.alerts],
        "board": board.to_dict(),
    }
    if extra:
        summary.update(extra)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alert_codes(alerts: list[Alert]) -> list[str]:
    return sorted({alert.code for alert in alerts})
