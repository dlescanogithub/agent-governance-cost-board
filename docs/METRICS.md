# Metrics

Two layers. Do not mix them.

## Command results (measured, 2026-10-17)

Package 0.1.0. Python 3.12.3.

| Metric | Command | Value |
| --- | --- | --- |
| Agents | rows in `inventory/fleet.yaml` | 12 |
| Policy violations | `policy` on the fleet, `--today 2026-10-17` | 0 (exit 0) |
| Eval gate | `python3 -m governance_board eval` | exit 0; 3 YAML cases plus 32 property trials |
| Regression gate | `python3 -m governance_board eval-regression` | exit 1; 3 breaches (expected) |
| Pytest | `python3 -m pytest` (pytest 9.1.1, Python 3.12.3, 2026-10-17) | 29 passed, total coverage 90.09% |
| Coverage floor | `pytest` `--cov-fail-under` | 80% |

## Pytest re-measured (2026-10-22)

Same package 0.1.0. Python 3.12.3. pytest 9.1.1. coverage 7.17.0. Command `python3 -m pytest --cov=governance_board --cov-report=term-missing --cov-fail-under=80`. Branch measurement is on in `pyproject.toml`, so the printed total is not line coverage alone.

| Figure | Value |
| --- | --- |
| Tests | 29 passed |
| Total coverage pytest-cov printed | 90.09% (`percent_covered` 90.08776458440887) |
| Statement (line) coverage | 93.158953722334% (1389 of 1491 statements) |
| Branch coverage | 79.82062780269058% (356 of 446) |

The run printed `CoverageWarning: Module governance_board was previously imported, but not measured`. The percentages are the totals coverage wrote anyway. The 2026-10-17 row above did not publish the statement split. The same day, fleet policy exited 0 with zero violations, the violating inventory exited 1 with five violations, eval exited 0, eval-regression exited 1 with three breaches, and the secret scan reported zero findings. The illustrative board was not regenerated.

## Illustrative board (simulated, not a measurement)

Command and label: `docs/example-board/EXAMPLE.md`. The spike is planted in `traces/generation.yaml`.

| Figure | Where it comes from | Value on the example file |
| --- | --- | --- |
| Events | seeded generator, seed 20261017 | 2016 |
| Alerts | aggregator on that file | 3 |
| Planted daily cap example | `refund-advisor` on 2026-10-15, `token_multiplier` 8 | 3,319,160 micro-USD vs cap 1,200,000 |
| Planted latency example | `bulletin-draft` p95 | 5895.4 ms vs SLO 2000 ms |

Percentiles use linear interpolation (`governance_board.stats.percentile`).

Human approval rate is `approved / runs`, including runs with `approval: none` in the denominator. Rejection rate counts `status == rejected` or `approval == rejected`, over runs. Both are in `summary.json`.

Answer quality is out of scope.

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
