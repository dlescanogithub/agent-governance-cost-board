# Risks

Educational mapping at the bottom. **Not legal advice. Not a certification. Not an ISO 42001 or AIGP engagement. It does not establish compliance with the NIST AI RMF or the EU AI Act.**

Owners are fictional role ids.

## Matrix

| Risk | Probability | Impact | Mitigation in this repo | Owner |
| --- | --- | --- | --- | --- |
| High-tier agent ships with no human gate | Medium if the YAML is edited by hand | High (external effect) | Policy `high_risk_human_gate`; CI on the fleet file | fleet-governor |
| No backup owner | Medium | Medium | Policy `high_risk_backup_owner` for high tier | fleet-governor |
| Stale review | High over a year | Medium | `review_fresh` against an injected clock | agent owner |
| Per-run cap above per-day cap | Low | Medium (the cap is incoherent) | `cap_consistency` | finance-ops for finance agents; fleet-governor for the file |
| Cost spike | Planted in `traces/generation.yaml` so the cap alert can be shown. Illustrative, not an observed incident | Medium in the simulation; unknown in a real fleet | Aggregator alerts; runbook kill switch | agent owner, with fleet-governor |
| Latency SLO miss | Planted for `bulletin-draft` in the same profile | Low in the simulation | `p95_latency_slo_breach` alert | agent owner |
| Harmful effect name in a trace | Low if the generator is the only writer | High | Invariant `no_harmful_effect`; regression fixture proves the gate fails | fleet-governor |
| Unapproved external effect | Low in the generator; the regression file includes one | High | Invariant `no_unapproved_external_action` | human queue |
| Real provider turned on by accident | Low | Medium (spend, data leaving the machine) | Default off; evals refuse a non-offline setting; tests block sockets | whoever runs the command |
| Secret committed | Low | High | `secretscan` in CI; `.env` gitignored | fleet-governor |
| YAML rewrite drops comments | High if you use the control CLI | Low | Commands default to a new file; git diff | whoever runs the command |
| Board mistaken for a certification | Medium in a portfolio reading | High (false assurance) | Disclaimer in the HTML and in this file | fleet-governor |
| Ingest mapping drops or misreads a field | Medium if a file uses a different shape | Low for the hand-written sample; higher for a real export | `docs/TRACE_INGEST.md`; the loader rejects unknown fields | fleet-governor |

Probability and impact are judgments for this portfolio.

## Educational map

Internal tier is **not** the legal class. The table says which NIST AI RMF function the control rhymes with, and which EU AI Act bucket a reader might confuse it with.

| Control in this repo | NIST AI RMF function (educational) | Easy-to-confuse EU AI Act bucket (educational) |
| --- | --- | --- |
| Inventory, owners, tier rubric | Govern, Map | Does not assign a legal risk class |
| Data classes on medium and high | Map | Transparency / data governance themes, not a compliance claim |
| Human gate on external effects | Govern, Manage | Human oversight theme. Our "high" is not "high-risk AI system" in the Act |
| Caps, SLO alerts, simulated metrics | Measure | Post-market monitoring is **not** implemented |
| Kill switch and prompt rollback | Manage | Not a conformity assessment |
| Invariant evals in CI | Measure | Not a notified-body test |
| This disclaimer | Govern | Required so the map is not read as advice |

EU AI Act buckets a reader should keep separate from our tiers: unacceptable, high-risk, limited risk (transparency), minimal risk. We do not classify Harborline agents into those buckets.

Full rubric: `docs/RISK_RUBRIC.md`.
