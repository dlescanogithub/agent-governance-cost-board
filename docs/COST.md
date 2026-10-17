# Cost

Every dollar figure from the generator is **simulated**. The rate card is not a vendor price.

| Rate | Value | Source |
| --- | --- | --- |
| Input | 5 micro-USD per token | `traces/generation.yaml`, written 2026-10-17, [EST] |
| Output | 15 micro-USD per token | same file, [EST] |
| 1 USD | 1,000,000 micro-USD | convention used by the report |

Price date: 2026-10-17, the day the card was added to this repo. No public price page was copied.

Latency in the table is simulated `latency_ms`. The p50/p95 numbers are the aggregator's printout of the seeded generator, dated 2026-10-17, package 0.1.0, command in `docs/example-board/EXAMPLE.md`. **SIMULATED / illustrative example.** The spike and the slow agent are planted in `traces/generation.yaml`. Quality is not scored.

| Scenario | Model / provider | Tokens or units | Cost/run | p50 / p95 latency | Quality | Price date / source |
| --- | --- | --- | --- | --- | --- | --- |
| intake-triage, full window | sim-small / sim | 168 simulated runs | mean 10,800.6 micro-USD | 626.0 / 919.9 ms | not scored | 2026-10-17, simulated card [EST], illustrative |
| refund-advisor, full window (includes the planted spike day) | sim-balanced / sim | 168 simulated runs | mean 50,216.9 micro-USD | 1,100.0 / 1,761.2 ms | not scored | 2026-10-17, simulated card [EST], illustrative |
| refund-advisor, planted spike day 2026-10-15 | sim-balanced / sim | 12 runs that day | day total 3,319,160 micro-USD (not a per-run mean) | (window p95 above) | not scored | planted `token_multiplier`, illustrative |
| bulletin-draft, full window | sim-small / sim | 168 simulated runs | mean 26,411.7 micro-USD | 2,905.5 / 5,895.4 ms | not scored | planted slow profile, illustrative |
| Fleet, 14 days | mixed sim-small and sim-balanced | 2016 runs | total 34,851,655 micro-USD | per agent in the README | not scored | 2026-10-17, simulated card [EST], illustrative |

Means and percentiles are rounded to 1 decimal from `docs/example-board/summary.json`. Totals are exact integers from that file.

The ROI dollars in `docs/BUSINESS_CASE.md` are a separate [EST] model. They do not use this rate card.

Running the demo, the tests, or CI does not call a paid API. Cost of those commands: zero.
