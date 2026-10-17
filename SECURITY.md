# Security

This is a portfolio repo of synthetic governance checks. It is private until the owner publishes it.

## Reporting

Open a private GitHub issue on this repository, or contact the owner through GitHub (`dlescanogithub`). Do not include live credentials, customer data, or a real inventory in the report.

## Secrets

- Configuration is environment variables. See `.env.example`. The program does not load a `.env` file.
- Do not commit `.env`, keys, or tokens.
- CI runs `python3 -m governance_board secretscan`.
- The scan looks for common token shapes. It is not a guarantee.
- The optional real provider is off unless `GOVERNANCE_REAL_PROVIDER_ENABLED=1` and a URL is set. CI does not enable it. Tests block outbound socket connects.

## What the checks cover

Inventory policy, effect invariants, and a static report. They do not authenticate users, authorize API calls, or protect a production network.

## Known limits

Rewriting YAML for the kill switch or a prompt rollback drops comments. The HTML report is a file on disk; it is not an authenticated app.
