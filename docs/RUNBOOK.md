# Runbook

Audience: someone operating the **synthetic** Harborline board. Roles are job ids in the inventory, not people.

## Ownership

| Role | Owns |
| --- | --- |
| fleet-governor | `inventory/fleet.yaml`, the policy CI check, this runbook |
| agent owner (for example `finance-ops`) | That agent's prompt version and budget numbers |
| backup owner (for example `finance-backup`) | The same agent when the owner is absent |
| human queue | The external effect named on the gate |

There is no on-call rotation in this repo. Handoff is: the YAML, `docs/example-board/summary.json`, and the prompt registry.

## Operate

From the repo root:

```bash
python3 -m governance_board policy \
  --inventory inventory/fleet.yaml \
  --prompts prompts/registry.yaml \
  --today 2026-10-17

python3 -m governance_board demo
```

Read `demo-out/index.html` or the committed `docs/example-board/index.html`. Logs are JSON on stderr.

## Monitor

The implemented monitor is the report. Alerts:

| Code | Meaning |
| --- | --- |
| `per_run_cap_exceeded` | At least one run cost more than the per-run cap |
| `per_day_cap_exceeded` | A UTC day's sum exceeded the per-day cap |
| `p95_latency_slo_breach` | Aggregated p95 latency is above the SLO |
| `cost_per_run_slo_breach` | Mean cost/run is above the SLO |
| `no_observations` | Inventory agent with zero events in the file |
| `unknown_agent` | Traces for an id that is not in the inventory |

Nothing pages a human. Delivery is design-only.

## Incident: token cost spike

Example already in the sample board: `refund-advisor` on 2026-10-15.

1. **Detect.** Open the report. Confirm `per_day_cap_exceeded` and the date in the message. Confirm the traces are the file you think they are (`traces/fleet.meta.json` has the seed).
2. **Cap.** The cap is the inventory budget. This CLI does not change a vendor quota. Lowering the cap is an inventory edit followed by `policy` until it passes. A lower cap does not claw back spend already in the JSONL.
3. **Disable.** Engage the kill switch. This rewrites YAML and drops comments. It does not signal a live process, because there is no live process here.

```bash
python3 -m governance_board kill-switch \
  --inventory inventory/fleet.yaml \
  --agent-id refund-advisor \
  --output /tmp/fleet-killed.yaml
```

Check the output: `kill_switch: engaged` and `status: disabled`. Policy accepts that pair. `engaged` with `status: active` fails the policy.

4. **Rollback prompt / model.** The registry keeps `1.0.0` (model `sim-small`) and `1.1.0` (model `sim-balanced`, current). Roll back to `1.0.0` and point the inventory at it:

```bash
python3 -m governance_board rollback \
  --registry prompts/registry.yaml \
  --registry-output /tmp/registry.yaml \
  --agent-id refund-advisor \
  --to-version 1.0.0 \
  --inventory /tmp/fleet-killed.yaml \
  --inventory-output /tmp/fleet-rolled.yaml
```

5. **Re-check.** Run `policy` on `/tmp/fleet-rolled.yaml` with the new registry and the same `--today`. Do not copy the killed file over `inventory/fleet.yaml` in this portfolio unless you mean to change the demo. The committed fleet stays active so the sample board still shows the spike.

6. **Close.** Note the alert codes, the version you rolled back to, and who engaged the switch. There is no GRC export.

## Rollback of the runbook itself

Restore the previous YAML from git. The commands write new files when you pass `--output` / `--registry-output`. `--in-place` on the kill switch is optional and easy to regret.

## Handoff

Leave the inventory path, the trace path, the injected today, and the last `summary.json`. Say whether the kill switch in the committed fleet is `disengaged` (it is, as of the sample).
