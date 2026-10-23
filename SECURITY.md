# Security

This is a portfolio repo of synthetic governance checks.

## Reporting

Report security issues through GitHub private vulnerability reporting. Open the Security tab on this repository and choose "Report a vulnerability". Do not include live credentials, customer data, or a real inventory in the report.

## Secrets

- Configuration is environment variables. See `.env.example`. The program does not load a `.env` file.
- Do not commit `.env`, keys, or tokens.
- CI runs `python3 -m governance_board secretscan`.
- A local run of that command on 2026-10-22 reported zero findings. One run. The scan looks for common token shapes. It is not a guarantee.
- The optional real provider is off unless `GOVERNANCE_REAL_PROVIDER_ENABLED=1` and a URL is set. CI does not enable it. Tests block outbound socket connects.

## What the checks cover

Inventory policy, effect invariants, and a static report. They do not authenticate users, authorize API calls, or protect a production network.

## Known limits

Rewriting YAML for the kill switch or a prompt rollback drops comments. The HTML report is a file on disk; it is not an authenticated app.
