# agent-governance-cost-board

## Start here

It proves a local policy gate on a simulated fleet of 12 agents: the fleet file passes, a violating inventory fails, invariant evals pass, and a forced regression fails. The cost board is a simulated example, not a measured saving.

One command, after `python3 -m pip install -e ".[dev]"`: `python3 -m governance_board demo`.

Walkthrough: [docs/HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md). Value plan: [docs/BUSINESS_VALUE.md](docs/BUSINESS_VALUE.md).

Policy checks, invariant evals, and a static cost board for a **simulated** fleet of 12 agents at the fictional Harborline Cooperative. The suite tests inventory rules, effect gates, and budget math. It does not test answer quality, and it does not call a model vendor.

## Problem

A fleet is hard to govern when ownership, human gates, and spend caps live in slides. This repo keeps them in YAML and checks them in CI. The static board renders either a seeded generator file or an ingested JSONL file, and the header says which one.

The board demonstrates the mechanism: policy-as-code, budget caps, a kill switch, and prompt rollback. It does not report a spend finding. The `refund-advisor` day over its cap is planted by `spike.token_multiplier` in `traces/generation.yaml`. Every figure from that generator is a **SIMULATED / illustrative example**.

Recorded on 2026-10-17, and run again on 2026-10-22 (package 0.1.0, Python 3.12.3, `--today 2026-10-17`): the fleet policy exits **0** with **zero violations**. The numbers for that re-run are in [Proof](#proof).

```bash
python3 -m governance_board policy \
  --inventory inventory/fleet.yaml \
  --prompts prompts/registry.yaml \
  --today 2026-10-17
```

## Architecture

```mermaid
flowchart LR
  inv[Inventory YAML] --> policy[Policy checks]
  reg[Prompt registry] --> policy
  profile[Generation profile] --> gen[Seeded generator]
  inv --> gen
  gen --> jsonl[Generated JSONL]
  file[Runtime-evals JSONL] --> ingest[Ingest and validate]
  jsonl --> agg[Aggregator]
  ingest --> agg
  inv --> agg
