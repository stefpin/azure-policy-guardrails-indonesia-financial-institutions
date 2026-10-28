# Part 1 - Prepare the stage

[Runbook index](README.md) &middot; Previous: [Part 0 - Before you start](00-before-you-start.md) &middot; Next: [Part 2 - Chapter 1: PREVENT - block unsafe deployments](02-chapter-1-prevent.md)

In this part you sign in, check that the sample application is healthy, create a small lab, and build the **policy library** (five custom definitions and three initiatives). Nothing here blocks or changes production. Plan about **60 to 90 minutes**, most of it waiting for Azure.

## 1.1  Sign in to Azure

> **Where to do this:** **PowerShell window** (Windows Terminal, PowerShell tab). Then the **Azure Portal** in Microsoft Edge for the check at the end.

`az login` opens a browser window. Sign in with the account that owns your subscription (a work, school or personal account that has access to it). The window closes by itself when you are signed in. Replace `<your-subscription-id>` in the second command with your own subscription ID; if you do not know it, run `az account list --query "[].{name:name, id:id}" -o table` after signing in.

```powershell
az login
az account set --subscription "<your-subscription-id>"
az account show --query "{subscription:name, subscriptionId:id, tenantId:tenantId, signedInAs:user.name}" -o yaml
```

> **What you should see**
>
> Four lines - `subscription`, `subscriptionId`, `tenantId` and `signedInAs` - with your own values. Check that `subscriptionId` is the subscription that holds your landing zone.

**Check that you are allowed to create policies.** You need the **Owner** role (an Owner role inherited from a management group is fine):

```powershell
$me = az ad signed-in-user show --query id -o tsv
az role assignment list --assignee $me --all `
  --query "[?roleDefinitionName=='Owner'].{role:roleDefinitionName, scope:scope}" -o table
```

> **What you should see**
>
> At least one row with the role **Owner**. The scope is your subscription, or a management group above it (an inherited Owner role is fine).

### Check the same thing in the Azure Portal

> **Where to do this:** **Azure Portal** in Microsoft Edge: https://portal.azure.com

1. Open https://portal.azure.com. If you see **Pick an account**, choose the account you used for `az login`.
2. Hover the mouse over your **account button** (top right corner, it shows your e-mail). The tooltip must show the directory (tenant) that holds your subscription.
3. Click the **search box** at the top (it says *Search resources, services, and docs (G+/)*). Type the name of your subscription and click it in the results.
4. On the **Overview** page, look at the **Essentials** box. **My role** must say **Owner**.

> [!NOTE]
> **The portal has changed**
>
> There is no longer a *Directories + subscriptions* icon in the top bar. To see or change the directory, click the **Settings** gear (it opens *Portal settings | Directories + subscriptions*) or the **Switch directory** link in the account menu. The subscription is shown as the **Scope** pill at the top of every Policy page.

> [!WARNING]
> **COMMON TRAP - 'Interactive authentication is needed'**
>
> Some tenants require multi-factor authentication for write operations (for example through a Conditional Access policy or an inherited Azure Policy). If a command later fails with *'Interactive authentication is needed'* or mentions a *claims challenge*, run this once and try again:
>
> ```powershell
> az logout
> az login --scope https://management.core.windows.net//.default
> ```

## 1.2  Prepare your PowerShell window

> **Where to do this:** **PowerShell window.** Paste the whole block. Do this again every time you open a new window.

The block creates **variables** (named values such as `$SUB` for the subscription ID) so that you never have to type a long name twice. It also creates a working folder `alz-policy-demo` in your user folder and moves PowerShell into it.

```powershell
# ---- Azure Policy guardrails demo variables: paste once in every new PowerShell window ----
$SUB    = "<your-subscription-id>"   # CHANGE ME: az account show --query id -o tsv
$LOC    = "indonesiacentral"
$SFX    = "a1b2"                  # CHANGE ME if needed: the suffix of your landing zone's resource names
$RUN    = "01"                      # use 02, 03 ... if you repeat the demo
$OWNER  = "demo-owner"                # CHANGE ME: your alias - used in the Owner tag of lab resources
$TAGS   = @("CostCenter=ALZ-Demo", "Owner=$OWNER")

# Resource groups (they already exist)
$RG_HUB  = "rg-alz-hub"
$RG_MGMT = "rg-alz-mgmt"
$RG_CORP = "rg-alz-corp-prod"
$RG_LAB  = "rg-alz-policy-lab"

# Sample application and platform resources (they already exist)
$AGW   = "agw-alz-web"
$LAW   = "law-alz-central"
$FE    = "app-alz-frontend-$SFX"
$BE    = "app-alz-backend-$SFX"
$PG    = "psql-alz-$SFX"
$REDIS = "redis-alz-$SFX"
$ST    = "stalz$SFX"
$KV    = "kv-alz-$SFX"

# Scopes (an Azure "scope" is the path of the thing a policy applies to)
$SCOPE_SUB  = "/subscriptions/$SUB"
$SCOPE_CORP = "$SCOPE_SUB/resourceGroups/$RG_CORP"
$SCOPE_LAB  = "$SCOPE_SUB/resourceGroups/$RG_LAB"
$LAW_ID     = "$SCOPE_SUB/resourceGroups/$RG_MGMT/providers/Microsoft.OperationalInsights/workspaces/$LAW"

# New things this runbook creates (lab only)
$VM     = "vm-pd-lab01"
$RSV    = "rsv-alz-pd-lab"
$ST_BAD = "stalzpdbad$RUN$SFX"
$ST_OK  = "stalzpdlab$RUN$SFX"
$KV_BAD = "kv-alz-pd-bad-$RUN-$SFX"
$KV_OK  = "kv-alz-pd-ok-$RUN-$SFX"

# Working folder for the JSON files
$WORK = "$HOME/alz-policy-demo"
if ($SUB -like '<*') { throw 'Set $SUB at the top of this block first (az account show --query id -o tsv), then paste it again.' }
New-Item -ItemType Directory -Force -Path "$WORK/evidence" | Out-Null
az account set --subscription $SUB
Set-Location $WORK
"Ready. Subscription: " + (az account show --query name -o tsv)
```

> **What you should see**
>
> The last line prints `Ready. Subscription: ` followed by the name of your subscription.

> [!NOTE]
> `$TAGS` is a list of two values. When a command contains `--tags $TAGS`, PowerShell turns it into `--tags CostCenter=ALZ-Demo Owner=demo-owner`. Change `$OWNER` in the block to your own alias before you paste it.

> [!IMPORTANT]
> **Match the names of your landing zone**
>
> `$SFX` must be the same four-character suffix that you set in the reference landing zone's `scripts/00-variables.ps1` (`$SFX` there), because Azure Storage, Key Vault and web app names include it. If your landing zone uses other names, change the matching variables in this block - every later command reads them.

## 1.3  Load the helper commands and take a 'before' snapshot

> **Where to do this:** **PowerShell window.**

The block defines six small commands that you will use many times. You paste them once; they then work like new commands in this window.

| Command | What it does |
| --- | --- |
| `Show-Assignments` | Lists every `alz-` policy assignment with its enforcement mode and scope. |
| `Show-Enforcing` | The safety check. It prints **nothing** when no `alz-` assignment is enforcing. |
| `Show-Remediation` | Shows the progress of the remediation tasks in a resource group. |
| `Show-Compliance` | Lists the resources that are non-compliant (or compliant) for one assignment. |
| `Show-Scorecard` | Counts the checks per control family (F1 to F9). |
| `Test-SampleApp` | Asks the application two questions: *through the gateway* (expect 200) and *directly* (expect 403) - and prints the gateway's **backend health** (expect Healthy). It is your quick check that policy did not break the application. |

```powershell
function Show-Assignments {
  # Lists alz- assignments with their enforcement mode and scope
  param([string]$Filter = 'alz-*')
  $all = az policy assignment list --disable-scope-strict-match -o json | ConvertFrom-Json
  $all | Where-Object { $_.name -like $Filter } | Sort-Object name | ForEach-Object {
    [pscustomobject]@{ Name = $_.name; Mode = $_.enforcementMode; Scope = ($_.scope -split '/')[-1] }
  } | Format-Table -AutoSize
}

function Show-Enforcing {
  # The safety check: prints NOTHING when no alz- assignment is enforcing
  $all = az policy assignment list --disable-scope-strict-match -o json | ConvertFrom-Json
  $all | Where-Object { $_.name -like 'alz-*' -and $_.enforcementMode -ne 'DoNotEnforce' } |
    Select-Object name, enforcementMode
}

function Show-Remediation {
  # Progress of the remediation tasks in one resource group
  param([string]$RG)
  $q = "[].{task:name, state:provisioningState, total:deploymentStatus.totalDeployments,"
  $q += " ok:deploymentStatus.successfulDeployments, failed:deploymentStatus.failedDeployments}"
  az policy remediation list -g $RG --query $q -o table
}

function Show-Compliance {
  # Shows the resources in one state (default NonCompliant) for one assignment
  param([string]$RG, [string]$Assignment, [string]$State = 'NonCompliant')
  $rows = az policy state list -g $RG --policy-assignment $Assignment `
            --filter "complianceState eq '$State'" -o json | ConvertFrom-Json
  if (-not $rows) { Write-Host "No $State rows for $Assignment in $RG" -ForegroundColor Green; return }
  $rows | ForEach-Object {
    [pscustomobject]@{
      Family   = ($_.policyDefinitionGroupNames -join ',')
      Check    = $_.policyDefinitionReferenceId
      Resource = ($_.resourceId -split '/')[-1]
      Type     = ($_.resourceType -replace '^Microsoft\.', '')
    }
  } | Sort-Object Family, Check, Resource | Format-Table -AutoSize
}

function Show-Scorecard {
  # Counts checks per control family. Targets look like  "rg-name:assignment-name"
  param([string[]]$Targets)
  $rows = foreach ($t in $Targets) {
    $rg, $asg = $t -split ':'
    $one = az policy state list -g $rg --policy-assignment $asg -o json | ConvertFrom-Json
    $one
  }
  $rows | Where-Object { $_.policyDefinitionGroupNames[0] } |
    Group-Object { $_.policyDefinitionGroupNames[0] } | Sort-Object Name | ForEach-Object {
      $g = $_.Group
      [pscustomobject]@{
        Family       = $_.Name
        Checks       = $g.Count
        Compliant    = @($g | Where-Object complianceState -eq 'Compliant').Count
        NonCompliant = @($g | Where-Object complianceState -eq 'NonCompliant').Count
        Exempt       = @($g | Where-Object complianceState -eq 'Exempt').Count
      }
    } | Format-Table -AutoSize
}

function Test-SampleApp {
  # The "did we break the application?" test.
  # Expected: 200 through the gateway (from a client the gateway accepts), 403 direct, backend health Healthy.
  $ip = az network public-ip show -g $RG_CORP -n pip-alz-appgw --query ipAddress -o tsv
  $tests = @(@('Through the gateway', "http://$ip/"), @('Directly to the web app', "https://$FE.azurewebsites.net/"))
  foreach ($t in $tests) {
    try { $code = (Invoke-WebRequest -Uri $t[1] -UseBasicParsing -TimeoutSec 30).StatusCode }
    catch { $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 'no answer' } }
    '{0,-26} {1}' -f $t[0], $code
  }
  $health = az network application-gateway show-backend-health -g $RG_CORP -n $AGW `
    --query "backendAddressPools[].backendHttpSettingsCollection[].servers[].health" -o tsv
  '{0,-26} {1}' -f 'Gateway backend health', (@($health) -join ', ')
}
```

Now take the **before snapshot**. First the policy view:

```powershell
Show-Assignments
(az resource list -g $RG_CORP --query "[].id" -o tsv | Measure-Object).Count      # how many sample-application resources
(az resource list -g $RG_LAB  --query "[].id" -o tsv | Measure-Object).Count      # how many lab resources
```

> **What you should see**
>
> `Show-Assignments` prints **8 rows**, every one with Mode **DoNotEnforce**: `alz-allowed-locations`, `alz-no-public-ip-nic`, `alz-require-costcenter-tag`, `alz-inno-allowed-locations`, `alz-inno-no-public-ip`, `alz-inno-require-tag`, `alz-sandbox-no-peering`, `alz-baseline-lab`.
>
> Then `26` (sample-application resources in the dry run; your number may differ a little) and `0` (the lab is empty).

Save a copy of the current state as evidence. You will compare against it in Part 5.

```powershell
az resource list -g $RG_CORP -o json | Out-File "$WORK/evidence/before-resources.json" -Encoding utf8
az policy state list -g $RG_CORP -o json | Out-File "$WORK/evidence/before-policy-states.json" -Encoding utf8
Get-ChildItem "$WORK/evidence"
```

### Make sure the resource groups have an Owner tag

> **Where to do this:** **PowerShell window.**

Chapter 3 fixes the missing `Owner` tag by **copying the tag from the resource group** of each resource - the production group for the real application, the lab group for new lab resources. So both groups need an `Owner` tag. Check them, and add the tag only where it is missing. This is a small, reversible change (Level 4 in Part 5 removes what you added):

```powershell
$ADDED_RG_OWNER = @()
foreach ($rg in $RG_CORP, $RG_LAB) {
  $o = az group show -n $rg --query tags.Owner -o tsv
  if ($o) { "$rg already has Owner = $o" }
  else {
    az tag update --resource-id "$SCOPE_SUB/resourceGroups/$rg" --operation Merge --tags "Owner=$OWNER" -o none
    $ADDED_RG_OWNER += $rg
    "Added Owner = $OWNER to $rg"
  }
}
# Remember what you added, so that Level 4 can undo exactly that (even from a new window)
if ($ADDED_RG_OWNER) { Add-Content "$WORK/evidence/added-rg-owner.txt" $ADDED_RG_OWNER }
```

> **What you should see**
>
> Two lines, one per resource group: either `... already has Owner = ...` or `Added Owner = ... to rg-alz-...`. The other tags of the groups (`CostCenter`, `Project`, ...) are kept: the `Merge` operation only adds. The names of the groups you tagged are saved in `$WORK/evidence/added-rg-owner.txt`.

### Compare your landing zone with the runbook's assumptions

> **Where to do this:** **PowerShell window.**

The expected results in this runbook were measured on the reference environment (section 0.3). Your copy can differ in small details. That is not an error - it only changes which findings you will see. This block prints six settings that decide the findings in Chapters 1 and 2, so that nothing surprises you later:

```powershell
"Web app HTTPS only          (expect True)    : " + (az webapp show -g $RG_CORP -n $FE --query httpsOnly -o tsv)
"Web app minimum TLS         (expect 1.2)     : " + (az webapp config show -g $RG_CORP -n $FE --query minTlsVersion -o tsv)
"Key Vault purge protection  (expect empty)   : " + (az keyvault show -g $RG_CORP -n $KV --query properties.enablePurgeProtection -o tsv)
"Storage infra encryption    (expect empty)   : " + (az storage account show -g $RG_CORP -n $ST --query encryption.requireInfrastructureEncryption -o tsv)
"PostgreSQL geo backup       (expect Disabled): " + (az postgres flexible-server show -g $RG_CORP -n $PG --query backup.geoRedundantBackup -o tsv)
"Subnets without an NSG      (see the note) : " + (az network vnet subnet list -g $RG_CORP --vnet-name vnet-alz-corp-prod --query "[?networkSecurityGroup==null].name" -o tsv)
```

> **What you should see**
>
> The values in the brackets. If one line differs, the matching finding will appear (or disappear) in Chapter 1 or 2, and the counts printed in this runbook will change by that amount. For example, a web app that is not HTTPS-only adds an `AppServiceHttpsOnly` row to the Chapter 1 impact preview, and a subnet without an NSG adds a `SubnetHasNsg` row to Chapter 2. The last line lists any subnet without an NSG. The reference landing zone attaches NSGs to its application, data and private-link subnets only, so its gateway and web-app subnets (`snet-appgw`, `snet-appsvc`) are normally listed, and Chapter 2 will most likely show one extra `SubnetHasNsg` row for each of them (about 13 production findings instead of 11). The method and the explanations stay the same.

## 1.4  Check the sample application - and start it

> **Where to do this:** **PowerShell window.**

To save money, parts of the sample application are normally **stopped** when the demonstration is not running. Check what is running:

```powershell
"Application Gateway : " + (az network application-gateway show -g $RG_CORP -n $AGW --query operationalState -o tsv)
"PostgreSQL          : " + (az postgres flexible-server show -g $RG_CORP -n $PG --query state -o tsv)
"Frontend web app    : " + (az webapp show -g $RG_CORP -n $FE --query state -o tsv)
"Backend web app     : " + (az webapp show -g $RG_CORP -n $BE --query state -o tsv)
"Hub firewall        : " + (az resource show -g $RG_HUB -n afw-alz-hub --resource-type Microsoft.Network/azureFirewalls --api-version 2025-05-01 --query properties.provisioningState -o tsv)
```

> **What you should see**
>
> Typical result when the demonstration has been idle: gateway **Stopped**, PostgreSQL **Stopped**, both web apps **Running**, firewall **Succeeded** (the gateway and the database are stopped to save cost). If you started them already, the first two lines say **Running** and **Ready**.
>
> If the firewall line fails with `NoRegisteredProviderFound`, Azure CLI asked for an API version that the firewall provider does not offer. The `--api-version 2025-05-01` option in the command avoids that; keep it.

If the gateway or the database is **Stopped**, start them. This changes the running state of production resources, so it is the only 'production change' in Part 1.

> [!CAUTION]
> **Cost**
>
> A running Application Gateway WAF_v2 and Azure Firewall are billed every hour. Start them only when you are ready to demonstrate, and stop them in Part 5.

```powershell
az network application-gateway start -g $RG_CORP -n $AGW        # [about 5 to 10 min]
az postgres flexible-server start -g $RG_CORP -n $PG            # [about 3 to 5 min]
```

When both commands finish, run the application test. **This is the baseline you will repeat after every chapter.**

```powershell
Test-SampleApp
```

> **What you should see**
>
> *Example output - do not type this:*
>
> ```text
> Through the gateway        200
> Directly to the web app    403
> Gateway backend health     Healthy
> ```
>
> **200** means the application answers through the Application Gateway and its WAF. **403** means the web app refuses direct calls (only the gateway is allowed). **Healthy** means the gateway can reach its back end. Write all three down.
>
> If an NSG on your gateway subnet accepts HTTP only from certain addresses, a request from somewhere else - for example Azure Cloud Shell - shows `no answer` on the first line. Then the **Healthy** line and the **403** line are your proof.

> [!WARNING]
> **Common trap**
>
> If *through the gateway* shows **502**, the gateway is still starting (wait 2 minutes) or its back end is unhealthy because of the *host header* setting; the reference landing zone's `scripts/04-workload.ps1` (section 'the host header fix') shows the fix. Do not go on until the backend health is **Healthy** (and you get **200** from an allowed client), otherwise you cannot tell later whether a policy caused a problem.

## 1.5  Register the Recovery Services provider

> **Where to do this:** **PowerShell window.** (A Portal alternative follows.)

Azure Backup needs the `Microsoft.RecoveryServices` resource provider. It may not be registered in your subscription yet. Registering is free and harmless.

```powershell
az provider show --namespace Microsoft.RecoveryServices --query registrationState -o tsv
az provider register --namespace Microsoft.RecoveryServices --wait        # [about 1 to 2 min]
az provider show --namespace Microsoft.RecoveryServices --query registrationState -o tsv
```

> **What you should see**
>
> `NotRegistered` before, `Registered` after.

### Option B - Azure Portal: register the provider

> **Where to do this:** **Azure Portal** - the subscription page.

1. In the top search box type the name of your subscription and open it.
2. In the left menu, under **Settings**, click **Resource providers**.
3. In the filter box type `RecoveryServices`. Click the row **Microsoft.RecoveryServices**.
4. Click **Register** in the toolbar above the list. Wait until the status says **Registered** (about 1 to 2 minutes; click **Refresh** if needed).

> [!NOTE]
> **Not verified live**
>
> The Register button and the status text come from the Azure documentation, because registering would have changed the subscription.

## 1.6  Meet the policies you did not create

> **Where to do this:** **PowerShell window** for the list; **Azure Portal** to see the same thing visually.

Before you add your own rules, look at the rules that are already there. This saves you from a confusing moment later, when something is blocked or changed and you wonder *who did that*.

```powershell
az policy assignment list --scope "/providers/Microsoft.Management/managementGroups/<your-tenant-id>" `
  --query "[].{name:name, displayName:displayName, mode:enforcementMode}" -o table
```

> **What you should see**
>
> One row for every policy assigned at the Tenant Root Group, each with its mode. An empty list means that nothing is inherited from the root. Inherited rules normally have mode **Default** (enforced). Management groups between the root and your subscription can add more: look at the **Scope** column in the Portal.

### See the inherited policies in the Azure Portal

> **Where to do this:** **Azure Portal** - the **Policy** service.

1. In the top search box type `Policy` and, under **Services**, click **Policy**.
2. In the left menu, under **Authoring**, click **Assignments**.
3. The **Scope** pill at the top shows your subscription. The list shows every assignment that applies to it, including the inherited ones.
4. Scroll the list or use the **Search** box (*Filter by name or ID...*). Rows whose **Scope** column is **not** your subscription or one of your `rg-alz-` groups - for example *Tenant Root Group* or a management group - are **inherited**.
5. Click an inherited assignment. In **Essentials** you see its scope and, usually, *Policy enforcement : Default*. You cannot (and must not) change it.

> [!TIP]
> **Show the enforcement mode in the list**
>
> Back on the list, click **Edit columns**, then **+ Add option**, pick **Policy enforcement**, and click **Save**. The list then shows the enforcement mode of every assignment, so you can see at a glance that all `alz-` rows are *DoNotEnforce* and the inherited rows are *Default*.

> [!NOTE]
> **Display names versus names**
>
> The Portal list shows each assignment's **display name** (for example *ALZ - Require a CostCenter tag*), while the CLI uses the short **name** (`alz-require-costcenter-tag`). The *Assignment ID* on the assignment page ends with the short name.

### How to tell who blocked you

When a request is blocked, the error message always names two things. Look at the **policy assignment name** first:

| If the assignment name starts with... | Then the rule is... | What to do |
| --- | --- | --- |
| `alz-pd-` | One of **yours** (this runbook). This is what you want to see in a demonstration. | Read the policy name and the friendly sentence, and explain it. |
| `alz-` (without `pd`) | One of the reference landing zone's baseline rules (they are `DoNotEnforce`, so they cannot block). | Not expected. Check Show-Assignments. |
| Anything else - a name you do not recognise, or a security benchmark initiative you did not assign | An **inherited** rule that you cannot change. | Change the test so that it avoids that rule (see section 0.3), or explain it as a bonus. |

> [!NOTE]
> **Why the tests in this runbook look the way they do**
>
> Several tests are designed to avoid common inherited rules so that the denial is clearly caused by a policy from this runbook: the storage test uses *HTTPS-only* (not anonymous blob access, which an inherited Modify policy may silently fix); the region test uses *East US* (a region that is not approved here and, in most tenants, not blocked by anything else).

## 1.7  Create the lab network

> **Where to do this:** **PowerShell window.** The lab resource group `rg-alz-policy-lab` already exists and is empty.

The lab needs a tiny network for the test VM. Everything gets the two required tags, so it will pass the tag rules later.

```powershell
az network nsg create -g $RG_LAB -n nsg-pd-lab -l $LOC --tags $TAGS
az network vnet create -g $RG_LAB -n vnet-pd-lab -l $LOC --address-prefixes 10.250.0.0/24 `
  --subnet-name snet-pd-lab --subnet-prefixes 10.250.0.0/26 --nsg nsg-pd-lab --tags $TAGS
```

> **What you should see**
>
> Two JSON blocks. In each you can find `"provisioningState": "Succeeded"`. The VNet block also shows the subnet `snet-pd-lab` with `10.250.0.0/26`.

## 1.8  Create the weak lab VM (do this early)

> **Where to do this:** **PowerShell window.**

Chapter 2 needs a VM that has weaknesses to find, and some findings (backup, vulnerability assessment) take **hours** to appear. Create it now. It is deliberately **weak**: security type *Standard* (not Trusted Launch), no encryption at host, and no backup. It has **no public IP**, so nobody can reach it from the Internet.

```powershell
az vm create -g $RG_LAB -n $VM -l $LOC `
  --image "Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest" `
  --size Standard_B2ls_v2 --admin-username azureuser --generate-ssh-keys `
  --vnet-name vnet-pd-lab --subnet snet-pd-lab `
  --public-ip-address '""' --nsg '""' --security-type Standard `
  --tags CostCenter=ALZ-Demo Owner=$OWNER Purpose=PolicyDemo Backup=daily
```

> **What you should see**
>
> After about 2 to 3 minutes a JSON block with `"powerState": "VM running"` and a private IP such as `10.250.0.4`. The tag `Backup=daily` is used by Chapter 3 to decide which VMs to back up.

> [!WARNING]
> **Common trap**
>
> `--public-ip-address '""'` looks odd. PowerShell removes a bare empty string, so you must wrap the quotes like this to tell the CLI *'no public IP'*.
>
> If you do not have an SSH key, `--generate-ssh-keys` creates one in the `.ssh` folder of your user profile. You never need to log in to this VM.

Confirm that the VM really has the weaknesses Chapter 2 will find:

```powershell
$q = "{size:hardwareProfile.vmSize, securityType:securityProfile.securityType,"
$q += " encryptionAtHost:securityProfile.encryptionAtHost}"
az vm show -g $RG_LAB -n $VM --query $q -o yaml
```

> **What you should see**
>
> `size: Standard_B2ls_v2`, `securityType: Standard` and `encryptionAtHost: null`. These two settings are exactly what the Trusted Launch and encryption-at-host rules will report.

## 1.9  Create the five custom policy definitions

> **Where to do this:** **PowerShell window.** Each definition needs two small JSON files: the **rule** (when does it match) and the **parameters** (settings you can change at assignment time). The first block writes the files; the second creates the definition.

Built-in policies cover most of what you need. Five rules have no suitable built-in, so you write them. Read the **plain-words** box before each one: it is the whole logic in a sentence.

### Definition 1 - alz-pd-nsg-no-internet-mgmt

> **What to say**
>
> **In plain words:** look at every network security group rule. If the rule is **inbound**, **allows** traffic, comes from the **Internet** (or from anywhere, `*`, or `0.0.0.0/0`) and targets port **22**, **3389** or **any port**, then apply the effect. The rule checks both single rules and the rules inside a whole NSG, because Azure evaluates them differently.

> [!NOTE]
> **Limit**
>
> The rule compares exact port numbers. A range such as `3000-4000` that happens to include 3389 is not detected. For this demo that is acceptable; a production rule would add range logic.

```powershell
@'
{
 "if": {
  "anyOf": [
   {
    "allOf": [
     {"field": "type", "equals": "Microsoft.Network/networkSecurityGroups/securityRules"},
     {
      "field": "Microsoft.Network/networkSecurityGroups/securityRules/direction",
      "equals": "Inbound"
     },
     {"field": "Microsoft.Network/networkSecurityGroups/securityRules/access", "equals": "Allow"},
     {
      "anyOf": [
       {
        "field": "Microsoft.Network/networkSecurityGroups/securityRules/sourceAddressPrefix",
        "in": ["*", "Internet", "0.0.0.0/0"]
       },
       {
        "count": {
         "field": "Microsoft.Network/networkSecurityGroups/securityRules/sourceAddressPrefixes[*]",
         "where": {
          "field": "Microsoft.Network/networkSecurityGroups/securityRules/sourceAddressPrefixes[*]",
          "in": ["*", "Internet", "0.0.0.0/0"]
         }
        },
        "greater": 0
       }
      ]
     },
     {
      "anyOf": [
       {
        "field": "Microsoft.Network/networkSecurityGroups/securityRules/destinationPortRange",
        "in": ["22", "3389", "*"]
       },
       {
        "count": {
         "field": "Microsoft.Network/networkSecurityGroups/securityRules/destinationPortRanges[*]",
         "where": {
          "field": "Microsoft.Network/networkSecurityGroups/securityRules/destinationPortRanges[*]",
          "in": ["22", "3389", "*"]
         }
        },
        "greater": 0
       }
      ]
     }
    ]
   },
   {
    "allOf": [
     {"field": "type", "equals": "Microsoft.Network/networkSecurityGroups"},
     {
      "count": {
       "field": "Microsoft.Network/networkSecurityGroups/securityRules[*]",
       "where": {
        "allOf": [
         {
          "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].direction",
          "equals": "Inbound"
         },
         {
          "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].access",
          "equals": "Allow"
         },
         {
          "anyOf": [
           {
            "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].sourceAddressPrefix",
            "in": ["*", "Internet", "0.0.0.0/0"]
           },
           {
            "count": {
             "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].sourceAddressPrefixes[*]",
             "where": {
              "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].sourceAddressPrefixes[*]",
              "in": ["*", "Internet", "0.0.0.0/0"]
             }
            },
            "greater": 0
           }
          ]
         },
         {
          "anyOf": [
           {
            "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].destinationPortRange",
            "in": ["22", "3389", "*"]
           },
           {
            "count": {
             "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].destinationPortRanges[*]",
             "where": {
              "field": "Microsoft.Network/networkSecurityGroups/securityRules[*].destinationPortRanges[*]",
              "in": ["22", "3389", "*"]
             }
            },
            "greater": 0
           }
          ]
         }
        ]
       }
      },
      "greater": 0
     }
    ]
   }
  ]
 },
 "then": {"effect": "[parameters('effect')]"}
}
'@ | Set-Content "$WORK/d1-nsg-rule.json" -Encoding ascii
```

```powershell
@'
{
 "effect": {
  "type": "String",
  "allowedValues": ["Audit", "Deny", "Disabled"],
  "defaultValue": "Deny",
  "metadata": {
   "displayName": "Effect",
   "description": "What the policy does when it finds a problem."
  }
 }
}
'@ | Set-Content "$WORK/d1-nsg-params.json" -Encoding ascii
```

```powershell
az policy definition create --name "alz-pd-nsg-no-internet-mgmt" `
  --display-name "ALZ PD - NSG rules must not allow Internet access to SSH or RDP" `
  --description "Stops (or audits) any inbound Allow rule that opens port 22 or 3389 to the Internet." `
  --mode All --rules "@$WORK/d1-nsg-rule.json" --params "@$WORK/d1-nsg-params.json" --subscription $SUB
```

### Definition 2 - alz-pd-route-default-via-fw

> **What to say**
>
> **In plain words:** look at every route. If the route sends **0.0.0.0/0** (all Internet-bound traffic) anywhere **other than** a virtual appliance at the hub firewall address (`10.110.0.4`), apply the effect. This is the 'controlled egress' rule: all outbound traffic must pass the firewall.

```powershell
@'
{
 "if": {
  "anyOf": [
   {
    "allOf": [
     {"field": "type", "equals": "Microsoft.Network/routeTables/routes"},
     {"field": "Microsoft.Network/routeTables/routes/addressPrefix", "equals": "0.0.0.0/0"},
     {
      "anyOf": [
       {
        "field": "Microsoft.Network/routeTables/routes/nextHopType",
        "notEquals": "VirtualAppliance"
       },
       {
        "field": "Microsoft.Network/routeTables/routes/nextHopIpAddress",
        "notEquals": "[parameters('firewallPrivateIp')]"
       }
      ]
     }
    ]
   },
   {
    "allOf": [
     {"field": "type", "equals": "Microsoft.Network/routeTables"},
     {
      "count": {
       "field": "Microsoft.Network/routeTables/routes[*]",
       "where": {
        "allOf": [
         {"field": "Microsoft.Network/routeTables/routes[*].addressPrefix", "equals": "0.0.0.0/0"},
         {
          "anyOf": [
           {
            "field": "Microsoft.Network/routeTables/routes[*].nextHopType",
            "notEquals": "VirtualAppliance"
           },
           {
            "field": "Microsoft.Network/routeTables/routes[*].nextHopIpAddress",
            "notEquals": "[parameters('firewallPrivateIp')]"
           }
          ]
         }
        ]
       }
      },
      "greater": 0
     }
    ]
   }
  ]
 },
 "then": {"effect": "[parameters('effect')]"}
}
'@ | Set-Content "$WORK/d2-route-rule.json" -Encoding ascii
```

```powershell
@'
{
 "effect": {
  "type": "String",
  "allowedValues": ["Audit", "Deny", "Disabled"],
  "defaultValue": "Audit",
  "metadata": {
   "displayName": "Effect",
   "description": "What the policy does when it finds a problem."
  }
 },
 "firewallPrivateIp": {
  "type": "String",
  "defaultValue": "10.110.0.4",
  "metadata": {
   "displayName": "Hub firewall private IP",
   "description": "The only allowed next hop for 0.0.0.0/0."
  }
 }
}
'@ | Set-Content "$WORK/d2-route-params.json" -Encoding ascii
```

```powershell
az policy definition create --name "alz-pd-route-default-via-fw" `
  --display-name "ALZ PD - The default route must go through the hub firewall" `
  --description "0.0.0.0/0 must point to the hub firewall private IP." `
  --mode All --rules "@$WORK/d2-route-rule.json" --params "@$WORK/d2-route-params.json" --subscription $SUB
```

### Definition 3 - alz-pd-appgw-https-listener

> **What to say**
>
> **In plain words:** if an Application Gateway has **any listener that is not HTTPS**, apply the effect. (The demo gateway has one HTTP listener, so this will be a real finding.)

```powershell
@'
{
 "if": {
  "allOf": [
   {"field": "type", "equals": "Microsoft.Network/applicationGateways"},
   {
    "count": {
     "field": "Microsoft.Network/applicationGateways/httpListeners[*]",
     "where": {
      "field": "Microsoft.Network/applicationGateways/httpListeners[*].protocol",
      "notEquals": "Https"
     }
    },
    "greater": 0
   }
  ]
 },
 "then": {"effect": "[parameters('effect')]"}
}
'@ | Set-Content "$WORK/d3-appgw-rule.json" -Encoding ascii
```

```powershell
@'
{
 "effect": {
  "type": "String",
  "allowedValues": ["Audit", "Deny", "Disabled"],
  "defaultValue": "Audit",
  "metadata": {
   "displayName": "Effect",
   "description": "What the policy does when it finds a problem."
  }
 }
}
'@ | Set-Content "$WORK/d3-appgw-params.json" -Encoding ascii
```

```powershell
az policy definition create --name "alz-pd-appgw-https-listener" `
  --display-name "ALZ PD - Application Gateway listeners must use HTTPS" `
  --description "Reports gateways that expose a plain HTTP listener." `
  --mode All --rules "@$WORK/d3-appgw-rule.json" --params "@$WORK/d3-appgw-params.json" --subscription $SUB
```

### Definitions 4 and 5 - resource groups named rg-alz-*

> **What to say**
>
> **In plain words:** a resource group is created at **subscription** level, so a rule about resource groups must be assigned to the whole subscription. A subscription can hold other workloads, so both rules start with a filter: *only if the name starts with `rg-alz-`*. Other resource groups are never affected. Rule 4 requires the `CostCenter` and `Owner` tags; rule 5 requires an approved region.

```powershell
@'
{
 "if": {
  "allOf": [
   {"field": "type", "equals": "Microsoft.Resources/subscriptions/resourceGroups"},
   {"field": "name", "like": "rg-alz-*"},
   {
    "anyOf": [
     {"field": "[concat('tags[', parameters('firstTagName'), ']')]", "exists": "false"},
     {"field": "[concat('tags[', parameters('secondTagName'), ']')]", "exists": "false"}
    ]
   }
  ]
 },
 "then": {"effect": "[parameters('effect')]"}
}
'@ | Set-Content "$WORK/d4-rgtags-rule.json" -Encoding ascii
```

```powershell
@'
{
 "effect": {
  "type": "String",
  "allowedValues": ["Audit", "Deny", "Disabled"],
  "defaultValue": "Deny",
  "metadata": {
   "displayName": "Effect",
   "description": "What the policy does when it finds a problem."
  }
 },
 "firstTagName": {
  "type": "String",
  "defaultValue": "CostCenter",
  "metadata": {"displayName": "First required tag"}
 },
 "secondTagName": {
  "type": "String",
  "defaultValue": "Owner",
  "metadata": {"displayName": "Second required tag"}
 }
}
'@ | Set-Content "$WORK/d4-rgtags-params.json" -Encoding ascii
```

```powershell
@'
{
 "if": {
  "allOf": [
   {"field": "type", "equals": "Microsoft.Resources/subscriptions/resourceGroups"},
   {"field": "name", "like": "rg-alz-*"},
   {"field": "location", "notIn": "[parameters('listOfAllowedLocations')]"}
  ]
 },
 "then": {"effect": "[parameters('effect')]"}
}
'@ | Set-Content "$WORK/d5-rgloc-rule.json" -Encoding ascii
```

```powershell
@'
{
 "effect": {
  "type": "String",
  "allowedValues": ["Audit", "Deny", "Disabled"],
  "defaultValue": "Deny",
  "metadata": {
   "displayName": "Effect",
   "description": "What the policy does when it finds a problem."
  }
 },
 "listOfAllowedLocations": {
  "type": "Array",
  "defaultValue": ["indonesiacentral", "southeastasia"],
  "metadata": {"displayName": "Allowed regions", "strongType": "location"}
 }
}
'@ | Set-Content "$WORK/d5-rgloc-params.json" -Encoding ascii
```

```powershell
az policy definition create --name "alz-pd-rg-required-tags" `
  --display-name "ALZ PD - rg-alz-* groups must carry the required tags" `
  --description "Only resource groups whose name starts with rg-alz- are checked." `
  --mode All --rules "@$WORK/d4-rgtags-rule.json" --params "@$WORK/d4-rgtags-params.json" --subscription $SUB

az policy definition create --name "alz-pd-rg-allowed-locations" `
  --display-name "ALZ PD - rg-alz-* groups must be in an approved region" `
  --description "Only resource groups whose name starts with rg-alz- are checked." `
  --mode All --rules "@$WORK/d5-rgloc-rule.json" --params "@$WORK/d5-rgloc-params.json" --subscription $SUB
```

> [!WARNING]
> **COMMON TRAP - 'Indexed' mode**
>
> Every command above says `--mode All`. If you leave it out, Azure uses **Indexed**, which ignores resource groups and child resources such as NSG rules and routes. The policy would be created, show no error, and **silently do nothing**.

### Check that all five exist

```powershell
az policy definition list --query "[?starts_with(name,'alz-pd-')].{name:name, mode:mode}" -o table
```

> **What you should see**
>
> Five rows, all with Mode **All**: `alz-pd-nsg-no-internet-mgmt`, `alz-pd-route-default-via-fw`, `alz-pd-appgw-https-listener`, `alz-pd-rg-required-tags`, `alz-pd-rg-allowed-locations`.

### Look at the custom definitions in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Definitions**.

1. Policy > left menu > **Authoring** > **Definitions**.
2. Click the pill **Policy type : All policy types**, tick **Custom**, click **Apply**. Type `ALZ PD` in the **Search** box.
3. You see your five definitions. The **Definition location** column shows the subscription and the **Type** column shows *Custom*.
4. Click **ALZ PD - NSG rules must not allow Internet access to SSH or RDP**. In the **Essentials** area check that **Mode** says **All**. Open the tab **Definition** to read the JSON you pasted, and the tab **Parameters (2)** for *Effect* (allowed values Audit, Deny, Disabled; default Deny).

## 1.10  Create the three initiatives

> **Where to do this:** **PowerShell window.**

An **initiative** is a package of policies. You create one per chapter, so each chapter is assigned (and explained) as one unit. Each rule inside an initiative has a **reference ID** (its label inside the package) and belongs to one of the nine **families**, so that the results can be grouped by family later.

Writing the initiative JSON by hand would be long and error-prone, so you use a small helper, `New-Ref`, that builds one line of the package. **Step 1 - paste the helper and the family names:**

```powershell
# One helper that builds one line of an initiative (called a "policy reference")
function New-Ref {
  param([string]$RefId, [string]$Policy, [string]$Family, [string]$Effect = '', [hashtable]$Params = @{})
  $root = "/providers/Microsoft.Authorization/policyDefinitions/"
  if ($Policy -like 'alz-*') { $root = "$SCOPE_SUB$root" }     # your own custom definitions
  $values = [ordered]@{}
  if ($Effect) { $values['effect'] = @{ value = $Effect } }
  foreach ($key in $Params.Keys) { $values[$key] = @{ value = $Params[$key] } }
  [ordered]@{
    policyDefinitionId          = "$root$Policy"
    policyDefinitionReferenceId = $RefId
    groupNames                  = @($Family)
    parameters                  = $values
  }
}

# The nine control families (used to group the results)
$F1 = 'F1-Locations';        $F2 = 'F2-PublicExposure';  $F3 = 'F3-DataInTransit'
$F4 = 'F4-StoredDataKeys';   $F5 = 'F5-Monitoring';      $F6 = 'F6-BackupRecovery'
$F7 = 'F7-ComputeBaseline';  $F8 = 'F8-NetworkSegmentation'; $F9 = 'F9-Ownership'
```

**Step 2 - Chapter 1 (PREVENT).** Ten rules, mostly with the effect **Deny**. Each line reads: *reference ID, policy, family, effect, extra settings*. The long GUID is the built-in policy's ID; `alz-pd-...` entries are your custom definitions.

```powershell
$c1 = @(
  New-Ref 'AllowedLocations' 'e56962a6-4747-49cd-b67b-bf8b01975c4c' $F1 'Deny' `
          @{ listOfAllowedLocations = "[parameters('allowedLocations')]" }
  New-Ref 'NoPublicIpOnNic' '83a86a26-fd1f-447c-b59d-e51f44264114' $F2
  New-Ref 'NsgNoInternetMgmtPorts' 'alz-pd-nsg-no-internet-mgmt' $F2 'Deny'
  New-Ref 'StorageSecureTransfer' '404c3081-a854-4457-ae30-26a93ef643f9' $F3 'Deny'
  New-Ref 'StorageMinTls' 'fe83a0eb-a853-422d-aac2-1bffd182c5d0' $F3 'Deny' `
          @{ minimumTlsVersion = "[parameters('minimumTlsVersion')]" }
  New-Ref 'AppServiceHttpsOnly' 'a4af4a39-4135-47fb-b175-47fbdf85311d' $F3 'Deny'
  New-Ref 'KeyVaultPurgeProtection' '0b60c0b2-2dc2-4e1c-b5c9-abbed971de53' $F4 'Deny'
  New-Ref 'RouteDefaultViaFirewall' 'alz-pd-route-default-via-fw' $F8 'Deny' `
          @{ firewallPrivateIp = "[parameters('firewallPrivateIp')]" }
  New-Ref 'RequireCostCenterTag' '871b6d14-10aa-478d-b590-94f262ecfa99' $F9 '' `
          @{ tagName = "[parameters('costCenterTagName')]" }
  New-Ref 'RequireOwnerTag' '871b6d14-10aa-478d-b590-94f262ecfa99' $F9 '' `
          @{ tagName = "[parameters('ownerTagName')]" }
)
ConvertTo-Json -InputObject $c1 -Depth 10 | Set-Content "$WORK/c1-defs.json" -Encoding ascii
```

**Step 3 - Chapter 2 (DETECT).** Twenty-one rules, all **Audit** or **AuditIfNotExists**. None of them can block or change anything.

```powershell
$LOGS    = @{ logAnalytics = "[parameters('logAnalyticsWorkspaceId')]"; categoryGroup = 'allLogs' }
$LOGSAPP = @{ logAnalytics = "[parameters('logAnalyticsWorkspaceId')]" }   # the App Service rule has no group
$AINE    = 'AuditIfNotExists'
$c2 = @(
  New-Ref 'AppServicePublicAccess' '1b5ef780-c53c-4a64-87f3-bb9c8c8094ba' $F2 'Audit'
  New-Ref 'StoragePublicAccess' 'b2982f36-99f2-4db5-8eff-283140c09693' $F2 'Audit'
  New-Ref 'KeyVaultPublicAccess' '405c5871-3e91-4644-8a63-58e19d68ff5b' $F2 'Audit'
  New-Ref 'PostgresPublicAccess' '5e1de0e3-42cb-4ebc-a86d-61d0c619ca48' $F2 'Audit'
  New-Ref 'ManagedRedisPublicAccess' '0f8a6cc3-040f-4b9b-8828-b37490729517' $F2 'Audit'
  New-Ref 'VmManagementPortsClosed' '22730e10-96f6-4aac-ad84-9383d35b5917' $F2 $AINE
  New-Ref 'AppGatewayHttpsListener' 'alz-pd-appgw-https-listener' $F3 'Audit'
  New-Ref 'AppServiceMinTls' 'f0e6e85b-9b9f-4a4b-b67b-f730d42f1b0b' $F3 $AINE
  New-Ref 'KeyVaultUsesRbac' '12d4fa5e-1f9f-4c21-97a9-b99b3c6611b5' $F4 'Audit'
  New-Ref 'StorageInfrastructureEncryption' '4733ea7b-a883-42fe-8cac-97454c2a9e4a' $F4 'Audit'
  New-Ref 'EncryptionAtHost' 'fc4d8e41-e223-45ea-9bf5-eada37891d87' $F4 'Audit'
  New-Ref 'DiagKeyVault' '6b359d8f-f88d-4052-aa7c-32015963ecc1' $F5 $AINE $LOGS
  New-Ref 'DiagAppService' 'c0d8e23a-47be-4032-961f-8b0ff3957061' $F5 $AINE $LOGSAPP
  New-Ref 'DiagPostgres' 'cdd1dbc6-0004-4fcd-afd7-b67550de37ff' $F5 $AINE $LOGS
  New-Ref 'DiagAppGateway' '92012204-a7e4-4a95-bbe5-90d0d3e12735' $F5 $AINE $LOGS
  New-Ref 'DiagRedisEnterprise' 'fa570aa1-acca-4eea-8e5a-233cf2c5e4c2' $F5 $AINE $LOGS
  New-Ref 'VmBackupEnabled' '013e242c-8828-4970-87b3-ab247555486d' $F6 $AINE
  New-Ref 'PostgresGeoBackup' 'cee2f9fd-3968-44be-a863-bd62c9884423' $F6 'Audit'
  New-Ref 'VmTrustedLaunch' 'c95b54ad-0614-4633-ab29-104b01235cbf' $F7 'Audit'
  New-Ref 'VmVulnerabilityAssessment' '501541f7-f7e7-4cd6-868c-4190fdad3ac9' $F7 $AINE
  New-Ref 'SubnetHasNsg' 'e71308d3-144b-4262-b144-efdc3cc90517' $F8 $AINE
)
ConvertTo-Json -InputObject $c2 -Depth 10 | Set-Content "$WORK/c2-defs.json" -Encoding ascii
```

**Step 4 - Chapter 3 (REMEDIATE).** Seven rules with the effects **Modify** (copy tags) and **DeployIfNotExists** (create diagnostic settings). `$LOGS` and `$LOGSAPP` come from step 3, so keep the same PowerShell window.

```powershell
$DINE = 'DeployIfNotExists'
$c3 = @(
  New-Ref 'InheritOwnerTag' 'ea3f2387-9b95-492a-a190-fcdc54f7b070' $F9 '' `
          @{ tagName = "[parameters('ownerTagName')]" }
  New-Ref 'InheritCostCenterTag' 'ea3f2387-9b95-492a-a190-fcdc54f7b070' $F9 '' `
          @{ tagName = "[parameters('costCenterTagName')]" }
  New-Ref 'DeployDiagKeyVault' '6b359d8f-f88d-4052-aa7c-32015963ecc1' $F5 $DINE $LOGS
  New-Ref 'DeployDiagAppService' 'c0d8e23a-47be-4032-961f-8b0ff3957061' $F5 $DINE $LOGSAPP
  New-Ref 'DeployDiagPostgres' 'cdd1dbc6-0004-4fcd-afd7-b67550de37ff' $F5 $DINE $LOGS
  New-Ref 'DeployDiagAppGateway' '92012204-a7e4-4a95-bbe5-90d0d3e12735' $F5 $DINE $LOGS
  New-Ref 'DeployDiagRedisEnterprise' 'fa570aa1-acca-4eea-8e5a-233cf2c5e4c2' $F5 $DINE $LOGS
)
ConvertTo-Json -InputObject $c3 -Depth 10 | Set-Content "$WORK/c3-defs.json" -Encoding ascii
```

**Step 5 - the settings (parameters) of each initiative, the nine family names, and the friendly messages** that will appear inside every Deny error:

```powershell
@'
{
 "allowedLocations": {
  "type": "Array",
  "defaultValue": ["indonesiacentral", "southeastasia"],
  "metadata": {
   "displayName": "Allowed regions",
   "description": "Regions that may be deployed into.",
   "strongType": "location"
  }
 },
 "costCenterTagName": {
  "type": "String",
  "defaultValue": "CostCenter",
  "metadata": {"displayName": "Cost centre tag name"}
 },
 "ownerTagName": {
  "type": "String",
  "defaultValue": "Owner",
  "metadata": {"displayName": "Owner tag name"}
 },
 "firewallPrivateIp": {
  "type": "String",
  "defaultValue": "10.110.0.4",
  "metadata": {"displayName": "Hub firewall private IP"}
 },
 "minimumTlsVersion": {
  "type": "String",
  "defaultValue": "TLS1_2",
  "allowedValues": ["TLS1_0", "TLS1_1", "TLS1_2"],
  "metadata": {"displayName": "Minimum TLS version for storage accounts"}
 }
}
'@ | Set-Content "$WORK/c1-params.json" -Encoding ascii
```

```powershell
@'
{
 "logAnalyticsWorkspaceId": {
  "type": "String",
  "metadata": {
   "displayName": "Central Log Analytics workspace (resource ID)",
   "description": "Where diagnostic logs must be sent."
  }
 }
}
'@ | Set-Content "$WORK/c2-params.json" -Encoding ascii
```

```powershell
@'
{
 "ownerTagName": {
  "type": "String",
  "defaultValue": "Owner",
  "metadata": {"displayName": "Owner tag name"}
 },
 "costCenterTagName": {
  "type": "String",
  "defaultValue": "CostCenter",
  "metadata": {"displayName": "Cost centre tag name"}
 },
 "logAnalyticsWorkspaceId": {
  "type": "String",
  "metadata": {"displayName": "Central Log Analytics workspace (resource ID)"}
 }
}
'@ | Set-Content "$WORK/c3-params.json" -Encoding ascii
```

```powershell
@'
[
 {
  "name": "F1-Locations",
  "displayName": "Family 1 - Approved deployment locations"
 },
 {
  "name": "F2-PublicExposure",
  "displayName": "Family 2 - Prevent unintended public exposure"
 },
 {
  "name": "F3-DataInTransit",
  "displayName": "Family 3 - Protect data in transit"
 },
 {
  "name": "F4-StoredDataKeys",
  "displayName": "Family 4 - Protect stored data and keys"
 },
 {"name": "F5-Monitoring", "displayName": "Family 5 - Centralised monitoring"},
 {
  "name": "F6-BackupRecovery",
  "displayName": "Family 6 - Backup and recovery protection"
 },
 {
  "name": "F7-ComputeBaseline",
  "displayName": "Family 7 - Secure compute baseline"
 },
 {
  "name": "F8-NetworkSegmentation",
  "displayName": "Family 8 - Network segmentation and controlled egress"
 },
 {
  "name": "F9-Ownership",
  "displayName": "Family 9 - Ownership and accountability"
 }
]
'@ | Set-Content "$WORK/groups.json" -Encoding ascii
```

```powershell
@'
[
 {
  "message": "Guardrail (Chapter 1 - Prevent): read the policy name in this error."
 },
 {
  "message": "F1 Locations: deploy only in Indonesia Central or Southeast Asia.",
  "policyDefinitionReferenceId": "AllowedLocations"
 },
 {
  "message": "F2 Public exposure: a network interface must not have a public IP.",
  "policyDefinitionReferenceId": "NoPublicIpOnNic"
 },
 {
  "message": "F2 Public exposure: do not open SSH (22) or RDP (3389) to the Internet.",
  "policyDefinitionReferenceId": "NsgNoInternetMgmtPorts"
 },
 {
  "message": "F3 Data in transit: storage accounts must require HTTPS.",
  "policyDefinitionReferenceId": "StorageSecureTransfer"
 },
 {
  "message": "F3 Data in transit: storage accounts must use the approved TLS version.",
  "policyDefinitionReferenceId": "StorageMinTls"
 },
 {
  "message": "F3 Data in transit: web apps must allow HTTPS only.",
  "policyDefinitionReferenceId": "AppServiceHttpsOnly"
 },
 {
  "message": "F4 Stored data and keys: a Key Vault needs purge protection.",
  "policyDefinitionReferenceId": "KeyVaultPurgeProtection"
 },
 {
  "message": "F8 Segmentation: 0.0.0.0/0 must go through the hub firewall.",
  "policyDefinitionReferenceId": "RouteDefaultViaFirewall"
 },
 {
  "message": "F9 Ownership: every resource needs the CostCenter tag.",
  "policyDefinitionReferenceId": "RequireCostCenterTag"
 },
 {
  "message": "F9 Ownership: every resource needs the Owner tag.",
  "policyDefinitionReferenceId": "RequireOwnerTag"
 }
]
'@ | Set-Content "$WORK/c1-messages.json" -Encoding ascii
```

**Step 6 - create the three initiatives:**

```powershell
az policy set-definition create --name "alz-pd-c1-prevent" `
  --display-name "ALZ PD - Chapter 1 PREVENT: block unsafe deployments" `
  --description "Ten guardrails that stop unsafe resources being created (effect Deny)." `
  --definitions "@$WORK/c1-defs.json" --params "@$WORK/c1-params.json" `
  --definition-groups "@$WORK/groups.json" --subscription $SUB

az policy set-definition create --name "alz-pd-c2-detect" `
  --display-name "ALZ PD - Chapter 2 DETECT: find the gaps" `
  --description "Audit-only checks. They cannot block or change anything." `
  --definitions "@$WORK/c2-defs.json" --params "@$WORK/c2-params.json" `
  --definition-groups "@$WORK/groups.json" --subscription $SUB

az policy set-definition create --name "alz-pd-c3-remediate" `
  --display-name "ALZ PD - Chapter 3 REMEDIATE: fix automatically" `
  --description "Copies tags and deploys diagnostic settings (effects Modify and DeployIfNotExists)." `
  --definitions "@$WORK/c3-defs.json" --params "@$WORK/c3-params.json" `
  --definition-groups "@$WORK/groups.json" --subscription $SUB
```

> **What you should see**
>
> Each command prints a JSON block. Check the number of policies with the next command.

```powershell
az policy set-definition list --query "[?starts_with(name,'alz-pd-')].{name:name, policies:length(policyDefinitions)}" -o table
```

> **What you should see**
>
> *Example output - do not type this:*
>
> ```text
> Name                  Policies
> --------------------  --------
> alz-pd-c1-prevent           10
> alz-pd-c2-detect           21
> alz-pd-c3-remediate         7
> ```

### Look at the initiatives in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Definitions**.

1. Policy > **Authoring** > **Definitions**. Click the pill **Definition type : All definition types** and tick **Initiative**. Type `ALZ PD` in **Search**.
2. You see three rows. The **Policies** column shows **10**, **21** and **7**.
3. Click **ALZ PD - Chapter 2 DETECT: find the gaps**. You should see the 21 policies, each with its **Reference ID** and its **Group** (F2-PublicExposure, F3-DataInTransit and so on).

> [!NOTE]
> **Why not build the initiatives in the portal?**
>
> The Portal has a wizard for this (**+ Initiative definition**, with the tabs Basics, Policies, Groups, Initiative parameters, Policy parameters and Review + create). It works, but you would have to add 38 policies one by one and set their parameters in a table. The PowerShell helper in step 1.10 does the same in seconds and cannot mistype a parameter.

## 1.11  Pre-flight checklist

Run the checks. **Do not start the demonstration until every row is true.** The list takes about 30 seconds.

```powershell
"--- Policy library ---"
az policy definition list --query "[?policyType=='Custom'].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' }
az policy set-definition list --query "[?policyType=='Custom'].name" -o tsv | Where-Object { $_ -like 'alz-pd-*' }
"--- Nothing is enforcing yet (the 8 baseline rows, plus any alz-pd- row you already made; none enforcing) ---"
Show-Assignments
Show-Enforcing
"--- Application ---"
Test-SampleApp
"--- Lab ---"
az resource list -g $RG_LAB --query "[].{name:name, type:type}" -o table
```

> [!IMPORTANT]
> **CHECKPOINT - do not continue until all of this is true**
>
> - Eight names are listed (5 definitions + 3 initiatives).
> - `Show-Assignments` shows the **eight baseline assignments** of the reference landing zone, all **DoNotEnforce**, plus any `alz-pd-` assignment you have already made. `Show-Enforcing` prints **nothing** (no `alz-` assignment is enforcing yet).
> - `Test-SampleApp` shows **403** directly and backend health **Healthy** (and **200** through the gateway, if your client can reach it - see step 1.4).
> - The lab contains the NSG, the VNet, the VM, its NIC and its disk.

---

[Runbook index](README.md) &middot; Previous: [Part 0 - Before you start](00-before-you-start.md) &middot; Next: [Part 2 - Chapter 1: PREVENT - block unsafe deployments](02-chapter-1-prevent.md)
