# Measured example board

Label: **simulated**.

| Field | Value |
| --- | --- |
| Date | 2026-10-17 |
| Package | 0.1.0 (`python3 -m governance_board version`) |
| Python | 3.12.3 |
| Events | 2016 |
| Seed | 20261017 |
| Window | 2026-10-04 through 2026-10-17 (14 days, 12 runs per agent per day) |
| Alerts | 3 (see `summary.json`) |
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
  --generated-on 2026-10-17
```

Git commit that added these artifacts: `STAMP_AFTER_COMMIT`.

Do not hand-edit the HTML. Regenerate it with the commands above. A test compares `traces/fleet.jsonl` to a fresh generator run.
