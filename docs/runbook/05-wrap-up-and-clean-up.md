# Part 5 - Wrap-up, reset and clean-up

[Runbook index](README.md) &middot; Previous: [Part 4 - Chapter 3: REMEDIATE and PROVE](04-chapter-3-remediate-and-prove.md) &middot; Next: [Part 6 - Troubleshooting](06-troubleshooting.md)

The demonstration is finished. Now you **put everything back into a safe state**. There are four levels. Do **Level 1 after every demonstration**, no exceptions. Do the others when you are finished with the demonstration.

**Opened a new PowerShell window?** Run the step 1.2 block, and then only the **first block of step 1.3** (the helper commands) before you start. Do not run the rest of step 1.3 again: it would overwrite your 'before' evidence.

| Level | What it does | When |
| --- | --- | --- |
| **1 - Safe state** | Switches off every enforcing assignment. Keeps all policy objects and lab resources. | Always - right after the demo |
| **2 - Empty the lab** | Deletes everything in `rg-alz-policy-lab` (the resource group itself stays). | At the end of the day |
| **3 - Remove the policy library** | Deletes exemptions, remediation tasks, role assignments, assignments, initiatives and definitions. | When you will not repeat the demo soon |
| **4 - Undo the production changes** | Removes the `Owner` tags and the diagnostic settings that Chapter 3 added to the sample application, and the `Owner` tags you added to the resource groups in step 1.3. | Only if you want production back exactly as it was before Part 4 |

## 5.1  What you proved - the evidence table

Use this table as a closing summary of what you proved. It maps each family to the evidence you produced. The last column is the reminder of what Azure Policy cannot do.

| Family | Chapter 1 proved | Chapter 2 found | Chapter 3 did | Still outside Azure Policy |
| --- | --- | --- | --- | --- |
| F1 Locations | Resources and `rg-alz-*` groups cannot be created outside the approved regions. | All sample-application resources are in Indonesia Central. | - | Which workloads are location-restricted; regulator approvals |
| F2 Public exposure | No public IP on a NIC; no Internet-open SSH or RDP. | Data tier fully private; web apps allow public access at platform level. | Web apps recorded as *Mitigated*. | Penetration testing; identity (MFA, PIM) |
| F3 Data in transit | Storage must require HTTPS. | Gateway has an HTTP listener (demo). | Recorded as *Waiver* with expiry. | Certificate lifecycle |
| F4 Stored data and keys | Key Vault needs purge protection. | Infrastructure encryption, encryption at host, purge protection missing. | Three decisions handed to the owner. | Key management procedures |
| F5 Monitoring | - | Five resources without diagnostic settings (the gateway already had its own). | Settings deployed on four resources; logs verified in Log Analytics. | People and process that read the logs |
| F6 Backup and recovery | - | VM without backup; PostgreSQL geo-backup unavailable. | VM backup deployed by tag; geo-backup *Waiver*. | The DR plan and the restore test |
| F7 Compute baseline | - | VM without Trusted Launch. | Decision handed to engineering: Trusted Launch needs the Enhanced backup policy first. | Patching and hardening operations |
| F8 Network segmentation | Default route must use the firewall; isolated networks cannot be peered. | Subnets and routes already compliant. | - | Firewall rule review |
| F9 Ownership | Resources need `CostCenter` and `Owner`. | 26 resources without `Owner`. | Tags copied from the resource group in production (remediation task); new lab resources tagged automatically. | Governance and accountability processes |

> [!CAUTION]
> **Keep in mind**
>
> This table shows the **technical configuration** of Azure resources. It does not establish regulatory compliance. Regulator approvals, contracts, identity governance, incident handling, penetration testing and the disaster-recovery exercise need their own owners (see section 0.9).

## 5.2  Level 1 - Back to a safe state (always)

> **Where to do this:** **PowerShell window.**

Switch every enforcing assignment back to `DoNotEnforce`. Nothing is deleted.

```powershell
$enforcing = @(
  @('alz-pd-c1-lab',        $SCOPE_LAB),
  @('alz-pd-c3-lab',        $SCOPE_LAB),
  @('alz-pd-lab-nopeering', $SCOPE_LAB),
  @('alz-pd-rg-tags',       $SCOPE_SUB),
  @('alz-pd-rg-loc',        $SCOPE_SUB)
)
foreach ($a in $enforcing) {
  az policy assignment update --name $a[0] --scope $a[1] --enforcement-mode DoNotEnforce -o none
}

# The safety check: this must print NOTHING
Show-Enforcing
```

> **What you should see**
>
> **No output at all.** If a name is printed, that assignment is still enforcing: run the `update` command for it again.

### Check enforcement in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Assignments**.

1. Policy > **Authoring** > **Assignments** > **Edit columns** > **+ Add option** > **Policy enforcement** > **Save** (see the tip in step 1.6).
2. Search `alz`. Every row must show **DoNotEnforce**. Click any row to double-check: **Essentials** says *Policy enforcement : DoNotEnforce*.
3. To switch one off in the Portal: click the assignment > **Edit assignment** > **Basics** > **Policy enforcement** = **Do not enforce** > **Review + save** > **Save**.

```powershell
Show-Assignments
Test-SampleApp
```

> **What you should see**
>
> `Show-Assignments` lists the 8 baseline rows plus your `alz-pd-...` rows, all **DoNotEnforce**. `Test-SampleApp` shows 403 directly and backend health Healthy (and 200 through the gateway from an allowed client).

## 5.3  Level 2 - Empty the lab

> **Where to do this:** **PowerShell window.**

The lab contains a VM that is **protected by Azure Backup**. Stop the backup **first**, then delete the vault, then empty the rest of the lab. Follow the order exactly.

> [!NOTE]
> **Soft delete is always on**
>
> New Azure Backup vaults keep deleted backup data in a **soft-deleted** state for **14 days** at no extra cost, and Azure no longer lets you switch this off. So 'delete' here means *removed from view, recoverable for 14 days, then gone for good*. A vault that holds only soft-deleted items is itself soft-deleted when you delete it, and you can create a new vault with the same name straight away. (This follows Microsoft Learn at the time of writing. The vault-level behaviour depends on your region and vault, and this level was not run in the dry run - the trap below has the fallback.)

### Step 1 - Remove the backup of the VM and the vault

```powershell
# 1. Stop protecting the VM and delete its backup data (it moves to the soft-deleted state)
az backup protection disable -g $RG_LAB -v $RSV -c $VM -i $VM --backup-management-type AzureIaasVM `
  --workload-type VM --delete-backup-data true --yes

# 2. Run this until it prints nothing (no backup job is still running)
az backup job list -g $RG_LAB -v $RSV --status InProgress -o table

# 3. Delete the vault
az backup vault delete -g $RG_LAB -n $RSV --yes
```

> **What you should see**
>
> No error messages. Command 1 prints the details of the backup job. Command 2 prints nothing once the jobs are finished (if it still lists a job, wait a minute and run it again).

> [!WARNING]
> **COMMON TRAP - the vault will not delete**
>
> If command 3 says that the vault still contains backup items, protection was not stopped yet or a job is still running: run command 1 again, wait until command 2 prints nothing, and try command 3 again.
>
> If the message names *backup items in soft deleted state*, this vault still follows the older rule. Leave the vault where it is and finish the rest of Level 2 (step 2 may then report an error about the vault - that is expected). Delete the vault after the soft-deleted items have expired (14 days). An empty vault costs next to nothing.

### Step 2 - Delete everything else in the lab

An empty template deployed in **Complete** mode deletes every resource in the resource group and keeps the group itself (it belongs to the landing zone, and the baseline assignment `alz-baseline-lab` is attached to it).

```powershell
$schema = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#'
'{"$schema":"' + $schema + '","contentVersion":"1.0.0.0","resources":[]}' | Set-Content "$WORK/empty.json" -Encoding ascii
az deployment group create -g $RG_LAB --mode Complete --template-file "$WORK/empty.json" --name alz-pd-empty-lab -o none
(az resource list -g $RG_LAB --query "[].id" -o tsv | Measure-Object).Count
az resource list -g $RG_LAB --query "[].{name:name, type:type}" -o table
```

> **What you should see**
>
> `0` - the lab is empty again - and no table after it. The Key Vault with purge protection is now *soft-deleted* (it disappears from the list; the name stays reserved for 7 days). If the number is not 0, the table shows what is left.

### Step 3 - Remove the resource group Azure Backup created

> [!NOTE]
> **Instant-restore prefix**
>
> If you give the vault's backup policy an instant-restore resource-group prefix (for example `rg-alz-pd-bkp-`), Azure names the helper group after that prefix instead of `AzureBackupRG_...`. Change the name filter in the two commands below accordingly. This level was not run in the dry run (see Appendix H).

Azure Backup creates a helper resource group for restore points the first time it protects a VM in a region. The group is **shared by every VM backup in that region**, so first look - then delete only if it is empty.

```powershell
# Is there another Recovery Services vault in Indonesia Central? Expect: nothing is printed
az backup vault list --query "[?location=='indonesiacentral'].{name:name, group:resourceGroup}" -o table

# The helper groups and how many resources each one holds
foreach ($g in (az group list --query "[].name" -o tsv | Where-Object { $_ -like 'AzureBackupRG_indonesiacentral_*' })) {
  "{0}: {1} resource(s)" -f $g, (az resource list -g $g --query "[].id" -o tsv | Measure-Object).Count
}
```

> [!CAUTION]
> **Check before you delete**
>
> Run the next block **only** if the first command printed no vault (or only vaults you know are yours) **and** every helper group shows **0 resource(s)**. If a group still holds resources, leave the group alone: they are the instant-restore snapshots of a backup (for the lab VM the names contain `vm-pd-lab01`). Azure does not remove them by itself once the vault is deleted, and they cost very little. Write the name in your clean-up list and remove the leftover snapshots later, after you have checked in the Portal that nothing else uses them. If in doubt, leave it - an empty group is free.

```powershell
foreach ($g in (az group list --query "[].name" -o tsv | Where-Object { $_ -like 'AzureBackupRG_indonesiacentral_*' })) {
  if ((az resource list -g $g --query "[].id" -o tsv | Measure-Object).Count -eq 0) { "Deleting the empty group $g"; az group delete -n $g --yes }
  else { "NOT deleted: $g still holds resources." }
}
```

## 5.4  Level 3 - Remove the policy library

> **Where to do this:** **PowerShell window.** The order matters: you cannot delete an initiative that is still assigned, or a definition that is still part of an initiative.

### Step 1 - Remove the role assignments of the policy identities

```powershell
$withIdentity = @(
  @('alz-pd-c3-prod',        $SCOPE_CORP),
  @('alz-pd-c3-lab',         $SCOPE_LAB),
  @('alz-pd-c3-lab-vmbackup', $SCOPE_LAB)
)
foreach ($a in $withIdentity) {
  $mi = az policy assignment show --name $a[0] --scope $a[1] --query identity.principalId -o tsv
  if ($mi) {
    foreach ($r in (az role assignment list --assignee $mi --all --query "[].id" -o tsv)) { az role assignment delete --ids $r }
  }
}
```

### Step 2 - Remove exemptions and remediation tasks

An exemption is deleted by its **name and its scope** (the resource it was created on). The `2>$null` hides the 'not found' message if you skipped section 4.7.

```powershell
$exemptions = @(
  @('alz-pd-ex-appsvc-frontend', "$SCOPE_CORP/providers/Microsoft.Web/sites/$FE"),
  @('alz-pd-ex-appsvc-backend',  "$SCOPE_CORP/providers/Microsoft.Web/sites/$BE"),
  @('alz-pd-ex-appgw-http',      "$SCOPE_CORP/providers/Microsoft.Network/applicationGateways/$AGW"),
  @('alz-pd-ex-pg-geobackup',    "$SCOPE_CORP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$PG")
)
foreach ($e in $exemptions) { az policy exemption delete --name $e[0] --scope $e[1] 2>$null }

foreach ($rg in $RG_CORP, $RG_LAB) {
  foreach ($t in (az policy remediation list -g $rg --query "[].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' })) {
    az policy remediation delete -g $rg -n $t
  }
}

# Check: must print nothing
az policy exemption list --disable-scope-strict-match --query "[].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' }
```

> **What you should see**
>
> No output from the last command. If a name is printed, run the `delete` command for that exemption again (check its scope with the table in section 4.7).

### Step 3 - Delete the assignments, then the initiatives, then the definitions

```powershell
$all = @(
  @('alz-pd-c1-lab',          $SCOPE_LAB),  @('alz-pd-c1-prod', $SCOPE_CORP),
  @('alz-pd-c2-lab',          $SCOPE_LAB),  @('alz-pd-c2-prod', $SCOPE_CORP),
  @('alz-pd-c3-lab',          $SCOPE_LAB),  @('alz-pd-c3-prod', $SCOPE_CORP),
  @('alz-pd-c3-lab-vmbackup', $SCOPE_LAB),  @('alz-pd-lab-nopeering', $SCOPE_LAB),
  @('alz-pd-rg-tags',         $SCOPE_SUB),  @('alz-pd-rg-loc', $SCOPE_SUB),
  @('alz-pd-sub-actlog',      $SCOPE_SUB)
)
foreach ($a in $all) { az policy assignment delete --name $a[0] --scope $a[1] 2>$null }

$sets = 'alz-pd-c1-prevent', 'alz-pd-c2-detect', 'alz-pd-c3-remediate'
foreach ($s in $sets) { az policy set-definition delete --name $s --subscription $SUB }

$defs = 'alz-pd-nsg-no-internet-mgmt', 'alz-pd-route-default-via-fw', 'alz-pd-appgw-https-listener',
        'alz-pd-rg-required-tags', 'alz-pd-rg-allowed-locations'
foreach ($d in $defs) { az policy definition delete --name $d --subscription $SUB }
```

> [!NOTE]
> `2>$null` hides the 'not found' message for an assignment you never created (for example the optional `alz-pd-sub-actlog`). The reference landing zone's own objects (`alz-baseline`, `alz-deny-vnet-peering` and their assignments) are **not** touched: their names do not start with `alz-pd-`.

## 5.5  Level 4 - Undo the production changes (optional)

> **Where to do this:** **PowerShell window.** Skip this level if you want to keep the improvements.

Chapter 3 changed two things in production, and step 1.3 may have added an `Owner` tag to the resource groups. All of it is easy to reverse.

```powershell
# 1. Remove the Owner tag that the remediation copied from the resource group
$rgOwner = az group show -n $RG_CORP --query tags.Owner -o tsv
foreach ($id in (az resource list -g $RG_CORP --query "[].id" -o tsv)) {
  az tag update --resource-id $id --operation delete --tags "Owner=$rgOwner" -o none
}

# 2. Remove the diagnostic settings that the policy deployed
$q = "[?type=='Microsoft.KeyVault/vaults' || type=='Microsoft.Web/sites' ||"
$q += " type=='Microsoft.DBforPostgreSQL/flexibleServers' || type=='Microsoft.Network/applicationGateways'].id"
$ids  = az resource list -g $RG_CORP --query $q -o tsv
$ids += "$SCOPE_CORP/providers/Microsoft.Cache/redisEnterprise/$REDIS/databases/default"
foreach ($id in $ids) { az monitor diagnostic-settings delete --name setByPolicy-LogAnalytics --resource $id }

# 3. Remove the Owner tag from the resource groups - ONLY the ones you added it to in step 1.3 (they are listed in a file)
foreach ($rg in (Get-Content "$WORK/evidence/added-rg-owner.txt" -ErrorAction SilentlyContinue)) {
  $cur = az group show -n $rg --query tags.Owner -o tsv
  az tag update --resource-id "$SCOPE_SUB/resourceGroups/$rg" --operation delete --tags "Owner=$cur" -o none
}
```

> **What you should see**
>
> No errors for the tags. Production again has no `Owner` tag and no policy-created diagnostic settings - exactly as in the 'before' snapshot of step 1.3. (In the dry run all four private-endpoint NICs accepted the tag; if Azure refused them in your run, a 'not found' message for those is normal.) Azure prints *not found* for the application gateway and the Redis database: they never got `setByPolicy-LogAnalytics`. That is expected, and the gateway's own `diag-agw-alz` is **not** touched.

## 5.6  Switch off the expensive parts

> **Where to do this:** **PowerShell window.**

```powershell
az network application-gateway stop -g $RG_CORP -n $AGW        # about 5 minutes
az postgres flexible-server stop -g $RG_CORP -n $PG             # about 3 minutes
```

The Azure Firewall and Azure Bastion keep running (and billing) until you delete them. The reference landing zone's `scripts/99-teardown.ps1 -Mode Pause` deletes them (and the gateway) and can rebuild them. Also check whether anything else you started is still on:

```powershell
az vm list -g $RG_LAB --query "[].name" -o tsv         # should print nothing after Level 2
az network application-gateway show -g $RG_CORP -n $AGW --query operationalState -o tsv
```

## 5.7  Final verification

> **Where to do this:** **PowerShell window.**

```powershell
"--- alz-pd assignments (expect none after Level 3) ---"
Show-Assignments -Filter 'alz-pd-*'
"--- alz-pd definitions and initiatives (expect none after Level 3) ---"
az policy definition list --query "[?policyType=='Custom'].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' }
az policy set-definition list --query "[?policyType=='Custom'].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' }
"--- nothing enforcing ---"
Show-Enforcing
"--- the 8 baseline assignments are still there ---"
Show-Assignments
```

> [!IMPORTANT]
> **CHECKPOINT - do not continue until all of this is true**
>
> - After Level 1: nothing enforcing.
> - After Level 2: the lab is empty (a deleted vault is kept by Azure for 14 days and is not listed).
> - After Level 3: no `alz-pd-...` object remains; the eight baseline assignments, the initiative `alz-baseline` and the policy `alz-deny-vnet-peering` are untouched.
> - `Test-SampleApp` still shows **403** directly and backend health **Healthy** (and **200** through the gateway, if your client can reach it and you did not stop the gateway yet).

> [!NOTE]
> **Local files**
>
> The folder `alz-policy-demo` in your user folder (the JSON files and the `evidence` subfolder) stays on your PC on purpose: it is your evidence. When you no longer need it, copy `evidence` to an approved location and remove the folder with `Remove-Item $WORK -Recurse -Force`.

---

[Runbook index](README.md) &middot; Previous: [Part 4 - Chapter 3: REMEDIATE and PROVE](04-chapter-3-remediate-and-prove.md) &middot; Next: [Part 6 - Troubleshooting](06-troubleshooting.md)
