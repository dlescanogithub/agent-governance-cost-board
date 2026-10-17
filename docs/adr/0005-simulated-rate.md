# 0005 — Simulated micro-USD rate card

## Status

Accepted (2026-10-17).

## Context

The board needs a cost figure. Copying a vendor price without a citation would be a fake measurement. This portfolio has no contract rate.

## Decision

`traces/generation.yaml` sets 5 micro-USD per input token and 15 per output token. Docs label that card simulated and [EST]. ROI dollars in `docs/BUSINESS_CASE.md` are a separate illustrative model and are not converted from this card.

## Consequences

Absolute dollars in the sample board are small on purpose. Comparisons (burn vs cap, which agent alerted) are the useful output. Replacing the card is a data change, not a code change.
