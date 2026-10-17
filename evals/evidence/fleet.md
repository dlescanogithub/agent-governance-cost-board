# Eval evidence links (synthetic)

These anchors are the evidence links stored on the Harborline Cooperative inventory.
They point at the invariant suite in this repo. They are not a production evaluation report.

## intake-triage

Covered by `evals/suite.yaml` (no harmful effect, cost within cap, no unapproved external action) and by the policy gate.

## claim-draft

External effect `update_claim_file` is allowed only with `approval: approved`. See `src/governance_board/evalkit/invariants.py`.

## kb-search

Read-only effect `retrieve_kb_passage`. Case `internal_draft_within_cap`.

## invoice-extract

Draft effect only. No external effect in the generator profile.

## meeting-notes

Draft effect only.

## change-review

Draft effect only. The agent does not merge or deploy.

## vendor-screener

External effect `send_vendor_decision` requires approval.

## onboarding-coach

Draft effect only.

## refund-advisor

External effect `write_ledger_note` requires approval. The synthetic spike is an alert on the board, not a passed cost-cap eval.

## bulletin-draft

Draft effect only. Latency SLO is expected to breach in the sample window.

## shift-suggester

External effect `update_schedule` requires approval.

## safety-checklist

Draft effect only.

## high-ungated

Fixture id used by `inventory/violating.yaml`. Not a passing agent.

## cap-broken

Fixture id used by `inventory/violating.yaml`. Not a passing agent.
