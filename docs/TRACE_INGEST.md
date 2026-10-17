# Trace ingest

The board renders from one of two JSONL inputs. The HTML and Markdown header states which one.

| `--source` | Meaning |
| --- | --- |
| `simulated-generator` | Seeded file from `governance_board.generate`. Illustrative example. |
| `ingested-runtime-evals` | File in the runtime-evals trace shape, loaded by `governance_board.ingest`. |

## Simulated generator

Native events, one JSON object per line:

| Field | Type | Notes |
| --- | --- | --- |
| `run_id` | string | |
| `agent_id` | string | Inventory id |
| `version` | string | Prompt version on that run |
| `ts` | string | ISO-8601 |
| `status` | `ok` \| `error` \| `rejected` | |
| `tokens_in`, `tokens_out` | int >= 0 | |
| `cost_micro_usd` | int >= 0 | Simulated rate card |
| `latency_ms` | int >= 0 | |
| `approval` | `none` \| `approved` \| `rejected` | |
| `effects` | string[] | Names, not payloads |

`traces/fleet.jsonl` is this shape. `traces/generation.yaml` plants a spend spike (`spike.token_multiplier` on `refund-advisor`) and a slow latency profile on `bulletin-draft`. Figures from that file are a **SIMULATED / illustrative example**. They show the cap and SLO alerts. They are not a measurement.

## Runtime-evals JSONL

Aligned with the trace format of `dlescanogithub/agent-runtime-evals`: run id, step, tokens in, tokens out, cost in micro-USD, latency, outcome.

Loader: `load_runtime_evals` in `src/governance_board/ingest.py`.

Required fields and the mapping onto a board event:

| Runtime-evals field | Type | Board field |
| --- | --- | --- |
| `run_id` | non-empty string | `run_id` |
| `step` | non-empty string | `agent_id` |
| `tokens_in` | int >= 0 | `tokens_in` |
| `tokens_out` | int >= 0 | `tokens_out` |
| `cost_micro_usd` | int >= 0 | `cost_micro_usd` |
| `latency_ms` | int >= 0 | `latency_ms` |
| `outcome` | string, see below | `status` |

`outcome` maps to `status` as follows:

| `outcome` | `status` |
| --- | --- |
| `ok`, `success` | `ok` |
| `error`, `failure`, `failed` | `error` |
| `rejected` | `rejected` |

Optional fields:

| Field | Rule |
| --- | --- |
| `ts` | ISO-8601. If absent, the loader uses the clock passed in (the report command uses `--generated-on` at 12:00). |
| `agent_id` | If present, it must equal `step`. |
| `version` | Non-empty string. Default `unknown`. |
| `approval` | `none`, `approved`, or `rejected`. Default `none`. |
| `effects` | List of strings. Default `[]`. |

Any other key is an error. Blank lines and lines whose first non-space character is `#` are skipped. A file with no events is an error.

`normalize_raw` in `governance_board.trace` still accepts a looser local shape (`trace_id`, nested `usage`, `tool_effects`). That path is not the runtime-evals contract and is not what `--source ingested-runtime-evals` reads.

## Hand-written sample

`traces/samples/runtime_evals_sample.jsonl` is a **SAMPLE**. The first line says so. It is written by hand. It is not a capture and not generator output.

```bash
python3 -m governance_board report \
  --inventory inventory/fleet.yaml \
  --traces traces/samples/runtime_evals_sample.jsonl \
  --out /tmp/ingested-board \
  --generated-on 2026-10-17 \
  --source ingested-runtime-evals
```

The header of that page reads `Source: ingested runtime-evals JSONL`.
