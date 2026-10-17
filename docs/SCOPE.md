# Scope

No fees. No statement of work. Harborline Cooperative is fictional.

## Phase 0 — this repo (implemented)

- Inventory of 12 synthetic agents, JSON Schema, tier rubric.
- Policy CLI and CI, including `inventory/violating.yaml` which must fail.
- Seeded traces, aggregator, static board committed under `docs/example-board/`.
- Invariant evals and `eval-regression`, which must fail.
- Kill switch and prompt rollback as local YAML edits.
- Educational NIST / EU note with a disclaimer.

Exit criteria for phase 0:

- `python3 -m pytest` meets the 80% coverage floor.
- Fleet policy exits 0 for `--today 2026-10-17`.
- Violating inventory exits non-zero.
- `python3 -m governance_board eval` exits 0.
- `python3 -m governance_board eval-regression` exits non-zero.
- Demo cost is zero and uses no network.

## Phase 1 — shadow on a real export (design only)

Replace the generator with JSONL copied from a runtime. Keep the real provider off in CI. Keep payloads out of the trace. Exit when a week of real traces (not in this repo) produces a board a human will open.

## Phase 2 — gate the high tier (design only)

The runtime refuses an external effect unless `approval` is `approved`, using the same invariant. Exit when a staged drill shows a rejected effect and a killed agent. This repo only has the drill as a fixture and a CLI.

## Phase 3 — alerts and access (design only)

SSO/RBAC on who may edit the inventory. Alert delivery. GRC export. Exit criteria belong to that future system, not to this package.

## Assumptions

- One YAML file is an acceptable source of truth for a fleet of this size.
- Role ids are enough; the HR system is out of scope.
- "Today" can be injected.
- Simulated latency is good enough to show an SLO breach in a demo.

## Out of scope

- Legal advice, certification, ISO 42001, production traffic.
- Answer quality.
- Live dashboards, pagers, ticketing.
- Multi-tenant hosting.
- Real prices and real clients.
