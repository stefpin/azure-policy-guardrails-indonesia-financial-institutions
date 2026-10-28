# Part 4 - Chapter 3: REMEDIATE and PROVE

[Runbook index](README.md) &middot; Previous: [Part 3 - Chapter 2: DETECT - find the gaps](03-chapter-2-detect.md) &middot; Next: [Part 5 - Wrap-up, reset and clean-up](05-wrap-up-and-clean-up.md)

Chapter 2 gave you a list of findings. In this chapter you **fix what can be fixed automatically**, you **record a formal exception** for what must stay as it is, and you **prove the result** - with evidence, and with the application still answering 200 and 403.

## 4.1  The idea

Two effects can change things:

| Effect | What it does | Example in this runbook |
| --- | --- | --- |
| **Modify** | Changes a property of the resource. Works on the request *before* the resource is created, and on existing resources through a *remediation task*. | Copy the `Owner` and `CostCenter` tags from the resource group. |
| **DeployIfNotExists** (DINE) | Deploys a missing related resource *after* the resource is created, and on existing resources through a *remediation task*. | Create the diagnostic setting that sends logs to `law-alz-central`. Enable backup for a VM. |

### Four ideas you need

1. **Managed identity.** Azure Policy has no hands of its own. To change a resource it uses a **managed identity** that belongs to the *assignment*. You create it with `--mi-system-assigned`.
2. **Roles.** The identity can only do what its **roles** allow. Each policy says which role it needs. You grant exactly those roles, at the smallest sensible scope (table below).
3. **Remediation task.** For resources that **already exist**, nothing happens until you start a *remediation task*. This is a deliberate, visible, reversible action. It works even though the assignment is `DoNotEnforce`.
4. **Not everything can be remediated.** Some settings cannot be changed in place, or must not be changed without a decision. Azure Policy cannot fix those; you record an **exemption** or plan an engineering change (section 4.7).

| Policy | Effect | Roles the identity needs | Granted at |
| --- | --- | --- | --- |
| Inherit `Owner` / `CostCenter` tag | Modify | **Contributor** (the role named inside the built-in definition) | the resource group |
| Diagnostic settings (5 kinds) | DeployIfNotExists | **Log Analytics Contributor** (named inside the definition) | the resource group (Contributor already covers it) **and** the workspace `law-alz-central`, which is in another resource group |
| Back up VMs by tag | DeployIfNotExists | **Virtual Machine Contributor** and **Backup Contributor** | the lab resource group |

> [!NOTE]
> **Why contributor?**
>
> The built-in tag policy names **Contributor** as the role it needs, so that is what the Azure Portal would grant too. It is broad. In a real landing zone you would review it, or use a custom role limited to tag writes. For this demo the role is granted only on one resource group and is removed in Part 5.

## 4.2  Assign Chapter 3 to production and to the lab - and give the identities their roles

> **Where to do this:** **PowerShell window.** The Portal alternative for the assignment follows the commands.

You create **two** assignments of the same initiative:

- `alz-pd-c3-prod` - on production, **`DoNotEnforce`**. Nothing changes by itself. Changes happen only when *you* start a remediation task.
- `alz-pd-c3-lab` - on the lab, **enforcing**. Here new resources are fixed **automatically at creation**.

```powershell
# --- Production: no automatic changes ---
az policy assignment create --name "alz-pd-c3-prod" `
  --display-name "ALZ PD - Chapter 3 REMEDIATE (PROD, started by remediation tasks)" `
  --description "Fixes are applied only when a remediation task is started. Enforcement stays OFF." `
  --policy-set-definition "$SCOPE_SUB/providers/Microsoft.Authorization/policySetDefinitions/alz-pd-c3-remediate" `
  --scope $SCOPE_CORP --params "@$WORK/assign-law.json" --enforcement-mode DoNotEnforce `
  --mi-system-assigned --location $LOC

# --- Lab: automatic fixes at creation ---
az policy assignment create --name "alz-pd-c3-lab" `
  --display-name "ALZ PD - Chapter 3 REMEDIATE (LAB, automatic)" `
  --description "Fixes new lab resources at creation." `
  --policy-set-definition "$SCOPE_SUB/providers/Microsoft.Authorization/policySetDefinitions/alz-pd-c3-remediate" `
  --scope $SCOPE_LAB --params "@$WORK/assign-law.json" --enforcement-mode Default `
  --mi-system-assigned --location $LOC
```

> **What you should see**
>
> Two JSON blocks, each with an `identity` section: `"type": "SystemAssigned"` and a `principalId`.

### Option B - the same assignment in the Azure Portal wizard

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Assignments** > **Assign initiative**.

The steps are the same as in step 2.2 (and the same warning about the automatic assignment name applies), with three differences:

1. **Basics:** choose the initiative **ALZ PD - Chapter 3 REMEDIATE: fix automatically**. For production **Policy enforcement** must be **Do not enforce**; for the lab **Default (enforcement)**.
2. **Parameters:** untick *Only show parameters that need input or review* if you want to see everything. Paste the workspace resource ID (`$LAW_ID`) into **logAnalyticsWorkspaceId**.
3. **Managed identity:** **Create a Managed Identity** is ticked and greyed out (the initiative contains Modify and DeployIfNotExists policies). Leave **Type of Managed Identity** = **System assigned managed identity** and set **System assigned identity location** to **(Asia Pacific) Indonesia Central**. The box **Permissions** lists the roles the Portal will give automatically - **at the scope of the assignment only**.

> [!NOTE]
> **What the portal does not do**
>
> The Portal grants the roles on the **assignment scope** (the resource group). It does **not** grant a role on the workspace `law-alz-central`, which is in another resource group. You still need the *Log Analytics Contributor* assignment on the workspace from the command in this step.

Now grant the roles. Read the identity of each assignment, wait a moment for Microsoft Entra ID to learn about it, then assign the roles. (If you created the assignments in the Portal wizard, the Portal has already granted **Contributor** on the resource group. The two `Contributor` commands below then simply return the existing role - that is harmless. You still need the two **Log Analytics Contributor** commands.)

```powershell
$MI_PROD = az policy assignment show --name alz-pd-c3-prod --scope $SCOPE_CORP --query identity.principalId -o tsv
$MI_LAB  = az policy assignment show --name alz-pd-c3-lab  --scope $SCOPE_LAB  --query identity.principalId -o tsv
"prod identity: $MI_PROD"; "lab identity:  $MI_LAB"
Start-Sleep -Seconds 45        # Entra ID needs a moment to know the new identity

az role assignment create --assignee-object-id $MI_PROD --assignee-principal-type ServicePrincipal `
  --role "Contributor" --scope $SCOPE_CORP -o none
az role assignment create --assignee-object-id $MI_PROD --assignee-principal-type ServicePrincipal `
  --role "Log Analytics Contributor" --scope $LAW_ID -o none

az role assignment create --assignee-object-id $MI_LAB --assignee-principal-type ServicePrincipal `
  --role "Contributor" --scope $SCOPE_LAB -o none
az role assignment create --assignee-object-id $MI_LAB --assignee-principal-type ServicePrincipal `
  --role "Log Analytics Contributor" --scope $LAW_ID -o none

"Waiting 2 minutes so that Azure can apply the new roles..."
Start-Sleep -Seconds 120
```

> **What you should see**
>
> No output from the four role commands (they end with `-o none`), then the waiting message. Check the result with:

```powershell
az role assignment list --assignee $MI_PROD --all --query "[].{role:roleDefinitionName, scope:scope}" -o table
```

> **What you should see**
>
> Two rows for the production identity: **Contributor** on `rg-alz-corp-prod` and **Log Analytics Contributor** on `law-alz-central`.

> [!WARNING]
> **COMMON TRAP - 'PrincipalNotFound'**
>
> If a role assignment fails with *PrincipalNotFound*, the identity is not visible yet. Wait 30 seconds and repeat only the failed command.

> [!WARNING]
> **COMMON TRAP - a task fails with 'AuthorizationFailed'**
>
> Azure documents that a new role can take **up to 10 minutes** to apply. The 2-minute wait is normally enough, but if a remediation task in section 4.3, 4.4 or 4.6 fails with an authorization error, wait 5 to 10 minutes, delete the failed task (`az policy remediation delete -g <resource group> -n <task name>`) and create it again.

### Check the roles in the Azure Portal

> **Where to do this:** **Azure Portal** - the resource group `rg-alz-corp-prod` > **Access control (IAM)**.

1. Open `rg-alz-corp-prod` (top search box). In its left menu click **Access control (IAM)**.
2. Open the tab **Role assignments** and look for the identity of the assignment (it is named after the assignment, for example `alz-pd-c3-prod`) with the role **Contributor**.
3. Repeat on the workspace `law-alz-central` (resource group `rg-alz-mgmt`) and look for **Log Analytics Contributor**.

> [!NOTE]
> **Not verified live**
>
> The IAM page layout was not inspected, because the identities do not exist until you create the assignment. The `az role assignment list` command in this step is the reliable check.

## 4.3  Fix production (1 of 2): the Owner tag - effect Modify

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

First look at the **before** state: no `Owner` tag anywhere.

```powershell
az resource list -g $RG_CORP --query "[].{name:name, owner:tags.Owner, costCenter:tags.CostCenter}" -o table
```

> **What you should see**
>
> 26 rows. The `owner` column is **empty** on every row; `costCenter` is `ALZ-Demo`.

Now start the remediation task. `ReEvaluateCompliance` tells Azure to check the resources first, so you do not have to wait for a scan.

```powershell
az policy remediation create -g $RG_CORP -n alz-pd-rem-owner-tag --policy-assignment alz-pd-c3-prod `
  --definition-reference-id InheritOwnerTag --resource-discovery-mode ReEvaluateCompliance
```

Watch it run. Repeat the second command every minute until the state is final:

```powershell
Show-Remediation -RG $RG_CORP
```

> **What you should see**
>
> *Example output - do not type this:*
>
> ```text
> Task                   State      Total  Ok  Failed
> ---------------------  ---------  -----  --  ------
> alz-pd-rem-owner-tag   Succeeded     26  26       0
> ```
>
> While it runs the state is `Accepted` or `Evaluating`, then `Succeeded`.

> [!NOTE]
> **If some deployments fail**
>
> In the dry run all 26 deployments succeeded, **including the four network interfaces of the private endpoints** (`pe-alz-....nic....`). Azure manages those NICs itself and could in principle refuse a tag change. If your task reports **up to 4 failed** deployments and you can see in the Portal (remediation task, *Deployments* tab) that they are those NICs, that is acceptable: the owning private endpoint (`pe-alz-...`) **does** get the tag. Every other resource must succeed.
>
> If a *different* resource fails, open its deployment error. The usual cause is a missing role, or a role that Azure has not applied yet (see 4.2: wait, delete the failed task and create it again).

Now the **after** state:

```powershell
az resource list -g $RG_CORP --query "[].{name:name, owner:tags.Owner}" -o table
```

> **What you should see**
>
> The `owner` column now shows the Owner value of the resource group on every row - copied from the group's own `Owner` tag. The application did not restart: tag changes are metadata.

```powershell
Test-SampleApp
```

> **What you should see**
>
> `403` directly and backend health `Healthy` (and `200` through the gateway from a client the gateway accepts).

### Option B - start the remediation task in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Quick Access** > **Remediation**.

1. Policy > **Remediation**. On the tab **Policies to remediate** the columns are **Policy Definition**, **Assignment**, **Resources to Remediate** and **Scope**. Find the row **Inherit a tag from the resource group if missing** whose assignment is *ALZ PD - Chapter 3 REMEDIATE (PROD ...)*.
2. Click the **...** button at the end of the row and choose **Create remediation task**. (You can also open the assignment and click **Create remediation task** in its toolbar.) Keep the defaults and start the task with the button at the bottom of the form.
3. Open the tab **Remediation tasks**. The columns are **Start Time**, **Remediation State**, **Policy Definition**, **Scope**, **Locations**, **Remediated Resources** and **Last Updated**. Click **Refresh** until the state is final.
4. To read errors, click the task and open its **Deployments** tab.

> [!NOTE]
> **Not verified live**
>
> The form of the remediation task itself was not opened, because it would start a change. The button that starts the task is labelled **Remediate** in the Microsoft documentation. A Portal-created task also gets an automatic name instead of `alz-pd-rem-owner-tag`.

**Check the tag on one resource.** Open the resource `kv-alz-a1b2` and click **Tags** in the left menu (top group): `Owner` now appears next to `CostCenter` and your other tags.

> **What to say**
>
> Accountability was missing on all 26 resources. We did not edit them one by one: we wrote the rule once - 'resources inherit their owner from the resource group' - and Azure applied it. In the lab (section 4.5) the same rule tags every new resource automatically. In production we ran it once on purpose; making it automatic for every new resource is a change the owner approves first.

## 4.4  Fix production (2 of 2): diagnostic settings - effect DeployIfNotExists

> **Where to do this:** **PowerShell window** for the tasks and checks; **Azure Portal** for the final proof in Log Analytics.

Five tasks, one for each kind of resource that Chapter 2 checks for diagnostics. Each creates a diagnostic setting named `setByPolicy-LogAnalytics` that sends **all logs** to `law-alz-central`.

```powershell
foreach ($ref in 'DeployDiagKeyVault','DeployDiagAppService','DeployDiagPostgres','DeployDiagAppGateway','DeployDiagRedisEnterprise') {
  az policy remediation create -g $RG_CORP -n "alz-pd-rem-$ref" --policy-assignment alz-pd-c3-prod `
    --definition-reference-id $ref --resource-discovery-mode ReEvaluateCompliance -o none
}
Show-Remediation -RG $RG_CORP
```

> **What you should see**
>
> After a few minutes the tasks end like this (this is what the dry run produced): `DeployDiagKeyVault` **Succeeded** (1 deployment), `DeployDiagAppService` **Succeeded** (2), `DeployDiagPostgres` **Succeeded** (1), `DeployDiagAppGateway` **Failed** (expected - see the box below) and `DeployDiagRedisEnterprise` finished with **0 deployments** (in the dry run the built-in rule returned no result for the Redis database). Repeat the last command until the states are final.

**Prove 1 - the settings exist** (this lists the diagnostic settings of the resources the tasks touched):

```powershell
$q = "[?type=='Microsoft.KeyVault/vaults' || type=='Microsoft.Web/sites' ||"
$q += " type=='Microsoft.DBforPostgreSQL/flexibleServers' || type=='Microsoft.Network/applicationGateways'].id"
$ids  = az resource list -g $RG_CORP --query $q -o tsv
$ids += "$SCOPE_CORP/providers/Microsoft.Cache/redisEnterprise/$REDIS/databases/default"
foreach ($id in $ids) {
  '{0,-32} {1}' -f ($id -split '/')[-1], (az monitor diagnostic-settings list --resource $id --query "[].name" -o tsv)
}
```

> **What you should see**
>
> *Example output - do not type this:*
>
> ```text
> app-alz-backend-a1b2       setByPolicy-LogAnalytics
> app-alz-frontend-a1b2      setByPolicy-LogAnalytics
> psql-alz-a1b2              setByPolicy-LogAnalytics
> kv-alz-a1b2                setByPolicy-LogAnalytics
> agw-alz-web                diag-agw-alz
> default
> ```
>
> `setByPolicy-LogAnalytics` exists on **four** resources. The gateway keeps its own earlier setting `diag-agw-alz`, and `default` (the Redis database) has no setting from this task.

> [!WARNING]
> **COMMON TRAP - the Application Gateway task fails with 'Data sinks can't be reused'**
>
> The gateway already has a diagnostic setting of its own (`diag-agw-alz`, created by the reference landing zone) that sends the log category `ApplicationGatewayAccessLog` to `law-alz-central`. Azure does not accept a second setting that uses the same log category and the same workspace on the same resource, so the task `alz-pd-rem-DeployDiagAppGateway` fails with *Data sinks can't be reused in different settings on the same category for the same resource*. The gateway's logs **do** reach the workspace; the policy simply does not recognise a setting it did not create, so the gateway stays non-compliant.
>
> You have three honest choices. Pick one and say it out loud:
>
> 1. **Explain it and keep the finding.** This is what the rest of this runbook does: the scorecard in 4.8 shows the gateway as the one remaining F5 finding.
> 2. **Record a *Mitigated* exemption** for `DiagAppGateway` on the gateway, with the reason 'diagnostics already sent by diag-agw-alz', exactly like the exemptions in 4.7.
> 3. **Replace the existing setting.** Delete `diag-agw-alz` and run the task again, so that the policy owns the setting. Do not do this while anyone relies on the logs: they stop for a few minutes.

**Prove 2 - logs really arrive.** A diagnostic setting only matters if data flows. Send some traffic to the application, wait, and look in Log Analytics.

```powershell
1..6 | ForEach-Object { try { Invoke-WebRequest "https://$FE.azurewebsites.net/" -UseBasicParsing -TimeoutSec 20 | Out-Null } catch { } }
Test-SampleApp
"Now wait 5 to 15 minutes before running the next block (first logs arrive slowly)."
```

After the wait, run this query. It does not matter which table the logs land in: the query finds them all.

> [!NOTE]
> The first time you use `az monitor log-analytics query`, Azure CLI may ask to install the *log-analytics* extension. Answer **Y** (yes).

```powershell
$LAW_GUID = az monitor log-analytics workspace show -g $RG_MGMT -n $LAW --query customerId -o tsv
az monitor log-analytics query -w $LAW_GUID -o table --analytics-query `
  "search '$FE' | where TimeGenerated > ago(2h) | summarize Rows = count() by `$table"
```

> **What you should see**
>
> One or more table names with a row count, for example `AppServiceHTTPLogs` and `AppServiceIPSecAuditLogs`. The 403 answers you provoked with the direct calls appear there, with the caller's address and the status code. In the dry run the first query (about 10 to 13 minutes after the settings were deployed and 4 minutes after the test traffic) returned `AppServicePlatformLogs` 47, `AppServiceConsoleLogs` 42, `AppServiceIPSecAuditLogs` 66 and `AppServiceHTTPLogs` 57 rows.
>
> If the answer is empty, wait another 10 minutes and run the query again.

### Option B - read the logs in the Azure Portal

> **Where to do this:** **Azure Portal** - the Log Analytics workspace `law-alz-central` > **Logs**.

1. Top search box: `law-alz-central` > open it (resource group `rg-alz-mgmt`). In the left menu click **Logs**.
2. Two pop-ups appear: **Welcome to Log Analytics** and **Queries hub**. Close each with its **X**.
3. The editor opens in **Simple mode**. In the drop-down **Choose working mode** select **KQL mode** (the **Run** button exists only there).
4. Paste this query. (`$table` is a KQL keyword, not a PowerShell variable.)

```kusto
// Replace the name with the name of your front-end web app
search 'app-alz-frontend-a1b2'
| where TimeGenerated > ago(2h)
| summarize Rows = count() by $table
```

1. Click the **Time range** pill and choose **Last 4 hours**. Click **Run** - the first click may open a small menu: choose **Run** in it (or press **Shift+Enter**).
2. Open the **Results** tab. **What you should see:** one or more table names (for example *AppServiceHTTPLogs*) with a row count.

**See the diagnostic setting itself:** open the web app `app-alz-frontend-a1b2`, then in its left menu **Monitoring** > **Diagnostic settings**. Before the remediation the page said *No diagnostic settings defined*; now the table lists a setting created by the policy, with **Log Analytics workspace** = `law-alz-central`.

> [!WARNING]
> **COMMON TRAP - nothing in the logs yet**
>
> The first events can take **10 to 20 minutes** to show up in a new workspace connection. This is normal Azure Monitor behaviour, not a failure. Prepare this step early, and do something else while you wait.

> **What to say**
>
> Before, an incident in the application would have left no trace in our central workspace. Now the application's services send their logs to one place - the gateway already did, with its own setting - and nobody had to configure the rest one by one. In the lab (section 4.5) the same rule also covers every new resource automatically. In production we ran it once on purpose; switching on automatic enforcement for new resources is a change the owner approves first.

## 4.5  Fix at birth: new lab resources are corrected automatically

> **Where to do this:** **PowerShell window.** Wait about **10 minutes** after step 4.2 before you start, so that the new lab assignment is active.

### Modify beats Deny - the same command that was refused in Test 7

In Chapter 1 (Test 7) this command was **denied**, because the NSG had no tags. Run exactly the same command again:

```powershell
az network nsg create -g $RG_LAB -n nsg-pd-notags -l $LOC -o none
az network nsg show -g $RG_LAB -n nsg-pd-notags --query tags -o json
```

> **What you should see**
>
> **No error this time.** The NSG exists, and it has tags you did not type:
>
> *Example output - do not type this:*
>
> ```text
> {
>   "CostCenter": "ALZ-Demo",
>   "Owner": "demo-owner"
> }
> ```

> **Why this matters**
>
> Azure Policy evaluates **Modify first and Deny second**. The Chapter 3 rule added the two tags to the request, so by the time the Chapter 1 *Require a tag* rule looked, the tags were there and the request was allowed. Both assignments are enforcing in the lab at the same time.
>
> This is the best pattern for tags: **Deny** gives you a safety net, **Modify** gives users a smooth experience. Use both.

### Create the compliant Key Vault and let diagnostics deploy themselves

This is the 'safe' half of Test 5: a Key Vault **with** purge protection. It also lets you watch the DeployIfNotExists effect work on a *new* resource.

> [!CAUTION]
> **Irreversible**
>
> **Purge protection cannot be switched off** once it is on. After you delete this vault in Part 5 it stays in a *soft-deleted* state for the retention period (7 days) and its name cannot be reused until then. It costs nothing. The name contains the run number (`$RUN`), so a repeat run uses a different name.

```powershell
az keyvault create -g $RG_LAB -n $KV_OK -l $LOC --retention-days 7 --enable-rbac-authorization true `
  --enable-purge-protection true --tags $TAGS --query "properties.provisioningState" -o tsv
```

> **What you should see**
>
> `Succeeded`. The Chapter 1 rule that refused the vault without purge protection accepts this one.

Wait **15 to 20 minutes** - DeployIfNotExists runs *after* the resource exists. Then check:

```powershell
$KVOK_ID = az keyvault show -g $RG_LAB -n $KV_OK --query id -o tsv
az monitor diagnostic-settings list --resource $KVOK_ID --query "[].{name:name, workspace:workspaceId}" -o table
```

> **What you should see**
>
> A row with `setByPolicy-LogAnalytics` and the workspace `.../workspaces/law-alz-central`. You never created that setting.

## 4.6  Back up the lab VM - DeployIfNotExists by tag

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

The lab VM carries the tag `Backup=daily`. A built-in policy backs up every VM with a given tag into an existing vault in the same region. First create the vault (empty, free until something is protected) and read its default backup policy:

```powershell
az backup vault create -g $RG_LAB -n $RSV -l $LOC --tags $TAGS -o none
$BACKUP_POLICY_ID = az backup policy show -g $RG_LAB -v $RSV -n DefaultPolicy --query id -o tsv
$BACKUP_POLICY_ID
```

> **What you should see**
>
> A long ID that ends with `/backupPolicies/DefaultPolicy`.

> [!NOTE]
> **Standard or enhanced backup policy?**
>
> `DefaultPolicy` is the **Standard** policy: one backup a day, simple and cheap, which is right for this demo. Azure Backup also has a newer **Enhanced** policy (several backups a day, and support for Trusted Launch VMs). Remember this - it explains the Trusted Launch decision in section 4.7.

Assign the built-in policy **directly** (not as part of an initiative - this is the other way of assigning). It needs its own identity and two roles:

```powershell
@{ effect            = @{ value = 'DeployIfNotExists' }
   vaultLocation     = @{ value = $LOC }
   backupPolicyId    = @{ value = $BACKUP_POLICY_ID }
   inclusionTagName  = @{ value = 'Backup' }
   inclusionTagValue = @{ value = @('daily') } } |
  ConvertTo-Json -Depth 6 | Set-Content "$WORK/vmbackup-assign.json" -Encoding ascii

az policy assignment create --name "alz-pd-c3-lab-vmbackup" `
  --display-name "ALZ PD - Back up VMs tagged Backup=daily (LAB)" `
  --policy "345fa903-145c-4fe1-8bcd-93ec2adccde8" `
  --scope $SCOPE_LAB `
  --params "@$WORK/vmbackup-assign.json" --enforcement-mode DoNotEnforce `
  --mi-system-assigned --location $LOC

$MI_BK = az policy assignment show --name alz-pd-c3-lab-vmbackup --scope $SCOPE_LAB --query identity.principalId -o tsv
Start-Sleep -Seconds 45
az role assignment create --assignee-object-id $MI_BK --assignee-principal-type ServicePrincipal `
  --role "Virtual Machine Contributor" --scope $SCOPE_LAB -o none
az role assignment create --assignee-object-id $MI_BK --assignee-principal-type ServicePrincipal `
  --role "Backup Contributor" --scope $SCOPE_LAB -o none

"Waiting 2 minutes so that Azure can apply the new roles..."
Start-Sleep -Seconds 120
az policy remediation create -g $RG_LAB -n alz-pd-rem-vm-backup --policy-assignment alz-pd-c3-lab-vmbackup `
  --resource-discovery-mode ReEvaluateCompliance
```

> [!NOTE]
> **Built-in policies are passed by GUID only**
>
> In `--policy` the built-in definition is given as its bare GUID. The long form `/providers/Microsoft.Authorization/policyDefinitions/<guid>` failed with `PolicyDefinitionNotFound` in Azure CLI 2.91. (Your own custom definitions, which live in your subscription, are passed with their full ID, as in the earlier steps.)

Wait 5 to 10 minutes, then check that the VM is protected:

```powershell
Show-Remediation -RG $RG_LAB
az backup item list -g $RG_LAB -v $RSV --backup-management-type AzureIaasVM --workload-type VM `
  --query "[].{vm:properties.friendlyName, protectionState:properties.protectionState, status:properties.protectionStatus, policy:properties.policyName}" -o table
```

> **What you should see**
>
> The task is `Succeeded` with 1 successful deployment. The backup item list shows a row for `vm-pd-lab01`. Its protection state may say **IRPending** (*initial recovery point pending*): the first backup runs in the vault's schedule. That is normal. In the dry run the row read `vm-pd-lab01`, `IRPending`, `Healthy`, `DefaultPolicy`.
>
> The command selects its own columns because a plain `az backup item list -o table` prints `Table output unavailable` in Azure CLI 2.91.

### See the backup in the Azure Portal

> **Where to do this:** **Azure Portal** - the Recovery Services vault `rsv-alz-pd-lab`.

1. Top search box: `rsv-alz-pd-lab` > open the vault.
2. In the left menu open **Backup items**, then **Azure Virtual Machine**. The VM `vm-pd-lab01` is listed with its protection status.

> [!NOTE]
> **Not verified live**
>
> The vault does not exist until you create it in this step, so its menu names were taken from the Microsoft documentation and may differ slightly.

> [!CAUTION]
> **What backup protection does not prove**
>
> Policy proves that backup is **configured**. It does not prove that a restore **works** or that you meet any recovery-time target. A restore test is a separate, scheduled exercise.

> **What to say**
>
> The VM was unprotected. One tag - `Backup=daily` - decided that it must be backed up, and Azure did the work. This assignment is deliberately set to `DoNotEnforce` so that you control the timing: a new VM with the same tag would be reported as non-compliant, and one more remediation task would protect it. After approval you would switch the assignment to `Default`, and Azure would protect new tagged VMs by itself.

## 4.7  When remediation is not the answer: exemptions and engineering decisions

Some findings must **not** be 'fixed' by policy. For each one you make a decision and you **write it down**. Azure Policy gives you a proper way to do that: the **exemption**.

| Category | Use it when | Example here |
| --- | --- | --- |
| **Mitigated** | The risk is real but another control covers it. | The web apps allow platform-level public access, but an access restriction and the WAF allow only the gateway. |
| **Waiver** | The control cannot be met (now), and the owner accepts the risk for a limited time. | The demo gateway has an HTTP listener; PostgreSQL geo-backup does not exist in Indonesia Central. |

> [!NOTE]
> **Good exemption hygiene**
>
> Always add a **description** (the reason), an **expiry date** and the **narrowest scope** (one resource). An exemption without an expiry date quietly becomes permanent.

### Create the four exemptions

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

```powershell
$C2_PROD = "$SCOPE_CORP/providers/Microsoft.Authorization/policyAssignments/alz-pd-c2-prod"
$EXPIRES = [DateTime]::UtcNow.AddDays(90).ToString("yyyy-MM-dd'T'00:00:00'Z'", [System.Globalization.CultureInfo]::InvariantCulture)   # 90 days from today

# 1 and 2 - MITIGATED: the two web apps
az policy exemption create --name "alz-pd-ex-appsvc-frontend" `
  --display-name "Frontend web app: public access limited to the gateway" `
  --description "Access restriction allows only the Application Gateway (WAF). A direct call returns 403." `
  --policy-assignment $C2_PROD --policy-definition-reference-ids AppServicePublicAccess `
  --exemption-category Mitigated --expires-on $EXPIRES `
  --scope "$SCOPE_CORP/providers/Microsoft.Web/sites/$FE"

az policy exemption create --name "alz-pd-ex-appsvc-backend" `
  --display-name "Backend web app: public access limited to the frontend subnet" `
  --description "Access restriction allows only the frontend subnet. A direct call returns 403." `
  --policy-assignment $C2_PROD --policy-definition-reference-ids AppServicePublicAccess `
  --exemption-category Mitigated --expires-on $EXPIRES `
  --scope "$SCOPE_CORP/providers/Microsoft.Web/sites/$BE"

# 3 - WAIVER: the demo HTTP listener
az policy exemption create --name "alz-pd-ex-appgw-http" `
  --display-name "Demo gateway: HTTP listener (no certificate in the demo)" `
  --description "The demo has no public DNS name or certificate. The production design uses HTTPS with TLS 1.2 or newer and a certificate in Key Vault." `
  --policy-assignment $C2_PROD --policy-definition-reference-ids AppGatewayHttpsListener `
  --exemption-category Waiver --expires-on $EXPIRES `
  --scope "$SCOPE_CORP/providers/Microsoft.Network/applicationGateways/$AGW"

# 4 - WAIVER: PostgreSQL geo-redundant backup
az policy exemption create --name "alz-pd-ex-pg-geobackup" `
  --display-name "PostgreSQL: geo-redundant backup not available in Indonesia Central" `
  --description "Indonesia Central has no paired region, so geo-redundant backup is not offered. Local backups (7 days) remain." `
  --policy-assignment $C2_PROD --policy-definition-reference-ids PostgresGeoBackup `
  --exemption-category Waiver --expires-on $EXPIRES `
  --scope "$SCOPE_CORP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$PG"
```

> **What you should see**
>
> Four JSON blocks, each with the `exemptionCategory`, the `expiresOn` date and your description.

List them. `--disable-scope-strict-match` is needed because each exemption sits on one resource, not on the subscription:

```powershell
az policy exemption list --disable-scope-strict-match --query "[?starts_with(name,'alz-pd-')].{name:name, category:exemptionCategory, expires:expiresOn}" -o table
```

> **What you should see**
>
> A table with four rows - the four exemption names with their category (`Mitigated` or `Waiver`) and the expiry date.

### Option B - create an exemption in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Assignments** > the assignment > **Create exemption**.

1. Policy > **Authoring** > **Assignments**; **Scope** = `rg-alz-corp-prod`; click **ALZ PD - Chapter 2 DETECT (PROD)**.
2. In the toolbar click **Create exemption**. (The **Exemptions** list page cannot create one: its only button is *Refresh*.)
3. Tab **Basics**: next to **Exemption scope** click **...** and choose the web app `app-alz-frontend-a1b2`. In **Exemption name** type a name. In **Exemption category** choose **Mitigated** (the other value is **Waiver**). Turn on **Exemption expiration setting** and choose a date. In **Exemption description** write the reason. For an initiative assignment also select the policy to exempt, *AppServicePublicAccess*.
4. Click **Review + create** and then **Create**.
5. To see the result open Policy > **Authoring** > **Exemptions**: the columns are **Name**, **Assignments**, **Scope**, **Exemption category**, **Created by** and **Expiration date**.

> [!NOTE]
> **Not verified live**
>
> The date picker (it only appears after the expiration switch is turned on) and the policy selector for initiative assignments were not opened. The commands in this step are the reliable way.

Exemptions trigger a new evaluation. After about 15 to 30 minutes the findings show the state **Exempt** instead of **NonCompliant** (in the dry run all four after about 30 minutes, the PostgreSQL one last):

```powershell
Show-Compliance -RG $RG_CORP -Assignment alz-pd-c2-prod -State Exempt
```

> **What you should see**
>
> Four rows: the two web apps (`AppServicePublicAccess`), the gateway (`AppGatewayHttpsListener`) and the database (`PostgresGeoBackup`).

### The decisions that stay with the owner

| Finding | Why policy does not fix it | What the owner decides |
| --- | --- | --- |
| Storage **infrastructure encryption** (F4) | It can only be chosen when the storage account is created. | Create a new account with `--require-infrastructure-encryption true` (you already did this for the lab account) and migrate the data - or accept the risk and record an exemption. |
| Scale set **encryption at host** (F4) | It needs a one-time subscription feature registration and a re-deployment of the scale set. | Plan the change with the next release of the worker image. |
| Key Vault **purge protection** (F4) | It is **irreversible**. Enabling it on the production vault is a one-way decision. | The owner decides. The lab vault shows what 'compliant' looks like. |
| Lab VM **Trusted Launch** (F7) | It is an engineering change that restarts the VM. Azure also refuses it while the VM is protected with the **Standard** backup policy - and step 4.6 left the lab VM protected that way. | Move the backup to the **Enhanced** policy first (a one-way change that costs a little more), then upgrade the VM. Plan it with the VM owner. Not done in this demo. |

> [!NOTE]
> **Why not fix the trusted launch finding live?**
>
> The lab VM is Generation 2, so Azure supports an in-place upgrade to Trusted Launch. Microsoft documents one condition: a VM that is backed up must use the **Enhanced** backup policy; a VM protected with the **Standard** policy cannot be upgraded. Step 4.6 left the lab VM in exactly that state, so the upgrade would be refused.
>
> This is a good thing to show honestly. Policy found a real weakness, and fixing it needs a small plan (move the backup to the Enhanced policy, then upgrade), not a one-line command. The two Microsoft Learn pages are in Appendix G.

## 4.8  Prove it: the before-and-after scorecard

> **Where to do this:** **PowerShell window.**

Ask Azure to evaluate once more, wait about 15 minutes, and then read the results the same way you did in Chapter 2. Everything you fixed should have turned green.

```powershell
az policy state trigger-scan -g $RG_CORP --no-wait
az policy state trigger-scan -g $RG_LAB --no-wait
# ... wait about 15 minutes, then:
Show-Compliance -RG $RG_CORP -Assignment alz-pd-c1-prod
Show-Compliance -RG $RG_CORP -Assignment alz-pd-c2-prod
Show-Compliance -RG $RG_LAB  -Assignment alz-pd-c2-lab
Show-Scorecard -Targets "${RG_CORP}:alz-pd-c1-prod", "${RG_CORP}:alz-pd-c2-prod", "${RG_LAB}:alz-pd-c2-lab"
```

| Check | Before (Part 2 and 3) | After (now) | How it got there |
| --- | --- | --- | --- |
| Owner tag (F9) | 26 non-compliant | **0** (in the dry run all 26 were tagged, including the four private-endpoint NICs) | Modify remediation task (4.3) |
| Diagnostic settings (F5) | 5 non-compliant | **1** - the gateway (see the trap in 4.4) | DeployIfNotExists tasks (4.4) |
| Web app public access (F2) | 2 non-compliant | **2 Exempt** (Mitigated) | Exemption (4.7) |
| Gateway HTTP listener (F3) | 1 non-compliant | **1 Exempt** (Waiver) | Exemption (4.7) |
| PostgreSQL geo-backup (F6) | 1 non-compliant | **1 Exempt** (Waiver) | Exemption (4.7) |
| Lab VM backup (F6) | 1 non-compliant | **0** | DeployIfNotExists by tag (4.6) |
| Lab VM Trusted Launch (F7) | 1 non-compliant | **1 non-compliant** | Needs a decision (Enhanced backup policy first) |
| Storage infrastructure encryption (F4) | 1 non-compliant | **1 non-compliant** | Needs a decision (new account) |
| Scale set encryption at host (F4) | 1 non-compliant | **1 non-compliant** | Needs a decision (re-deploy) |
| Key Vault purge protection (F4) | 1 non-compliant | **1 non-compliant** | Needs a decision (irreversible) |

### The application never noticed

```powershell
Test-SampleApp
```

> **What you should see**
>
> **200** through the gateway (from a client the gateway accepts), **403** directly and backend health **Healthy** - exactly the values from step 1.4. Three chapters of governance, and the application did not restart or change.

### Save the evidence

```powershell
az policy state list -g $RG_CORP -o json | Out-File "$WORK/evidence/after-policy-states.json" -Encoding utf8
az resource list -g $RG_CORP -o json | Out-File "$WORK/evidence/after-resources.json" -Encoding utf8
$rows = az policy state list -g $RG_CORP --policy-assignment alz-pd-c2-prod -o json | ConvertFrom-Json
$rows | Select-Object @{n='Family';e={$_.policyDefinitionGroupNames -join ','}}, @{n='Check';e={$_.policyDefinitionReferenceId}}, `
  @{n='Resource';e={($_.resourceId -split '/')[-1]}}, complianceState |
  Export-Csv "$WORK/evidence/findings-c2-prod.csv" -NoTypeInformation
Get-ChildItem "$WORK/evidence"
```

> **What you should see**
>
> Five files in `alz-policy-demo/evidence`: the two *before* JSON files from step 1.3, the two *after* JSON files, and one CSV that opens in Excel.

> **What to say**
>
> We started with 26 resources without an owner, five services without central logs, and a list of findings nobody had. We finish with owners everywhere, logs in one workspace (the gateway's through its own setting), four findings formally accepted with a reason and an expiry date, and four honest engineering decisions - three in production and one in the lab - and the gateway's back end stayed Healthy the whole time.

## 4.9  Optional: the Activity Log (a subscription-level check)

> **Where to do this:** **PowerShell window.**

The **Activity Log** records every management operation in the subscription (who created, changed or deleted what). A built-in policy checks that it is exported to a central workspace. Because it works at **subscription** level, you will use it for *reporting only*.

```powershell
@{ logAnalytics = @{ value = $LAW_ID }; effect = @{ value = 'DeployIfNotExists' } } |
  ConvertTo-Json -Depth 5 | Set-Content "$WORK/actlog-assign.json" -Encoding ascii

az policy assignment create --name "alz-pd-sub-actlog" `
  --display-name "ALZ PD - Activity Log goes to the central workspace (report only)" `
  --policy "2465583e-4e78-4c15-b6be-a36cbc7c8b0f" `
  --scope $SCOPE_SUB `
  --params "@$WORK/actlog-assign.json" --enforcement-mode DoNotEnforce `
  --mi-system-assigned --location $LOC
```

After about 30 minutes the subscription shows as **non-compliant** if its Activity Log is not exported to `law-alz-central` (the usual case: the reference landing zone does not configure it). The assignment has a managed identity because Azure requires one for this definition (it can deploy a diagnostic setting), but it gets **no role** - on purpose: nothing may be deployed from here.

> [!CAUTION]
> **Do not remediate this one in a subscription you share**
>
> A remediation task would create a **subscription-level diagnostic setting**, which sends the Activity Log of the **whole subscription** into `law-alz-central`. A subscription can hold only **five** such settings, and some may already be used. Show the finding; describe the fix; do not run it here. In a real landing zone the same policy would be assigned once, at the management group, with the identity and the workspace designed for it.

---

[Runbook index](README.md) &middot; Previous: [Part 3 - Chapter 2: DETECT - find the gaps](03-chapter-2-detect.md) &middot; Next: [Part 5 - Wrap-up, reset and clean-up](05-wrap-up-and-clean-up.md)
