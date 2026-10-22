# Value realization plan: adopting `agent-governance-cost-board`

> **Important notice**
>
> - **Fictional organization.** Harborline Cooperative is invented in this repo. It is not a client and not an employer. Do not paste a real organization name over it in a public copy. See [ADAPT_TO_A_REAL_CLIENT.md](ADAPT_TO_A_REAL_CLIENT.md).
> - **Inspired by the AWS Business Value Realization (BVR) framework:** a value plan, a baseline and a target for each KPI, and a point where the buyer would confirm the result. **It is not an official AWS template** (the official template is not public) and **I do not hold the AWS BVR Competency**, which is awarded to AWS partner companies, not to individuals.
> - This file **restates** [BUSINESS_CASE.md](BUSINESS_CASE.md), [COST.md](COST.md), [METRICS.md](METRICS.md), [SCOPE.md](SCOPE.md), and [RISKS.md](RISKS.md). It does not add a second dollar model. Where those files mark a figure **[EST]** or **SIMULATED**, this file uses the same tag.
> - Labels:
>   - **MEASURED**: a command run recorded with a date.
>   - **[EST]**: an illustrative assumption already marked that way in this repo.
>   - **SIMULATED**: output of the seeded generator. The spike is planted in `traces/generation.yaml`.
>   - **UNVERIFIED**: not measured and not given a number in this repo. No figure is filled in for those cells.
> - Package **0.1.0**. The pytest line below was measured on **2026-10-22** with Python 3.12.3. The illustrative board was **not** regenerated that day. Its numbers stay the 2026-10-17 file described in [example-board/EXAMPLE.md](example-board/EXAMPLE.md).

---

## Buyer and problem

**Buyer in this exercise:** the fictional Harborline Cooperative. Role ids in the inventory, not named people. [RUNBOOK.md](RUNBOOK.md) splits ownership this way: the fleet governor owns `inventory/fleet.yaml` and the policy check; the agent owner owns that agent's prompt version and budget numbers; a human queue owns each external effect.

**Problem, as [BUSINESS_CASE.md](BUSINESS_CASE.md) states it.** Agents get built one by one. The owner, the backup, the human who may approve an external effect, and the daily cap sit in a document that CI never reads. A cost spike shows up on a monthly bill. An unapproved write shows up in an incident channel.

**What the lab changes.** The inventory is a file the policy command can fail. The board shows burn against the cap from traces. The runbook has a kill switch and a prompt version to roll back to. That is the implemented loop. It is phase 0 in [SCOPE.md](SCOPE.md): shadow data, local gates, no live runtime.

## What the lab actually does

- Twelve synthetic agents in `inventory/fleet.yaml`. JSON Schema rejects a malformed file. Policy rules in `src/governance_board/policy.py` include owner required, cap consistency (per-run not above per-day, SLO cost/run not above per-run), review freshness against an injected clock, an allowlist of providers (`fake`, `sim`, `cassette`), kill-switch status, data classes and eval evidence on medium and high tiers, and, for high tier, a required human gate plus a backup owner who is a different role.
- **MEASURED 2026-10-22**, Python 3.12.3, package 0.1.0, `--today 2026-10-17`: policy on `inventory/fleet.yaml` exited 0 with zero violations. The same command on `inventory/violating.yaml` exited 1 with five violations (cap consistency, empty owner, missing high-tier backup, missing high-tier human gate, stale review).
- Invariants in `src/governance_board/evalkit/invariants.py`: no harmful effect (`transfer_funds`, `delete_customer_record`, `exfiltrate_data`, `send_external_email`, `provision_production_access`), cost within the per-run cap, no external effect without `approval` equal to `approved`. External names in `src/governance_board/effects.py`: `update_claim_file`, `send_vendor_decision`, `write_ledger_note`, `update_schedule`.
- **MEASURED 2026-10-22:** `python3 -m governance_board eval` exited 0. The JSON reported 3 cases, property trials 32, zero breaches. Four properties in `src/governance_board/evalkit/properties.py` each use that trial count (seed `20261017`): a cap breach is flagged, an engaged kill switch blocks, rollback restores the previous prompt version, and an agent with no owner or no tier fails policy. `python3 -m governance_board eval-regression` exited 1 with three breaches on one event (`no_harmful_effect`, `cost_within_cap`, `no_unapproved_external_action`). The regression is supposed to fail.
- The static board reads either the seeded generator or a runtime-evals JSONL file. The header names which. The committed example is source `simulated-generator`. The sample under `traces/samples/` is hand-written. Detail: [TRACE_INGEST.md](TRACE_INGEST.md).
- Demo, tests, and CI do not call a paid API. [COST.md](COST.md) states their cost as zero. The real HTTP provider stays off unless `GOVERNANCE_REAL_PROVIDER_ENABLED=1`. CI does not set that flag.

## Value levers

These are the levers [BUSINESS_CASE.md](BUSINESS_CASE.md) and [METRICS.md](METRICS.md) already name. None of them is a measured saving.

| Lever | What the repo implements | What it does not show |
| --- | --- | --- |
| A file CI can fail | Policy command, plus `inventory/violating.yaml`, which must fail | That a real inventory is complete |
| A cap visible before the monthly bill | Aggregator alerts on the report | That a person opens the report. "1 day" is [EST] |
| A human on effects that leave the system | Policy rule `high_risk_human_gate` and invariant `no_unapproved_external_action` | A real approval queue. The queue is design only |
| A way to stop and roll back | `kill-switch` and `rollback` rewrite local YAML. [RUNBOOK.md](RUNBOOK.md) | A signal to a live process. There is no live process here |
| Evidence with a named source | JSONL, `summary.json`, prompt registry, source line on the HTML header | A GRC export. That is design only |

## Baseline vs target KPIs

Lab columns are **MEASURED** or **SIMULATED** as tagged. Baseline and target columns for a team adopting the pattern are the sketch in [METRICS.md](METRICS.md). They are not results of this repo.

| KPI | Category | Lab, this repo | Baseline if a team adopted the pattern | Target |
| --- | --- | --- | --- | --- |
| Agents with a passing policy | Operational | 12 agents, 0 violations on `inventory/fleet.yaml`. **MEASURED 2026-10-22** (also recorded 2026-10-17) | Not measured outside this lab. **UNVERIFIED** | 100% of in-scope agents. **[EST]** in METRICS.md |
| Time to notice a daily cap breach | Cost control | The planted `refund-advisor` day is an alert on the committed board. **SIMULATED** | 30 days, until a monthly invoice. **[EST]** in BUSINESS_CASE.md | 1 business day, if someone opens the report. **[EST]** |
| High-tier agents with a named backup | Governance | The policy fails the violating fixture when the backup is missing. **MEASURED 2026-10-22** | The same rule, on a real file. Completeness **UNVERIFIED** | 100%. **[EST]** |
| Unapproved external effects | Risk | 0 breaches on the eval gate. The forced regression shows the breach and exits 1. **MEASURED 2026-10-22** | Not measured on a real trace export. **UNVERIFIED** | 0. The invariant |
| Cost-spike incidents with a rollback version recorded | Resilience | The registry has history and the CLI can point at an older version. No incident count | Not measured. **UNVERIFIED** | 100% of cost-spike incidents. **[EST]** |
| Answer quality | Quality | Out of scope | Out of scope | Not a target of this repo |

The three alerts on the illustrative file are **SIMULATED**: per-run cap, per-day cap (both `refund-advisor`), and a p95 latency SLO on `bulletin-draft` (5895.4 ms against an SLO of 2000 ms, from `docs/example-board/summary.json`). That file is not a baseline for a buyer.

## ROI model

Formula used in [BUSINESS_CASE.md](BUSINESS_CASE.md), one incident, not a year:

overrun avoided = (days until the invoice would show it − days until the board shows it) × (spend on a bad day − daily cap).

**[EST] assumptions, copied from that file. Do not replace them with the simulated rate card.** [COST.md](COST.md) says the ROI dollars do not use the generator's rate card.

| Assumption | Value | Tag |
| --- | --- | --- |
| Agents in the fleet | 12 | Matches the synthetic inventory count. The dollar rate does not |
| Model spend per agent per month | $80 | [EST] |
| Monthly fleet spend | $960 | [EST], 12 × 80 |
| Daily cap on the runaway agent | $40 | [EST] |
| Spend during a bad day | $120 | [EST], 3 × the $40 cap. The generator's planted spike is a different example |
| Days until a monthly invoice would show it | 30 | [EST] |
| Days until the board shows it | 1 | [EST], if someone opens the report |
| Overrun avoided on that one incident | $2,320 | [EST], 29 × ($120 − $40) |

The README rounds that incident to **on the order of $2,300** [EST]. Same source.

**What this model does not compute.** A year-1 ROI percentage, a payback month, a labor rate, an integration cost, and an incident count per year are **not in this repo**. They stay **UNVERIFIED**. Filling them in would be a second model. This file does not do that.

What would change the model, as BUSINESS_CASE.md already says: a real daily cap, a real invoice cycle, and a count of incidents per quarter. None of those are in this repo.

The robust value the repo can defend is the control: a failing command when the inventory is wrong, and a report that names whether its numbers came from the generator or from an ingested file. The dollar line is an illustration.

### Separate illustrative spike (not the ROI)

**SIMULATED.** `traces/generation.yaml` plants `refund-advisor` at 3,319,160 micro-USD on 2026-10-15 against a 1,200,000 micro-USD cap (`token_multiplier` 8). At the simulated card that is $3.3192 versus $1.2000. It demonstrates the cap alert. It is not the $120 bad day in the [EST] model, and it is not a measurement.

## Cost table

### [EST] planning figures

| Item | Value | Source |
| --- | --- | --- |
| Monthly fleet spend in the ROI sketch | $960 [EST] | [BUSINESS_CASE.md](BUSINESS_CASE.md), 12 × $80 |
| One caught runaway, overrun avoided | $2,320 [EST] | same file, formula above |
| Input token on the generator card | 5 micro-USD [EST] | `traces/generation.yaml`, written 2026-10-17. Not a vendor price |
| Output token on the generator card | 15 micro-USD [EST] | same file |
| 1 USD | 1,000,000 micro-USD | convention in [COST.md](COST.md) |
| Provider cost of demo, tests, and CI | zero | [COST.md](COST.md): those commands do not call a paid API |

No public price page was copied. Price date for the card: 2026-10-17, the day it was added.

The [EST] monthly spend ($960) and the simulated board total below are **different examples**. Do not subtract one from the other.

### SIMULATED board (not [EST], not MEASURED)

From `docs/example-board/summary.json`, generated 2026-10-17, package 0.1.0, seed `20261017`. Not regenerated on 2026-10-22. Per-agent rows, means, and the rounded percentiles are in [COST.md](COST.md) and the README. Totals below are the integer fields in that JSON file.

| Scenario | Runs | Cost | Note |
| --- | ---: | ---: | --- |
| Fleet, 14 days (2026-10-04 through 2026-10-17) | 2016 | 34,851,655 micro-USD | README publishes this as $34.8517 at the simulated card |
| `refund-advisor`, full window, includes the planted spike day | 168 | 8,436,435 micro-USD | alerts: per-run cap, per-day cap |
| `refund-advisor`, planted day 2026-10-15 | 12 runs that day | 3,319,160 micro-USD | day total, not a per-run mean. Cap 1,200,000 micro-USD |
| `bulletin-draft`, full window | 168 | 4,437,160 micro-USD | p95 latency 5895.4 ms against SLO 2000 ms |

Quality is not scored. Latency in that file is the simulated `latency_ms` field.

## Measurement plan

Phases are [SCOPE.md](SCOPE.md). Only phase 0 is implemented.

| Stage | Work that exists here | Exit | Buyer confirmation |
| --- | --- | --- | --- |
| 0. This repo | Inventory, policy CLI, seeded board, ingest loader, invariant evals, kill switch, prompt rollback | **MEASURED 2026-10-22** against the same bars SCOPE.md recorded on 2026-10-17: pytest meets the 80% floor (see below); fleet policy exits 0 for `--today 2026-10-17`; violating inventory exits non-zero; `eval` exits 0; `eval-regression` exits non-zero. Demo cost is zero and uses no network, as COST.md states | A reader can re-run the commands in the README. That is the confirmation this repo supports |
| 1. Shadow on a real export | The loader exists (`--source ingested-runtime-evals`). A week of real traces does not | SCOPE.md: a human will open a board built from those traces. **UNVERIFIED** until that file exists | The buyer would compare the board to an invoice. This repo has no invoice |
| 2. Gate the high tier | The runtime check is a fixture and a CLI, not a deployed gate | SCOPE.md: a staged drill shows a rejected effect and a killed agent | Not run outside the fixture |
| 3. Alerts and access | Design only (SSO/RBAC, alert delivery, GRC export) | SCOPE.md: exit criteria belong to that future system | Not in this package |

**Pytest bar, MEASURED 2026-10-22.** Python 3.12.3, pytest 9.1.1, coverage 7.17.0, package 0.1.0. Command `python3 -m pytest --cov=governance_board --cov-report=term-missing --cov-fail-under=80`, with `branch = true` in `pyproject.toml`. **29 passed.** pytest-cov printed total coverage **90.09%** (JSON `percent_covered` 90.08776458440887). That total mixes statements and branches. Statement coverage on the same run: **93.158953722334%** (1389 of 1491 statements). Branch coverage: **79.82062780269058%** (356 of 446). The process printed `CoverageWarning: Module governance_board was previously imported, but not measured`. The percentages are the totals coverage wrote anyway. The 2026-10-17 record in METRICS.md is the same 29 passed and the same 90.09% total. It did not publish the statement split.

How a later team would measure the [EST] targets: count in-scope agents whose policy exits 0; record the clock time from a cap breach to a person opening the report; count high-tier rows with a backup; count external effects whose approval is not `approved`; count cost-spike incidents whose rollback version is in the registry. This repo does not contain those counts for a real fleet.

## Risks

Judgments below are the ones [RISKS.md](RISKS.md) already records. Probability words are that file's, not a new scale. The NIST AI RMF and EU AI Act table in that file is an educational map. It is not legal advice and not a certification.

| Risk | How RISKS.md rates it | What this repo does | What remains |
| --- | --- | --- | --- |
| High-tier agent with no human gate | Medium if the YAML is edited by hand. Impact high | Policy `high_risk_human_gate`. The violating fixture fails | A real change-control process. **UNVERIFIED** |
| No backup owner | Medium. Impact medium | Policy `high_risk_backup_owner` on high tier | Same |
| Stale review | High over a year. Impact medium | `review_fresh` against an injected clock | A workflow tool. Design only |
| Per-run cap above per-day cap | Low. Impact medium | `cap_consistency` | A finance rollup in monthly dollars. Not built |
| Cost spike | Planted so the alert can be shown. Not an observed incident | Aggregator alerts and the runbook | Whether anyone opens the report. The 1 day is [EST] |
| Latency SLO miss | Planted for `bulletin-draft` | `p95_latency_slo_breach` | Real latency. The board's latency is SIMULATED |
| Harmful effect or unapproved external effect | Low in the generator. The regression file includes one. Impact high | Invariants. The regression must fail | A real trace export. **UNVERIFIED** |
| Real provider turned on by accident | Low. Impact medium | Default off. Tests block sockets | Operator error outside CI |
| Secret committed | Low. Impact high | `secretscan` in CI. **MEASURED 2026-10-22:** the local scan reported zero findings | The scan is not a guarantee. SECURITY.md says so |
| YAML rewrite drops comments | High if you use the control CLI. Impact low | Commands default to a new file | A reviewer still has to read the diff |
| Board mistaken for a certification | Medium in a portfolio reading. Impact high | Disclaimer in the HTML and in RISKS.md | A reader who skips the disclaimer |
| Ingest mapping drops a field | Medium if a file uses a different shape | The loader rejects unknown fields | A real export. The sample is hand-written |

## MEASURED vs not

| Claim | Label |
| --- | --- |
| 29 tests passed on 2026-10-22, Python 3.12.3, pytest 9.1.1 | **MEASURED** |
| pytest-cov total 90.09%; statement coverage 93.158953722334%; branch coverage 79.82062780269058% | **MEASURED** the same run. The total is not line coverage alone |
| Fleet policy exit 0 with zero violations; violating inventory exit 1 with five violations; eval exit 0; regression exit 1 with three breaches; secret scan zero findings | **MEASURED 2026-10-22**, one run each. The 2026-10-17 README recorded the same exits |
| Example-board totals, the planted spike, and the latency percentiles | **SIMULATED**. File dated 2026-10-17. Not regenerated on 2026-10-22 |
| $80, $960, $40, $120, 30 days, 1 day, $2,320 | **[EST]** from BUSINESS_CASE.md |
| 5 and 15 micro-USD per token | **[EST]** rate card, not a vendor price |
| Provider cost of demo, tests, and CI is zero | Stated in COST.md because those commands do not call a paid API. The 2026-10-22 test run did not enable the real provider |
| Year-1 ROI, payback, labor rate, build cost, incidents per quarter, minutes saved | **UNVERIFIED**. Not in this repo. Not estimated here |
| A week of real traces, SSO, paging, a GRC export, answer quality | Not in this repo. Design only, or out of scope |
