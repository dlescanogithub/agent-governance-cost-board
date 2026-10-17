# Example board

**SIMULATED / illustrative example.** Not a measurement.

The spend spike for `refund-advisor` is planted in `traces/generation.yaml` (`spike.token_multiplier`). The slow `bulletin-draft` latency profile is planted there too. The page demonstrates policy-as-code, budget caps, the kill switch, and prompt rollback.

| Field | Value |
| --- | --- |
| Date label | 2026-10-17 |
| Package | 0.1.0 (`python3 -m governance_board version`) |
| Python | 3.12.3 |
| Source named in the header | `simulated-generator` |
| Events | 2016 |
| Seed | 20261017 |
| Window | 2026-10-04 through 2026-10-17 (14 days, 12 runs per agent per day) |
| Alerts on this illustrative file | 3 (see `summary.json`) |
| Rate card | 5 micro-USD per input token, 15 per output token, simulated [EST], not a vendor price |

Commands that produced `traces/fleet.jsonl`, `traces/fleet.meta.json`, `index.html`, `report.md`, and `summary.json`:

```bash
python3 -m governance_board generate-traces \
  --inventory inventory/fleet.yaml \
  --profile traces/generation.yaml \
  --out traces/fleet.jsonl

python3 -m governance_board report \
  --inventory inventory/fleet.yaml \
  --traces traces/fleet.jsonl \
  --out docs/example-board \
  --generated-on 2026-10-17 \
  --source simulated-generator
```

Git commits:

- `traces/fleet.jsonl` and `traces/fleet.meta.json` (unchanged in the review): `e54858f7621d9d438eea380cd4c90173abc6fb5f`
- `docs/example-board/index.html`, `report.md`, and `summary.json`, regenerated with `--source simulated-generator`: `c3201af7345b24152264015f3b90b2b0b57de95c`

This stamp file is a later commit. Regenerating the board needs this stamp updated.

Do not hand-edit the HTML. A test compares `traces/fleet.jsonl` to a fresh generator run.
