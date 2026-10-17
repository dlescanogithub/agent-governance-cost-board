# Metrics

Two layers. Do not mix them.

## Measured on the simulated fleet (2026-10-17)

Command and commit: `docs/example-board/MEASURED.md`. Package 0.1.0.

| Metric | Definition | Value |
| --- | --- | --- |
| Agents | Rows in `inventory/fleet.yaml` | 12 |
| Policy violations | `policy` command, `--today 2026-10-17` | 0 |
| Events | Lines in `traces/fleet.jsonl` | 2016 |
| Alerts | Entries in `summary.json` | 3 |
| Daily cap breach | `refund-advisor` on 2026-10-15 | 3,319,160 micro-USD vs cap 1,200,000 |
| Latency SLO breach | `bulletin-draft` p95 | 5895.4 ms vs SLO 2000 ms |
| Eval breaches on the suite | `evals/suite.yaml` | 0 |
| Eval breaches on the regression | `evals/regression.yaml` | 3 (expected) |
| Test coverage floor | `pytest` `--cov-fail-under` | 80% |

Percentiles use linear interpolation (`governance_board.stats.percentile`).

Human approval rate is `approved / runs`, including runs with `approval: none` in the denominator. Rejection rate counts `status == rejected` or `approval == rejected`, over runs. Both are in `summary.json`.

Quality of answers is **not measured**.

## Success metrics if a team adopts the pattern [EST]

These are targets to agree in discovery, not results of this repo.

| Metric | Sketch target [EST] | Why it would matter |
| --- | --- | --- |
| Share of agents with a passing policy | 100% of in-scope agents | The gate is real only if the inventory is complete |
| Time to notice a daily cap breach | 1 business day | Versus a monthly invoice |
| High-tier agents with a named backup | 100% | The policy already fails otherwise |
| Unapproved external effects in traces | 0 | The invariant |
| Incidents with a rollback version recorded | 100% of cost-spike incidents | The registry has history |

Adoption and savings stay [EST] until someone runs phase 1 in `docs/SCOPE.md` on real traces. This repo does not report them as measured.
