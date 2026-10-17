# Changelog

## 0.1.0 — 2026-10-17

- Inventory YAML with JSON Schema validation for a synthetic 12-agent fleet.
- Policy-as-code CLI, including a violating fixture that must fail.
- Seeded JSONL trace generator, aggregator, and static HTML/Markdown board.
- Invariant evals and a forced regression that must fail.
- Kill switch and versioned prompt rollback commands.
- CI for lint, types, tests with a coverage floor, secret scan, and both gates.

Same day, still 0.1.0 (no tag):

- Generator output is labelled a simulated illustrative example. The spend spike is planted in `traces/generation.yaml`.
- Runtime-evals JSONL ingest, validation, a hand-written sample, and a source line on the board header.
- Seeded property checks on the eval gate. The forced regression still fails on purpose.
- Secret scanner aligned with the shared portfolio pattern list. `docs/PROVENANCE.md` records its sha256.

This version does not claim a production deployment. The `Dockerfile` was not built in the authoring environment.
