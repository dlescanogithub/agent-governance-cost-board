# Architecture

Harborline Cooperative is fictional. Traces are simulated.

## Pieces

| Piece | Module | Role |
| --- | --- | --- |
| Inventory loader | `governance_board.inventory` | YAML to typed records, after JSON Schema |
| Policy | `governance_board.policy` | Tier matrix, caps, review age, prompt version |
| Generator | `governance_board.generate` | Seeded JSONL, no network |
| Traces | `governance_board.trace` | Native events plus a small alternate shape |
| Aggregator | `governance_board.aggregate` | Cost, latency, approval, alerts |
| Report | `governance_board.report` | One HTML file, one Markdown file, `summary.json` |
| Evals | `governance_board.evalkit` | Invariants over events |
| Providers | `governance_board.providers` | Fake and cassette on by default; real HTTP off |
| Controls | `governance_board.controls` | Kill switch and prompt rollback |
| Secret scan | `governance_board.secretscan` | Local pattern scan |

Logging is JSON on stderr (`governance_board.logging_setup`). Retries exist for the optional real provider (`governance_board.retry`): max attempts and a backoff cap. The default path does not retry because it does not call the network.

## Trace schema (native)

One JSON object per line:

| Field | Type | Notes |
| --- | --- | --- |
| `run_id` | string | |
| `agent_id` | string | Matches an inventory id when the trace is from this fleet |
| `version` | string | Prompt/agent version at the time of the run |
| `ts` | string | ISO-8601 UTC |
| `status` | `ok` \| `error` \| `rejected` | |
| `tokens_in`, `tokens_out` | int | Simulated counts |
| `cost_micro_usd` | int | Simulated |
| `latency_ms` | int | Simulated |
| `approval` | `none` \| `approved` \| `rejected` | |
| `effects` | string[] | Names, not payloads |

## Alternate shape

`normalize_raw` also accepts a flatter export some local eval harnesses use: `trace_id`, `agent`, `agent_version`, `timestamp`, `outcome` (`success`/`failure`), `usage.prompt_tokens`, `usage.completion_tokens`, `cost.micro_usd`, `elapsed_ms`, `human_approval`, `tool_effects`. A sample lives in `traces/runtime_evals_sample.jsonl`.

That map was **not** checked against the private repo named in the brief. This environment got HTTP 404 for that repo. See `docs/PROVENANCE.md`.

## Effects

External effects (`update_claim_file`, `send_vendor_decision`, `write_ledger_note`, `update_schedule`) require `approval: approved`.

Harmful names (`transfer_funds`, `delete_customer_record`, `exfiltrate_data`, `send_external_email`, `provision_production_access`) fail the invariant even if a trace marks them approved. The generator never emits them. The regression fixture does, so the gate can go red.

## Percentiles

`governance_board.stats.percentile` uses linear interpolation between nearest ranks. p50 and p95 in the board use that definition.

## Clocks

`--today` / `GOVERNANCE_TODAY` is the review clock. The default in code is `2026-10-17` so a clean shell matches the checked-in fleet. Report timestamps use `--generated-on`, not the wall clock, so the HTML is reproducible.

## Providers

| Name | When |
| --- | --- |
| `fake` | Default. Deterministic string, no network |
| `cassette` | Replays a JSON file keyed by SHA-256 of the prompt |
| `sim` | Allowed as an inventory provider label. The generator does not call it |
| `real` | `GOVERNANCE_REAL_PROVIDER_ENABLED=1` and `GOVERNANCE_REAL_PROVIDER_URL`. Off in CI. Evals refuse to start if the settings are not offline |
