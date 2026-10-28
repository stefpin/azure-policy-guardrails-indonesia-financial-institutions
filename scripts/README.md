# Scripts

The PowerShell of the [runbook](../docs/runbook/README.md), as files. They are **generated from the runbook pages** by
[`tools/extract_scripts.py`](../tools/extract_scripts.py) (CI fails if they drift), so the page is always the source of
truth.

> [!WARNING]
> **Do not run these files as one script.** Run them **block by block** (select a block and press F8 in VS Code or the
> PowerShell ISE, or paste it into the terminal). Chapter 1 contains commands that Azure is *supposed to refuse*, some
> steps need you to wait for Azure Policy, and every step has a result you should read before you go on. The page explains
> each step.

| File | What it holds | Page |
|---|---|---|
| [`00-variables.ps1`](00-variables.ps1) | The variable block. **Edit `$SUB` and `$OWNER` first.** Dot-source it in every new PowerShell window | [1.2](../docs/runbook/01-prepare-the-stage.md) |
| [`01-helpers.ps1`](01-helpers.ps1) | `Show-Assignments`, `Show-Enforcing`, `Show-Remediation`, `Show-Compliance`, `Show-Scorecard`, `Test-SampleApp` | [1.3](../docs/runbook/01-prepare-the-stage.md) |
| [`10-part1-prepare-the-stage.ps1`](10-part1-prepare-the-stage.ps1) | Sign in, the lab, the policy library (5 custom definitions, 3 initiatives), the pre-flight checks | [Part 1](../docs/runbook/01-prepare-the-stage.md) |
| [`20-part2-chapter1-prevent.ps1`](20-part2-chapter1-prevent.ps1) | Chapter 1: assign, switch enforcement on, the nine tests, the production what-if | [Part 2](../docs/runbook/02-chapter-1-prevent.md) |
| [`30-part3-chapter2-detect.ps1`](30-part3-chapter2-detect.ps1) | Chapter 2: assign the audit initiative and read the findings | [Part 3](../docs/runbook/03-chapter-2-detect.md) |
| [`40-part4-chapter3-remediate.ps1`](40-part4-chapter3-remediate.ps1) | Chapter 3: identities and roles, remediation tasks, backup by tag, exemptions, scorecard | [Part 4](../docs/runbook/04-chapter-3-remediate-and-prove.md) |
| [`50-part5-cleanup.ps1`](50-part5-cleanup.ps1) | Level 1 (safe state) to Level 4 (undo production changes), switch off the expensive parts | [Part 5](../docs/runbook/05-wrap-up-and-clean-up.md) |

## Quick use

```powershell
# 1. Open 00-variables.ps1, set $SUB and $OWNER, then:
. ./scripts/00-variables.ps1
. ./scripts/01-helpers.ps1

# 2. Open 10-part1-prepare-the-stage.ps1 and run it block by block, then Part 2, 3, 4 and 5 in order.
```

The scripts need the same things as the runbook: Azure CLI 2.88 or newer, Owner on the subscription, and the
[reference landing zone](https://github.com/stefpin/azure-landing-zone). **Level 1 of `50-part5-cleanup.ps1` is safe at
any time**: it switches every enforcing assignment back to `DoNotEnforce`.
