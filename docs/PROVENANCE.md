# Provenance

The brief asked for a documented copy of eval helpers from the private repository `dlescanogithub/agent-runtime-evals`, commit `55cfd4183fb2489d77fc9c8552e008274dc78f77`, branch `cursor/agent-runtime-evals-mvp-7e58`.

This environment's GitHub credential received **HTTP 404** for that repository (clone and API). No file was copied from it. There is no NOTICE of third-party copyright because no code was taken.

What this repo implemented locally, following the brief's description of that template:

| Idea in the brief | Where it lives here |
| --- | --- |
| Cassette provider | `src/governance_board/providers/cassette.py` |
| Fake provider | `src/governance_board/providers/fake.py` |
| JSONL traces | `src/governance_board/trace.py` |
| JSON logging | `src/governance_board/logging_setup.py` |
| Secret scan | `src/governance_board/secretscan.py` |
| Invariant evals, not trajectories | `src/governance_board/evalkit/` |

`traces/runtime_evals_sample.jsonl` uses field names documented in `docs/architecture.md` (`trace_id`, nested `usage`, `tool_effects`). That sample is synthetic. It is **not** a verified dump of the other repo's format.

If the private repo becomes readable later, a follow-up should diff these modules against that commit and either replace them with a cited copy or record the drift here.
