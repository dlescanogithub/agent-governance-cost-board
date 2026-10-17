# Risk rubric

Internal rubric for this portfolio. It is not a legal category and not an EU AI Act class. See the disclaimer in `docs/RISKS.md`.

## Tiers

| Tier | Use it when |
| --- | --- |
| low | Read-only or internal drafts. No effect that leaves the system. No money movement. |
| medium | Internal confidential data or limited pseudonymous customer data. Drafts a human might later send. No autonomous external effect, unless a human gate is also declared. |
| high | Financial instruction, a recommendation a ledger might follow, or any effect that updates a system of record. |

Examples in the synthetic fleet: `kb-search` is low, `intake-triage` is medium, `refund-advisor` is high.

## Controls the policy enforces

| Control | low | medium | high |
| --- | --- | --- | --- |
| Non-empty owner | yes | yes | yes |
| Per-run and per-day caps, both > 0, per-run ≤ per-day | yes | yes | yes |
| SLO cost/run ≤ per-run cap | yes | yes | yes |
| `last_review` within `review_max_age_days` of the injected today | yes | yes | yes |
| `kill_switch` field (`engaged` requires `status: disabled`) | yes | yes | yes |
| Provider in `fake`, `sim`, `cassette` | yes | yes | yes |
| Non-empty `data_classes` | | yes | yes |
| Non-empty `eval_evidence` | | yes | yes |
| Backup owner, different from owner | | | yes |
| Required human gate enforced at `human_queue` or `runtime_effect_check` | | | yes |

A medium agent may still declare a human gate. `shift-suggester` does, because `update_schedule` is an external effect.

## Review clock

The fleet file sets `review_max_age_days: 90`. CI passes `--today 2026-10-17`.
