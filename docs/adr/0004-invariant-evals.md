# 0004 — Invariant evals, not trajectories

## Status

Accepted (2026-10-17).

## Context

Pinning the exact tool-call sequence makes a suite brittle and does not state the harm we care about.

## Decision

Evals assert three invariants: no harmful effect, cost within the per-run cap, no unapproved external action. `evals/suite.yaml` must pass. The same `eval` command also runs seeded property checks: a cap breach is always flagged, an engaged kill switch always blocks, rollback restores the previous prompt version, and an agent with no owner or no risk tier fails policy. `evals/regression.yaml` must fail, and CI asserts that non-zero exit. The regression command does not run the property checks, so a green property suite cannot hide the forced failure. Providers in the eval path must be offline.

## Consequences

A change that still respects the invariants stays green. A change that allows `transfer_funds` or an over-cap run goes red. The suite does not grade answer text.
