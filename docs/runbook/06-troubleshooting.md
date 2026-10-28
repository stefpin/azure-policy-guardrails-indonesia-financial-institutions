# Part 6 - Troubleshooting

[Runbook index](README.md) &middot; Previous: [Part 5 - Wrap-up, reset and clean-up](05-wrap-up-and-clean-up.md) &middot; Next: [Appendix A - Everything this runbook creates](appendix-a-everything-this-runbook-creates.md)

Find your symptom in the left column. If a step fails and you are unsure what to do, run **Level 1** of Part 5 first (it is always safe), then come back.

## 6.1  Azure CLI and PowerShell

| Symptom | Cause | Fix |
| --- | --- | --- |
| `az` is not recognised | The Azure CLI is not installed, or the terminal was opened before it was installed. | Run `winget install Microsoft.AzureCLI`, close the terminal, open a new one. |
| `Please run 'az login' to setup account` | Your sign-in expired or you are in a new window. | Run `az login` and step 1.1 again. |
| `Interactive authentication is needed` or a *claims challenge* | Your tenant requires multi-factor authentication for write operations (for example through Conditional Access or an inherited policy). | `az logout` then `az login --scope https://management.core.windows.net//.default`. |
| `The subscription ... doesn't exist` or `not found` | Wrong account or the subscription is not selected. | `az account set --subscription "<your-subscription-id>"`. |
| `AuthorizationFailed` when creating an assignment or a role assignment | Your account is not Owner (or Resource Policy Contributor + User Access Administrator). | Ask for the Owner role on the subscription (step 1.1). |
| `unrecognized arguments` and a line starting with `--` | A line that should continue lost its **backtick** at the very end, or a space follows the backtick, or the paste was split. | Paste the block again in one piece. The backtick must be the last character on the line. |
| `... was unexpected at this time.` (for example `-o was unexpected at this time`) | Windows PowerShell hands a quoted `--query` that has round brackets but **no space** to the Azure CLI launcher (a batch file), and the Windows command processor cannot read it. | Count and filter in PowerShell as this runbook does, for example `(az resource list -g $RG_LAB --query "[].id" -o tsv \| Measure-Object).Count`. If you write your own `--query` with brackets, put a space inside it, for example `starts_with(name, 'x')`. |
| `Failed to parse '--definitions' argument` or `'--params'` | The JSON file is missing, malformed or in the wrong folder. | Run `Get-ChildItem $WORK`. Re-create the file with its here-string. Make sure the closing `'@` is at the **start** of its line. |
| Variables such as `$SUB` or `$WORK` are empty; `New-Ref` is not recognised | You opened a new PowerShell window. | Run the step 1.2 block again, then only the **first block of step 1.3** (the helper commands) - not its snapshot or Owner-tag blocks, which would overwrite your 'before' evidence - and the `New-Ref` helper from step 1.10 if you create initiatives. |
| `Variable reference is not valid. ':' was not followed by a valid variable name character` | In a string, `$RG_CORP:name` is read as a drive-qualified variable. | Write `"${RG_CORP}:name"` with curly braces, as the commands in this runbook do. |
| Strange quote errors when passing JSON on the command line | PowerShell 5.1 removes double quotes from inline JSON. | Always use a file and `"@file.json"`, as in this runbook. |
| A command works in one window but prints nothing in another | `ConvertFrom-Json` returns an array as **one object** in Windows PowerShell 5.1. | Store the result in a variable first (`$x = ... \| ConvertFrom-Json`) and then `foreach` over it. The helper commands do this already. |
| `NoRegisteredProviderFound` in the hub firewall check (step 1.4) | Azure CLI 2.91 asks for an API version that the firewall provider does not offer. | Keep `--api-version 2025-05-01` in the `az resource show` command, as step 1.4 does. |
| `ResourceIdentityRequired` when assigning Chapter 2 or the Activity Log policy | The initiative (or policy) contains definitions that can deploy resources, so Azure demands a managed identity even for audit-only use. | Add `--mi-system-assigned --location $LOC` to the assignment (steps 3.2 and 4.9). The identity needs no role. |
| `PolicyDefinitionNotFound` for a built-in policy | The long form `/providers/Microsoft.Authorization/policyDefinitions/<guid>` is not accepted by `az policy assignment create --policy` in Azure CLI 2.91. | Pass the built-in policy as its bare GUID, as steps 4.6 and 4.9 do. |
| A diagnostic-settings query prints nothing | Azure CLI 2.91 returns a plain list, so a query that starts with `value[]` finds nothing. | Start the query with `[]`, for example `--query "[].name"`. |

## 6.2  Policy behaviour

| Symptom | Cause | Fix |
| --- | --- | --- |
| The 'unsafe' command **succeeded** instead of being denied | The assignment is not active yet (about 5 minutes for the first rule; in the dry run up to 10 minutes for every rule), or enforcement is `DoNotEnforce`, or it is assigned at a different scope. | Run the probe in step 2.3. Check `az policy assignment show --name alz-pd-c1-lab --scope $SCOPE_LAB --query enforcementMode -o tsv` (expect `Default`). **Delete the resource that was created by mistake**, wait, and try again. |
| The deny error names an assignment that does not start with `alz-` | An **inherited** policy, not yours. | Read section 0.3 and change the test so it avoids that rule. You cannot change inherited policies. |
| Anonymous blob access was not denied | An inherited Modify policy (if your tenant has one) fixes it before any Deny rule is evaluated (Modify runs first). | Use the HTTPS-only test (Test 4). |
| `az vm create` in the lab is denied with the SSH rule | By default the CLI adds an NSG rule that allows SSH from anywhere. Chapter 1 (Test 3 rule) blocks that. | Use `--nsg '""'` as in step 1.8 so no new NSG is created, or `--nsg-rule NONE`. |
| The compliance list is **empty** | Azure has not finished evaluating. | Wait 10 to 20 minutes. Run `az policy state trigger-scan -g <group> --no-wait`. Check that the assignment exists at that scope (`Show-Assignments`). |
| `Show-Compliance` says `No NonCompliant rows` for an assignment that exists at the **subscription** scope | `az policy state list -g <group>` only sees assignments in that group. | For the two subscription-level assignments use `az policy state list --policy-assignment alz-pd-rg-tags` (no `-g`). |
| The Portal compliance page shows many findings you do not recognise | It also shows inherited assignments (for example a security benchmark). | Filter by the assignment name **alz-pd** (section 3.3). |
| A finding disappeared even though you changed nothing | An exemption applies, or the resource was deleted and re-created. | Check `az policy exemption list --disable-scope-strict-match` (without that option the list only shows exemptions on the subscription itself, not on single resources) and the resource's creation time. |
| After an exemption is created the finding still says Non-compliant | Exemptions trigger a new evaluation that takes 15 to 30 minutes. | Wait, then run `az policy state trigger-scan`. Check that the **scope** is the resource and the **reference ID** is exact (it is case-sensitive). |

## 6.3  Remediation

| Symptom | Cause | Fix |
| --- | --- | --- |
| `az policy remediation create` says it cannot find the assignment | The `-g` resource group is different from the assignment's scope. | Use `-g $RG_CORP` for `alz-pd-c3-prod` and `-g $RG_LAB` for the lab assignments. |
| The task ends with failed deployments | The identity is missing a role, or Azure has not applied the role yet (it can take up to 10 minutes), or Azure refuses to change that resource. | Check the roles (step 4.2). Open the task in the Portal (Policy, Remediation, Remediation tasks, select the task, **Deployments** tab) and read the error. If it says *AuthorizationFailed*, wait 5 to 10 minutes, delete the failed task (`az policy remediation delete -g <group> -n <task>`) and create it again. The four private-endpoint network interfaces may refuse a tag change - that is expected. |
| `PrincipalNotFound` when granting a role | Microsoft Entra ID has not yet replicated the new identity. | Wait 30 seconds and repeat only that command. |
| The task stays `Evaluating` for a long time | Re-evaluating compliance of many resources. | Wait. A task for 26 resources normally ends within 10 minutes. |
| Diagnostic setting exists but no logs appear | Logs take time, or no traffic was generated, or the query time range is too short. | Generate traffic (step 4.4), wait 10 to 20 minutes, widen the time range to 2 hours. |
| The Application Gateway task fails: `Data sinks can't be reused in different settings on the same category for the same resource` | The gateway already has a diagnostic setting of its own (`diag-agw-alz`) that sends the same log category to the same workspace. Azure accepts only one. | Expected. See the trap in step 4.4 for the three options. |
| The Redis diagnostics task finishes with **0 deployments** | The built-in rule returned no result for the Redis database in the dry run. | Expected. Check the database by hand with `az monitor diagnostic-settings list --resource <database id>`. |
| The VM is not backed up after the task | The vault is in another region, the tag value does not match, or `Microsoft.RecoveryServices` is not registered. | Check `vaultLocation`, the tag `Backup=daily` on the VM, and step 1.5. |

## 6.4  Resources and names

| Symptom | Cause | Fix |
| --- | --- | --- |
| `StorageAccountAlreadyTaken` | Storage account names are unique across all of Azure. | Change `$RUN` in step 1.2 (for example to `02`) and run the commands again. |
| `VaultAlreadyExists` or the name is reserved by a deleted vault | A purge-protected vault stays soft-deleted for its retention period. | Change `$RUN`. |
| `SkuNotAvailable` or a quota error for the VM | The size is not available in the region or the quota is used. | Use another small size. List the sizes with `az vm list-skus -l indonesiacentral --resource-type virtualMachines --query "[].name" -o tsv \| Select-String Standard_B2`. |
| `RequestDisallowedByPolicy` while **creating the VM scale set, large VMs or classic resources** | Inherited deny rules (for example on VM sizes or resource types). | Keep to small B-series VMs and Resource Manager resources. |
| The Application Gateway answers **502** | The back end is unhealthy (host header) or the gateway is still starting. | The 'host header fix' in the reference landing zone's `scripts/04-workload.ps1`. Wait 2 minutes after starting the gateway. |
| `Test-SampleApp` prints `no answer` on the first line | The gateway is stopped, **or** an NSG on the gateway subnet accepts HTTP only from certain addresses (then a request from Azure Cloud Shell gets no answer). | Step 1.4: start the gateway and wait until it finishes. If it is running, rely on the **Gateway backend health** line (expect Healthy) and the 403 line, or run the test from an allowed client. |
| A vault cannot be deleted in Level 2 | Protection was not stopped yet, a backup job is still running, or this vault still follows the older soft-delete rule. | Run the numbered commands of step 5.3 in order and read its COMMON TRAP box. Soft delete cannot be switched off any more, so deleted backup data stays recoverable for 14 days (per Microsoft Learn at the time of writing). |

## 6.5  Azure Portal

| Symptom | Cause | Fix |
| --- | --- | --- |
| A menu or button has a slightly different name | The Portal changes often. | Use the search box at the top of the Portal to find the page (for example, type **Policy**). The CLI commands do not change. |
| You do not see your resources | Wrong directory or subscription filter. | Check the directory (the **Settings** gear opens *Portal settings \| Directories + subscriptions*; or use **Switch directory** in the account menu) and check that the **Scope** pill at the top of the Policy page shows your subscription. |
| The *Policy* pages are slow | Compliance data is large. | Select a narrow scope (the resource group) and filter by `alz-pd`. |

---

[Runbook index](README.md) &middot; Previous: [Part 5 - Wrap-up, reset and clean-up](05-wrap-up-and-clean-up.md) &middot; Next: [Appendix A - Everything this runbook creates](appendix-a-everything-this-runbook-creates.md)
