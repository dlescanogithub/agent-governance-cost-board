# Architecture

Harborline Cooperative is fictional. The checked-in fleet file is a seeded generator run: a **SIMULATED / illustrative example**. The board can also render an ingested JSONL file, and the header says which input it used.

## Pieces

| Piece | Module | Role |
| --- | --- | --- |
| Inventory loader | `governance_board.inventory` | YAML to typed records, after JSON Schema |
| Policy | `governance_board.policy` | Tier matrix, caps, review age, prompt version, owner, risk tier |
| Generator | `governance_board.generate` | Seeded JSONL, no network. Plants the spike used on the example board |
| Traces | `governance_board.trace` | Native events, plus a looser local shape via `normalize_raw` |
| Ingest | `governance_board.ingest` | Runtime-evals JSONL: run id, step, tokens, cost, latency, outcome |
| Aggregator | `governance_board.aggregate` | Cost, latency, approval, cap and SLO alerts |
| Report | `governance_board.report` | One HTML file, one Markdown file, `summary.json`. Header names the source |
| Evals | `governance_board.evalkit` | Hand-written cases plus seeded property checks |
| Providers | `governance_board.providers` | Fake and cassette on by default; real HTTP off |
| Controls | `governance_board.controls` | Kill switch and prompt rollback |
| Secret scan | `governance_board.secretscan` | Vendored pattern scan. Hash in `docs/PROVENANCE.md` |

Logging is JSON on stderr (`governance_board.logging_setup`). Retries exist for the optional real provider (`governance_board.retry`): max attempts and a backoff cap. The default path does not retry because it does not call the network.

## Trace schemas

Native generator fields and the runtime-evals mapping are in [TRACE_INGEST.md](TRACE_INGEST.md).

`normalize_raw` also accepts a looser local export: `trace_id`, `agent`, `agent_version`, `timestamp`, `outcome` (`success`/`failure`), `usage.prompt_tokens`, `usage.completion_tokens`, `cost.micro_usd`, `elapsed_ms`, `human_approval`, `tool_effects`. That helper is not the ingest contract. `--source ingested-runtime-evals` rejects unknown keys.

The hand-written sample is `traces/samples/runtime_evals_sample.jsonl`. The first line labels it SAMPLE.

## Effects

External effects (`update_claim_file`, `send_vendor_decision`, `write_ledger_note`, `update_schedule`) require `approval: approved`.

Harmful names (`transfer_funds`, `delete_customer_record`, `exfiltrate_data`, `send_external_email`, `provision_production_access`) fail the invariant even if a trace marks them approved. The generator never emits them. The regression fixture does, so the gate can go red.

## Property checks

`python3 -m governance_board eval` runs the YAML cases and then `run_property_checks` (seed `20261017`, 32 trials): a cost over the cap is flagged and a cost equal to the cap is not; an engaged kill switch blocks; rollback restores the previous prompt version; an agent with an empty owner or a missing risk tier fails policy. `eval-regression` does not run those properties. It fails on the bad YAML case, and CI asserts that failure.

## Percentiles

`governance_board.stats.percentile` uses linear interpolation between nearest ranks. p50 and p95 in the board use that definition.

## Clocks

`--today` / `GOVERNANCE_TODAY` is the review clock. The default in code is `2026-10-17` so a clean shell matches the checked-in fleet. Report timestamps use `--generated-on`, not the wall clock, so the HTML is reproducible. Ingested rows with no `ts` use that date at 12:00.

## Providers

| Name | When |
| --- | --- |
| `fake` | Default. Deterministic string, no network |
| `cassette` | Replays a JSON file keyed by SHA-256 of the prompt |
| `sim` | Allowed as an inventory provider label. The generator does not call it |
| `real` | `GOVERNANCE_REAL_PROVIDER_ENABLED=1` and `GOVERNANCE_REAL_PROVIDER_URL`. Off in CI. Evals refuse to start if the settings are not offline |
