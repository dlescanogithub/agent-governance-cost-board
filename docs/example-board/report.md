# Cost and governance board — Harborline Cooperative

Date label: 2026-10-17.

SIMULATED / illustrative example. Source: simulated generator. A spike is planted in traces/generation.yaml so a cap alert can be shown. This page demonstrates policy-as-code, budget caps, the kill switch, and prompt rollback. It is not a measurement.

Alerts: **3**.

| Agent | Runs | Cost total | Mean cost | p50 ms | p95 ms | Approval | Rejection | Max day burn | Alerts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| intake-triage | 168 | $1.8145 | $0.0108 | 626.0 | 919.9 | 0.0% | 0.0% | 4.6% | — |
| claim-draft | 168 | $4.2866 | $0.0255 | 967.5 | 1465.2 | 16.7% | 6.0% | 9.0% | — |
| kb-search | 168 | $1.3062 | $0.0078 | 483.0 | 670.8 | 0.0% | 0.0% | 5.1% | — |
| invoice-extract | 168 | $2.4618 | $0.0147 | 780.5 | 1076.9 | 0.0% | 0.0% | 6.4% | — |
| meeting-notes | 168 | $2.5002 | $0.0149 | 828.0 | 1278.2 | 0.0% | 0.0% | 9.6% | — |
| change-review | 168 | $2.5863 | $0.0154 | 868.5 | 1238.3 | 0.0% | 0.0% | 6.5% | — |
| vendor-screener | 168 | $3.2250 | $0.0192 | 1019.0 | 1500.1 | 10.1% | 4.2% | 6.2% | — |
| onboarding-coach | 168 | $1.3107 | $0.0078 | 551.0 | 710.5 | 0.0% | 0.0% | 5.0% | — |
| refund-advisor | 168 | $8.4364 | $0.0502 | 1100.0 | 1761.2 | 26.8% | 4.8% | 276.6% | per_run_cap_exceeded, per_day_cap_exceeded |
| bulletin-draft | 168 | $4.4372 | $0.0264 | 2905.5 | 5895.4 | 0.0% | 0.0% | 12.6% | p95_latency_slo_breach |
| shift-suggester | 168 | $1.6534 | $0.0098 | 705.5 | 961.2 | 23.2% | 3.0% | 4.3% | — |
| safety-checklist | 168 | $0.8333 | $0.0050 | 402.5 | 553.3 | 0.0% | 0.0% | 3.2% | — |

## Alerts

- `per_run_cap_exceeded` **refund-advisor**: 12 runs over the per-run cap of 100000 micro-USD
- `per_day_cap_exceeded` **refund-advisor**: daily cost exceeded the per-day cap on 2026-10-15
- `p95_latency_slo_breach` **bulletin-draft**: p95 latency 5895.4 ms > SLO 2000 ms

## Daily fleet cost (simulated illustrative example)

| Day | Cost |
| --- | ---: |
| 2026-10-04 | $2.2832 |
| 2026-10-05 | $2.2973 |
| 2026-10-06 | $2.2769 |
| 2026-10-07 | $2.2658 |
| 2026-10-08 | $2.2652 |
| 2026-10-09 | $2.2991 |
| 2026-10-10 | $2.3161 |
| 2026-10-11 | $2.2751 |
| 2026-10-12 | $2.3154 |
| 2026-10-13 | $2.2864 |
| 2026-10-14 | $2.2698 |
| 2026-10-15 | $5.1678 |
| 2026-10-16 | $2.2507 |
| 2026-10-17 | $2.2825 |
