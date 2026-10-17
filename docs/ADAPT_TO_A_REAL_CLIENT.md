# Adapt this to a real client

Short version. Do the discovery in `docs/DISCOVERY.md` first. Keep this repo's CI as the shadow gate until the answers are stable.

Replace:

- `Harborline Cooperative` and the role ids with the client's own names. Do not paste a real customer name into a public fork of this portfolio.
- `inventory/fleet.yaml` with their inventory. Keep the schema. Expect the first import to fail policy; that failure is the point.
- `traces/generation.yaml` with an export in the native JSONL shape, or the alternate shape in `docs/architecture.md` if it actually matches. Confirm the field map on a sample before trusting totals.
- The simulated rate card with their contract rates, cited and dated. Until then, keep the [EST] label.
- The SLO numbers. The ones in the fleet file are [EST] targets chosen so the demo shows one latency breach.

Leave in place until a later phase: fake/cassette providers in CI, the invariant evals, the violating-fixture pattern, the kill-switch field.

Do not turn on `GOVERNANCE_REAL_PROVIDER_ENABLED` in CI. Do not log document bodies into the JSONL.

This file is not a proposal and has no fees.
