# Appendix H - Dry-run record and known limitations

[Runbook index](README.md) &middot; Previous: [Appendix G - Sources](appendix-g-sources.md)

The first draft of the runbook was written without running its commands against Azure. The first end-to-end dry run then led to ten corrections. The *Observed* column records what happened. Use the same table to record your own run.

### How dry run 1 was run

- **Environment:** Azure Cloud Shell (PowerShell 7), Azure CLI 2.91, a browser, an account with Owner on the subscription and multi-factor authentication. Cloud Shell runs on Linux, so paths were typed with forward slashes, which is why this runbook uses them everywhere.
- **Scope:** Parts 1 to 4 including optional 4.9, then Part 5 Level 1 only. Levels 2 to 4, step 5.6 and the Portal (Option B) boxes were **not** run.
- **Start state:** the Application Gateway and PostgreSQL were already running, so the start commands in step 1.4 were skipped.
- **Backup helper group:** during step 4.6 the vault's `DefaultPolicy` was given an instant-restore resource-group prefix, so Azure Backup named its helper group after that prefix.
- **After Level 1:** all 11 `alz-pd-` assignments were `DoNotEnforce`; the lab held 15 resources; the policy library, the 4 exemptions, the Owner tags and the 4 diagnostic settings were still in place.

### Dry-run checklist with the observed results

| Check during the dry run | Expected (before the dry run) | Observed in dry run 1 |
| --- | --- | --- |
| Probe in 2.3: how many attempts until Deny is active | 1 to 8 attempts | 1 attempt; active about 1 minute after enforcement was switched on. Tests 1 and 3, run 2 to 3 minutes later, were nevertheless *allowed* (the East US NSG and the RDP rule were created, then deleted). Both were refused when rerun about 10 minutes after the switch. **Fix: wait 10 more minutes after the probe.** |
| Tests 1 to 9: each unsafe command is denied with an `ALZ PD` assignment name and a friendly sentence | Denied | All 9 refused (Tests 1 and 3 only on the second run). The friendly sentence appears in Tests 1 to 7; Tests 8 and 9 name the assignment but show no sentence. Test 4 was refused by **two** rules (HTTPS-only and minimum TLS). For Test 9 subscription-level enforcement was on for about 2.5 minutes. |
| Section 2.6: non-compliant rows for `alz-pd-c1-prod` | About 27 (1 purge protection, 26 Owner tag) | Exactly **27**: 1 `KeyVaultPurgeProtection` and 26 `RequireOwnerTag`; names returned in lowercase. After Chapter 3: 1 (purge protection, an owner decision). |
| Section 3.4: non-compliant rows for `alz-pd-c2-prod` | About 12 | **11.** No Redis row, because `DiagRedisEnterprise` returned no result for the Redis database. Both Chapter 2 assignments first failed with `ResourceIdentityRequired` (fixed in 3.2). Lab: 6 findings; both Defender checks appeared within one hour, and `SubnetHasNsg` flagged `snet-pd-lab` although `nsg-pd-lab` was attached. |
| Section 4.3: the Owner-tag task - do the 4 private-endpoint NICs fail? | 26 ok, or 22 ok and 4 failed | **26 ok, 0 failed.** All 4 private-endpoint NICs accepted the tag. |
| Section 4.4: first minutes until the KQL query returns rows | 5 to 20 minutes | Rows on the first query, about 10 to 13 minutes after the settings were deployed and 4 minutes after the test traffic: `AppServicePlatformLogs` 47, `AppServiceConsoleLogs` 42, `AppServiceIPSecAuditLogs` 66, `AppServiceHTTPLogs` 57. |
| Section 4.5: untagged NSG gets tags (Modify beats Deny) | Succeeds with 2 tags | Succeeded; `nsg-pd-notags` received `CostCenter` and `Owner`. The lab Key Vault received `setByPolicy-LogAnalytics`, visible only with the corrected query. |
| Sections 4.2 and 4.6: the first remediation tasks after the 2-minute wait | Succeeded without an authorization error | No authorization error. Owner tag: 26 of 26. Lab VM backup: 1 of 1. `DeployDiagAppGateway` **failed with a conflict**, because the existing `diag-agw-alz` already sends the access log to `law-alz-central`. `DeployDiagRedisEnterprise` found 0 resources. |
| Section 4.6: backup item appears; protection state | Row for the VM; IRPending | `vm-pd-lab01`: IRPending, Healthy, DefaultPolicy (after two corrections: the built-in policy by GUID, and a `--query` for the table). |
| Section 4.7: `az policy exemption list --disable-scope-strict-match` | Four rows named `alz-pd-ex-...` | 4 rows (2 Mitigated, 2 Waiver). All four showed *Exempt* within about 30 minutes; PostgreSQL was last. |
| Section 5.3: stop protection, then delete the vault | Commands succeed; the lab is empty | **Not run** (dry run 1 ended with Level 1). |
| Section 5.3: the helper group `AzureBackupRG_indonesiacentral_1` | 0 resources and deleted, or left in place with a message | **Not run.** Because of the instant-restore prefix no helper group existed at the end of the run. |
| Section 5.4: delete the four exemptions by name and scope | The check prints nothing | **Not run.** |
| Portal pages in the Portal boxes (menu and tab names) | As written | **Not checked** (dry run 1 used the PowerShell path only). |
| `Test-SampleApp` after every chapter | 200 and 403 | Direct: 403 after every chapter. Through the gateway: *no answer* from Cloud Shell, because an NSG on the gateway subnet accepted HTTP only from certain addresses. Gateway backend health: Healthy at the start and after every chapter. **Fix: the test now also prints backend health (step 1.3).** |

### The ten corrections that the dry run led to

1. **1.4** - the hub firewall check needs `--api-version 2025-05-01` (`NoRegisteredProviderFound` otherwise).
2. **3.2, 4.9** - audit-only assignments need a managed identity: `--mi-system-assigned --location $LOC` (`ResourceIdentityRequired` otherwise). The identities get no role.
3. **4.6, 4.9** - built-in policies are passed by GUID only (`PolicyDefinitionNotFound` otherwise).
4. **3.5, 4.4, 4.5** - diagnostic-settings queries start with `[]`, because Azure CLI 2.91 returns a plain list.
5. **4.6** - `az backup item list` needs a `--query` (plain `-o table` is unavailable).
6. **2.3** - wait 10 more minutes after the probe.
7. **4.4, 4.8** - the Application Gateway diagnostics conflict, with three options.
8. **Counts** - production Detect findings 11 (not 12); F5 5 before and 1 after (not 6 and 0); `setByPolicy-LogAnalytics` on 4 resources (not 6).
9. **2.4, 2.6, 3.4** - names return in lowercase; Test 4 is refused by two rules; Tests 8 and 9 show no friendly sentence; the Defender checks appeared within one hour.
10. **1.3, 1.4, 6.4** - `Test-SampleApp` also prints the gateway backend health.

### Changes made after the dry run (not tested)

Some text and commands were changed after the dry run, to generalise the runbook. These changes were **not** run end to end:

- Placeholders for the subscription ID and the owner alias, and a guard that stops the variable block if the subscription ID is still a placeholder.
- Step 1.3 now checks the resource groups for an `Owner` tag (and adds it where missing) and prints the settings that the expected results assume. Level 4 removes only what step 1.3 added.
- Exemptions expire 90 days after the day you run the step. The date is built with the invariant culture (checked for the Indonesian culture in Windows PowerShell 5.1).
- Paths use forward slashes so that the same blocks run in Windows Terminal and in Azure Cloud Shell.
- `Show-Scorecard` assigns each result to a variable before it emits it, because Windows PowerShell 5.1 returns a JSON array as one object (checked with a mock `az` in Windows PowerShell 5.1).
- In Test 4 the safe storage account also disables public network access, so that it passes the Chapter 2 check; the pre-flight check also runs `Show-Enforcing`; the Log Analytics query uses `$FE` instead of a fixed name.

### Not verified yet

- The Portal (Option B) boxes and Test 10.
- Part 5 Levels 2 to 4 and step 5.6.
- Windows PowerShell 5.1, and Windows cultures other than English (en-US), were not run end to end. Every script parses in Windows PowerShell 5.1, and the exemption expiry date is built with the invariant culture, but the dry run used PowerShell 7 in Azure Cloud Shell.
- Optional improvement: add non-compliance messages to `alz-pd-lab-nopeering`, `alz-pd-rg-tags` and `alz-pd-rg-loc`, so that Tests 8 and 9 also show a friendly sentence.

### Known limitations and assumptions

- The expected counts (27, 11, 26, 5) were **measured** in dry run 1 on one environment. They can differ by a few on another run or another landing zone; the *pattern* matters.
- The built-in Redis diagnostics check (`DiagRedisEnterprise`) returned no result for the Redis database, so Chapters 2 and 3 neither report nor fix it.
- The Application Gateway of the reference landing zone already has the diagnostic setting `diag-agw-alz`, so the policy cannot add its own in step 4.4.
- `SubnetHasNsg` comes from Microsoft Defender for Cloud and can report a subnet as non-compliant for a while after an NSG is attached.
- Two Chapter 2 checks (**VM management ports** and **vulnerability assessment**) depend on Microsoft Defender for Cloud and can take up to 24 hours. In dry run 1 they appeared within one hour.
- The NSG rule detects exact ports 22 and 3389 and wildcards, not ranges.
- The private-endpoint network interfaces may refuse a tag change (step 4.3). In dry run 1 they accepted it.
- Backup is shown as **configured**; no restore test is part of this runbook.
- Azure Backup soft delete cannot be switched off (according to Microsoft Learn at the time of writing), so Azure keeps deleted backup data for 14 days. Level 2 was not run, so the exact behaviour of the lab vault is unverified. The Trusted Launch upgrade is not a demo step, because the lab VM is backed up with the Standard policy (step 4.7).
- Statements about Azure service availability (for example that Indonesia Central has no paired region, so geo-redundant PostgreSQL backup is unavailable) were true at the time of the dry run. Check the current documentation before you quote them.
- The Portal changes often; menu names were checked in October 2026 and may drift.
- Portal items marked **NOT VERIFIED LIVE** could not be opened without changing Azure: the denial banner wording, the remediation-task form, the exemption date picker, the Recovery Services vault pages, the IAM page of the policy identity and the Register button.
- Two settings have no labelled Portal field: PostgreSQL **geo-redundant backup** (use the CLI, or Overview > JSON View) and the scale set's **Trusted launch** (the Portal shows *Security type : Standard*).
- All assignments here are at resource-group or subscription scope because the demo uses one subscription. A real landing zone assigns the same initiatives **once at the management group**, and every subscription below inherits them.
- Azure Policy is a technical guardrail, not proof of regulatory compliance.

---

[Runbook index](README.md) &middot; Previous: [Appendix G - Sources](appendix-g-sources.md)
