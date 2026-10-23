# Changelog

## 0.1.1 - 2026-10-22

- Translated `docs/HOW_IT_WORKS.md` into English. Removed the interview framing. The page is a walkthrough for engineers and buyers.
- README docs table now describes that walkthrough in English.
- Bumped the package version from 0.1.0 to 0.1.1 in `pyproject.toml` and `governance_board.__version__`.
- The 2026-10-22 pytest, policy, eval, and secret-scan figures stay the measurements recorded on package 0.1.0. Those commands do not read the walkthrough text.

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
- Recorded pytest result corrected to 29 passed and 90.09% coverage. Command `python3 -m pytest`, pytest 9.1.1, Python 3.12.3, 2026-10-17.

This version does not claim a live deployment. The `Dockerfile` was not built in the authoring environment.

Docs, still 0.1.0, 2026-10-22 (no tag):

- README rewritten in English: Start here, Quickstart, Business value, Proof, and What this does NOT prove. The simulated board table is unchanged.
- Added `docs/BUSINESS_VALUE.md`. It restates the [EST] model in `docs/BUSINESS_CASE.md` and does not add a second set of dollar figures.
- `docs/HOW_IT_WORKS.md` records the 2026-10-22 measurement below.
- Pytest re-measured 2026-10-22, Python 3.12.3, pytest 9.1.1, coverage 7.17.0, package 0.1.0: 29 passed. pytest-cov total coverage 90.09%. Statement coverage 93.158953722334% (1389 of 1491). Branch coverage 79.82062780269058% (356 of 446). The same day, fleet policy exited 0, the violating inventory exited 1 with five violations, eval exited 0, eval-regression exited 1, and the secret scan reported zero findings.
