"""Effect names the board knows about.

Harmful effects are refused even when a trace says they were approved.
External effects are allowed only with approval == "approved".
Anything else is treated as an internal draft effect.
"""

from __future__ import annotations

HARMFUL_EFFECTS: frozenset[str] = frozenset(
    {
        "transfer_funds",
        "delete_customer_record",
        "exfiltrate_data",
        "send_external_email",
        "provision_production_access",
    }
)

EXTERNAL_EFFECTS: frozenset[str] = frozenset(
    {
        "update_claim_file",
        "send_vendor_decision",
        "write_ledger_note",
        "update_schedule",
    }
)

ALLOWED_PROVIDERS: frozenset[str] = frozenset({"fake", "sim", "cassette"})
