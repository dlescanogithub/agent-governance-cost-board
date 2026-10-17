# Provenance

Shared portfolio utilities live in this repo as small vendored copies, maintained in parallel and kept aligned:

| Utility | Where it lives here |
| --- | --- |
| Cassette provider | `src/governance_board/providers/cassette.py` |
| Invariant checks | `src/governance_board/evalkit/` |
| JSON traces | `src/governance_board/trace.py` and `src/governance_board/ingest.py` |
| Structured JSON logging | `src/governance_board/logging_setup.py` |
| Secret scan | `src/governance_board/secretscan.py` |

`src/governance_board/secretscan.py` is the vendored scanner. Keep that file identical across the portfolio repos. Its sha256 is the lock:

sha256: 24dd770a4ebc88eb13991110a9531adda4202145c7ab648681d1b656d0c33a5e

`make secretscan-hash` and `tests/test_secretscan.py` recompute that digest from the file bytes.

What this repo adds around those utilities: the inventory schema, policy-as-code, the seeded generator, the cost board, the kill switch, prompt rollback, and the runtime-evals JSONL loader. The loader's field list (run id, step, tokens in and out, cost in micro-USD, latency, outcome) matches the trace format used by `dlescanogithub/agent-runtime-evals`. The mapping is in `docs/TRACE_INGEST.md`. The sample under `traces/samples/` is hand-written.

Nothing in this repository is copied from employer or client work.
