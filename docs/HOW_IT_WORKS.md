# How it works

Walkthrough for engineers and buyers. The data is simulated. Harborline Cooperative is fictional.

## What it is for

The model reasons, but trust comes from the system around it. This repo is that system, at a small scale. It has an inventory of 12 agents, rules that run in CI, synthetic JSONL traces, and a static HTML board of cost and latency.

It does not serve anyone. It does not call a paid provider. If you run it on your machine, the cost is zero.

## Analogy

Take a building superintendent. They do not live in each apartment. They keep a sheet: who is responsible, who covers them, and which apartments need a signature before anyone touches the gas valve. They have a meter. If the meter spikes, they do not argue with the pipe: they shut the valve and write down which version of the faucet was installed.

Here the sheet is `inventory/fleet.yaml`. The meter is the trace aggregator. The valve is the kill switch. The faucet version is the prompt registry.

## Step by step

1. **Inventory.** Each agent has an id, an owner, a backup owner, a version, a simulated model, a purpose, data classes, a tier (low, medium, high), approval gates, budget caps, an SLO, and a last-review date. The JSON schema rejects a malformed file.

2. **Policy.** `python3 -m governance_board policy` reads the inventory and the prompt registry. A high-tier agent with no human gate, or with no distinct backup owner, fails. A per-run cap larger than the daily cap fails. A review older than N days fails. Today's date is injected (`--today` or `GOVERNANCE_TODAY`) so the check is reproducible.

3. **Fixture that must fail.** `inventory/violating.yaml` is valid for the schema and invalid for the policy. CI requires that command to exit with a non-zero code.

4. **Simulated traces.** The generator uses a fixed seed and writes JSONL: run, agent, version, time, status, tokens, cost in micro-USD, latency, approval, and effects. The numbers come from a simulated rate card, not from a provider. The `refund-advisor` spike is planted in `traces/generation.yaml` (`token_multiplier`). It is an illustrative example meant to show the cap. It is not a measurement.

5. **Ingest.** The board also reads a JSONL file in the runtime-evals schema: `run_id`, `step`, input and output tokens, cost in micro-USD, latency, and `outcome`. The mapping is in `docs/TRACE_INGEST.md`. The sample in `traces/samples/` is hand-written and says SAMPLE. The HTML header says whether the numbers come from the generator or from that file.

6. **Aggregator.** For each agent it computes cost, latency p50/p95, the human-approval rate, the rejection rate, and daily-cap burn. If a day goes over the cap, or if p95 goes over the SLO, it records an alert.

7. **Board.** One HTML file with CSS and SVG charts inside it, plus a Markdown file. There is no CDN and no network. The header names the source.

8. **Evals.** They do not look at the exact tool sequence. They look at invariants: no harmful effect, cost within the cap, no external effect without `approval: approved`. In addition, `eval` runs seeded properties: a cost above the cap is always flagged, an engaged kill switch always blocks, rollback returns to the previous prompt version, and an agent with no owner or no tier does not pass policy. `eval-regression` runs a bad case and **must fail**. CI checks that failure.

9. **Cost incident.** The runbook stops the agent (`kill-switch`) and returns the prompt to a previous version (`rollback`). The example spike is planted so that path can be practiced.

## What was measured

On 2026-10-22, with Python 3.12.3, pytest 9.1.1, coverage 7.17.0, and package 0.1.0, the command was:

`python3 -m pytest --cov=governance_board --cov-report=term-missing --cov-fail-under=80`

29 tests passed. pytest-cov printed total coverage of 90.09%. The project measures branches, so that total mixes statements and branches. In the JSON from the same run, statement coverage (line coverage) was 93.158953722334%: 1389 of 1491. Branch coverage was 79.82062780269058%: 356 of 446. The process warned that the module was already imported and was not measured again. The percentages are the ones coverage wrote anyway. The 2026-10-17 record stated the same 29 and the same 90.09%, without splitting out statements.

The same day, with `--today 2026-10-17`: fleet policy exited 0 with zero violations; `inventory/violating.yaml` exited 1 with five violations; `eval` exited 0 (3 cases and 32 property trials, zero breaches); `eval-regression` exited 1 with three breaches on one event. The secret scan found nothing. One run each. The example board was not regenerated that day: it is still the simulated file from 2026-10-17.

The value plan is in `docs/BUSINESS_VALUE.md`. It repeats the [EST] model from `docs/BUSINESS_CASE.md`. It does not add another dollar figure.

## Glossary

| Word | What it means here |
| --- | --- |
| Tier | Internal rubric: low, medium, or high. It is not a legal category. |
| Gate | A human has to approve before an effect that leaves the system. |
| Effect | Something the run says it did, for example writing a ledger note. |
| micro-USD | One millionth of a dollar. 1,000,000 micro-USD = 1 USD in this convention. |
| SLO | A p95 latency target and a cost-per-run target. In this repo the SLO numbers are [EST] and the latency numbers are simulated. |
| Kill switch | An inventory field. Engaged means `status: disabled`. |
| Cassette | A recorded response from a fake provider. It keeps the run off the network. |

## Honest limits

- It certifies nothing. The map to NIST and to the EU AI Act is study material. See `docs/RISKS.md`.
- It does not score whether an answer is good. It checks gates. The example cost and latency are simulated.
- It does not page anyone. The alert stays in the HTML.
- There are no users and no permissions.
- The generator is not real traffic. If you change the seed, the numbers change.
- Rewriting the YAML with the kill switch or with rollback can drop comments.

This did not run in production. It ran in this repository, on synthetic data, and the command is in the README.
