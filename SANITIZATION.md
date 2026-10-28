# Privacy and provenance

Everything in this repository is written for the public [reference landing zone](https://github.com/stefpin/azure-landing-zone).
Resource and policy names are that repository's `alz-` names, identifiers are placeholders (`<your-subscription-id>`,
`<your-tenant-id>`, `$OWNER = "demo-owner"`), and the policy IDs are Microsoft's public built-in IDs. The repository
contains no customer, organisation, tenant or personal data, and no credentials: the runbook signs in with `az login` and
never needs a secret in a file.

## What is checked

Every text file is scanned (in CI by `tools/validate_repo.py`, and again before publication by additional scans) for
GUIDs, e-mail addresses, user-profile paths, IP addresses and secret patterns. The JSON is parsed and compared with the
here-strings in the runbook, every PowerShell file is parsed, the Markdown links are resolved, and the images and diagrams
were inspected. The documentation was also reviewed for context that scanners cannot see.

## What is not checked

A complete run of the runbook against a freshly deployed reference landing zone. See
[Appendix H](docs/runbook/appendix-h-dry-run-record.md) for what the dry run did and did not cover.

## Report a problem

If you find anything that should not be here, please open an issue (or contact the owner privately) so that it can be
removed.
