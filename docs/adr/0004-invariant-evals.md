# 0004 — Invariant evals, not trajectories

## Status

Accepted (2026-10-17).

## Context

Pinning the exact tool-call sequence makes a suite brittle and does not state the harm we care about.

## Decision

Evals assert three invariants: no harmful effect, cost within the per-run cap, no unapproved external action. `evals/suite.yaml` must pass. `evals/regression.yaml` must fail, and CI asserts that non-zero exit. Providers in the eval path must be offline.

## Consequences

A change that still respects the invariants stays green. A change that allows `transfer_funds` or an over-cap run goes red. The suite does not grade answer text.
