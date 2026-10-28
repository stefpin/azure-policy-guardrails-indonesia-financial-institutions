# Runbook: Azure Policy guardrails, step by step

This is the complete, beginner-friendly runbook. It tells you **exactly where to type or click** for every step: the PowerShell window, the Azure CLI, or a named page in the Azure Portal.

> [!IMPORTANT]
> This runbook builds on the public [reference landing zone](https://github.com/stefpin/azure-landing-zone). Deploy that first (or have an equivalent with the same names). Technical guidance only, not legal advice - see [`NOTICE.md`](../../NOTICE.md).

> [!NOTE]
> **Status.** The commands of Parts 1 to 4 (including the optional step 4.9) and Part 5 Level 1 were run end to end once, in Azure Cloud Shell with Azure CLI 2.91 (October 2026). The Portal (Option B) boxes, Test 10 and Part 5 Levels 2 to 4 have **not** been run. The expected counts are *measured* values from that one run, on an environment of the same design. Changes made after the run to generalise the runbook are listed in [Appendix H](appendix-h-dry-run-record.md) and have not been tested end to end.

## Contents

| Part | What you do | Time |
| --- | --- | --- |
| [Part 0 - Before you start](00-before-you-start.md) | Understand what the runbook is, the environment you start from, the safety rules, cost, and Azure Policy in ten minutes | 20 min reading |
| [Part 1 - Prepare the stage](01-prepare-the-stage.md) | Sign in, set variables, create a small lab, build the policy library (5 custom definitions, 3 initiatives, 38 rules) | 60 - 90 min |
| [Part 2 - Chapter 1: PREVENT](02-chapter-1-prevent.md) | Switch on enforcement in the lab and watch nine unsafe actions be refused; preview the impact on production | 45 min |
| [Part 3 - Chapter 2: DETECT](03-chapter-2-detect.md) | Audit the real application: 11 findings, each explained | 30 min |
| [Part 4 - Chapter 3: REMEDIATE and PROVE](04-chapter-3-remediate-and-prove.md) | Fix tags and diagnostics automatically, back up a VM by tag, record exemptions, show the scorecard | 45 min |
| [Part 5 - Wrap-up, reset and clean-up](05-wrap-up-and-clean-up.md) | The evidence table and four levels of clean-up | 15 min |
| [Part 6 - Troubleshooting](06-troubleshooting.md) | Symptom, cause, fix | as needed |

| Appendix | What it holds |
| --- | --- |
| [A - Everything this runbook creates](appendix-a-everything-this-runbook-creates.md) | Every object it creates and the level that removes it |
| [B - Policy catalogue](appendix-b-policy-catalogue.md) | All 38 rules with their definition IDs |
| [C - Inherited policies: what to look for](appendix-c-inherited-policies.md) | Why a test may behave differently in your tenant |
| [D - Glossary](appendix-d-glossary.md) | Plain-words definitions |
| [E - One-page crib sheet](appendix-e-crib-sheet.md) | The whole demo on one page |
| [F - What was verified, and how](appendix-f-what-was-verified.md) | How much trust the numbers deserve |
| [G - Sources](appendix-g-sources.md) | Microsoft Learn pages and related repositories |
| [H - Dry-run record and known limitations](appendix-h-dry-run-record.md) | What the dry run observed, the ten corrections, what is not verified |

## How to use this runbook

Read Part 0 once. Then follow Parts 1 to 5 **in order**. Do not skip a part: later parts need things that earlier parts create. Every step has the same shape, so you always know what to do next.

> **Where to do this:** this box tells you **where** to do the step - for example the PowerShell window, a page in the Azure Portal, or the Windows Terminal. Read it first.

```powershell
# This is a code block. Copy the whole block, paste it into the window named in the "Where to do this" line,
# then press Enter. Lines that start with # are comments - they are only notes for you.
```

> **What you should see**
>
> This box shows what you should see if the step worked. If your screen is different, stop and look at Part 6 (Troubleshooting).

> **What to say**
>
> A short talk track you can say to the audience while the step runs.

> [!NOTE]
> Extra information or an important difference you should know about.

> [!TIP]
> A shortcut, or an idea that makes the demonstration clearer.

> [!WARNING]
> A mistake that real people make, or a behaviour that looks like a bug but is not.

> [!CAUTION]
> Something that can cost money, break a running service or cannot be undone. Read it before you press Enter.

### Rules for copying commands

- **Copy the whole block** unless the text says otherwise. Many blocks depend on earlier lines in the same block.
- A line that ends with a **backtick** (the `` ` `` character, usually left of the number 1 key) continues on the next line. Do not add spaces after the backtick.
- PowerShell **here-strings** (text between `@'` and `'@`, or between `@"` and `"@`) must have the closing marker at the very **start** of its line, with no spaces before it.
- All code blocks use plain straight quotes and plain hyphens, so they are safe to paste. If you retype a command by hand, use the same characters.
- Names such as `$SUB` and `$RG_LAB` are **PowerShell variables** that you create once in step 1.2, and the helper commands (`Show-Assignments`, `Test-SampleApp` and so on) come from the **first block of step 1.3**. If you close the PowerShell window, run those two blocks again - and only those: the rest of step 1.3 would overwrite your 'before' evidence.
- Times such as [about 3 min] are estimates from the Azure documentation and the size of the resources. Your numbers can differ.

### The two places you will work

| Place | How to open it | What you do there |
| --- | --- | --- |
| **PowerShell window** | Windows Terminal (press the Windows key, type **Terminal**, make sure the tab says **PowerShell**), or Azure Cloud Shell (PowerShell) | Type or paste Azure CLI (`az`) and PowerShell commands. This is the fast, repeatable way. |
| **Azure Portal** | https://portal.azure.com in your browser, signed in with the account from step 1.1 | Look at results (compliance, remediation, resource settings), take screenshots, and - where the text says so - click through the same action the commands perform. |

### Scripts

The code blocks of Parts 1 to 5 are also available as PowerShell files in [`scripts/`](../../scripts/). They are **generated from these pages** and meant to be run **block by block**, not as one script - Chapter 1 contains commands that Azure is *supposed to refuse*. See [`scripts/README.md`](../../scripts/README.md).
