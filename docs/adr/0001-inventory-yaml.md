# 0001 — Inventory as YAML with JSON Schema

## Status

Accepted (2026-10-17).

## Context

A fleet of 12 agents needs owners, tiers, caps, and gates in a file a human can review and a command can reject.

## Decision

Store the inventory as YAML. Validate it with JSON Schema (`src/governance_board/schema/inventory.schema.json`) before the policy rules run. Schema failures become a policy report with rule `schema` and a non-zero exit, so CI always sees a report.

## Consequences

YAML dates are coerced to ISO strings before validation, because PyYAML parses unquoted dates. Comments are for humans; the control commands that rewrite YAML do not keep them. A database or an API would be a later phase (`docs/SCOPE.md`).
