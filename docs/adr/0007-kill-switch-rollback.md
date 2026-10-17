# 0007 — Kill switch and prompt rollback

## Status

Accepted (2026-10-17).

## Context

The cost-spike runbook needs a way to disable an agent and to point it at an older prompt and model. There is no live runtime in this repo.

## Decision

The inventory has `kill_switch: engaged|disengaged`. Engaged requires `status: disabled`. The prompt registry stores every version and exactly one `current`. `kill-switch` and `rollback` rewrite YAML to a new file unless `--in-place` is passed. Rollback updates `prompt_version`, `version`, and `model` on the agent when an inventory is supplied.

## Consequences

The commands do not stop a process. They prepare the file a runtime would read. Comment preservation is sacrificed. Git remains the undo.
