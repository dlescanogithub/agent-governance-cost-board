# Discovery

Ten questions to ask before copying this board into a real team. Harborline answers are the ones baked into this repo. A different answer changes the design.

1. **Who owns the agent when the builder leaves?**
   Harborline stores a role id (`finance-ops`), not a person. If the answer is "a named person", the inventory needs a joiner/leaver update that this repo does not have.

2. **Who is the backup?**
   High tier requires a different role. If the org has no backup, the policy fails closed. If backups are optional even for high tier, delete rule `high_risk_backup_owner` and accept the gap in writing.

3. **Which effects leave the system?**
   The external set is a Python frozenset. A new effect name is internal until someone adds it. Discovery has to list writes, sends, and deletes. If that list is unknown, start in shadow and do not turn on the gate.

4. **What is high risk here?**
   The rubric is in `docs/RISK_RUBRIC.md`. If "high" means "uses a large model" rather than "can change a system of record", the tier matrix is the wrong control.

5. **What is an acceptable per-run and per-day cap?**
   Caps here are integers in micro-USD. If finance speaks in monthly dollars, add a rollup. The policy only checks per-run ≤ per-day and SLO cost ≤ per-run.

6. **Who approves, and how fast?**
   Gates are declared as `human_queue` or `runtime_effect_check`. This repo does not implement the queue. If approval must happen in under a minute, the design needs a real queue and a timeout. That is out of scope.

7. **What data classes are in play?**
   Medium and high tiers must list at least one. If the real classes include secrets or payment data, the trace schema must stay free of payloads, as it does here. Do not log the document.

8. **How fresh is a review?**
   Default 90 days, clock injected. If audit wants 30, change `review_max_age_days`. If they want a workflow tool, this YAML date is only the shadow.

9. **What does rollback mean?**
   Here it means "mark an older prompt version as current and point the inventory at it." If rollback means "shift traffic" or "restore a database", the command in this repo is the wrong tool.

10. **What evidence does audit actually want?**
    Today: the inventory file, the JSONL, and `summary.json`. If they want a GRC export, that is design-only (`docs/SCOPE.md`). If they want legal sign-off, this repo is not that sign-off.
