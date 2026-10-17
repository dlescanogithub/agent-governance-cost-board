# Business case

Harborline Cooperative is fictional. Nothing here is a client invoice.

## Problem

Agents get built one by one. The owner, the backup, the human who may approve an external effect, and the daily cap sit in a doc that CI never reads. A cost spike shows up on a monthly bill. An unapproved write shows up in an incident channel.

## What this repo changes

The inventory is a file the policy command can fail. The board shows burn against the cap from traces. The runbook has a kill switch and a prompt version to roll back to. That is the whole implemented loop.

## ROI model [EST]

These figures are illustrative [EST]. They use the assumptions in the table. The simulated rate card in `traces/generation.yaml` is a separate example.

| Assumption | Value | Tag |
| --- | --- | --- |
| Agents in the fleet | 12 | matches the synthetic inventory count; the dollar rate does not |
| Model spend per agent per month | $80 | [EST] |
| Monthly fleet spend | $960 | [EST], 12 × 80 |
| Daily cap on the runaway agent | $40 | [EST] |
| Spend during a bad day | 3× cap = $120 | [EST]. The generator's planted spike is a separate illustrative example, not this model |
| Days until a monthly invoice would show it | 30 | [EST] |
| Days until the board shows it | 1 | [EST], if someone opens the report |
| Overrun avoided | 29 × ($120 − $40) = $2,320 | [EST] |

Round number used in the README: on the order of **$2,300** [EST] for one caught incident.

What would change the model: a real daily cap, a real invoice cycle, and a count of incidents per quarter. None of those are in this repo.

## Illustrative example, separate from the ROI

The example board is a **SIMULATED / illustrative example**. `traces/generation.yaml` plants `refund-advisor` at 3,319,160 micro-USD on 2026-10-15 against a 1,200,000 micro-USD cap (token multiplier 8). That is $3.3192 versus $1.2000 on the simulated rate card (5 and 15 micro-USD per token [EST]). It demonstrates the cap alert. It is not a measurement and not the ROI.

## Who pays attention

A fleet governor owns the policy file. Finance cares about the cap. The agent owner cares about the prompt version. A human in the queue owns the external effect. Adoption means those people can point at a file and a failing command, not at a slide.
