# 0002 — Policy as code in CI

## Status

Accepted (2026-10-17).

## Context

A dashboard that only displays a red row does not stop a bad inventory from merging.

## Decision

`python3 -m governance_board policy` exits 0 only when every rule passes. CI runs it on `inventory/fleet.yaml`. CI also runs it on `inventory/violating.yaml` and fails the job if that command exits 0. The violating file is schema-valid so the failure is the policy, not a parse error.

## Consequences

Rules live in `governance_board.policy` and are unit-tested. Changing the rubric means changing code and the docs in `docs/RISK_RUBRIC.md` together. The injected `--today` keeps the review-age rule stable.
