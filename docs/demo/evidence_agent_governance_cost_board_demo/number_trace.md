# Number trace — agent-governance-cost-board demo
| On screen / spoken | Value | Kind | Source |
| --- | --- | --- | --- |
| Agents in fleet | 12 | SIMULATED inventory | `inventory/fleet.yaml` + `python -m governance_board demo` |
| Policy violations | 0 | MEASURED this take | `governance_board policy --today 2026-10-17` |
| Simulated events on board | 2016 | SIMULATED generator | demo stdout |
| Alerts | 3 | SIMULATED (planted spike) | demo stdout |
| Eval cases / property trials | 3 / 32 | MEASURED | `governance_board eval` |
| Regression breaches | 3 (exit 1) | MEASURED | `governance_board eval-regression` |
| Harborline Cooperative | — | SYN | fiction |
| Lab path cost | US$0 | MEASURED | no network / no key |
