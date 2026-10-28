# Part 2 - Chapter 1: PREVENT - block unsafe deployments

[Runbook index](README.md) &middot; Previous: [Part 1 - Prepare the stage](01-prepare-the-stage.md) &middot; Next: [Part 3 - Chapter 2: DETECT - find the gaps](03-chapter-2-detect.md)

In this chapter policy says **no** before anything is created. You will try to create nine unsafe things in the disposable lab, watch Azure refuse each one, and then create the safe version of the same thing and watch it succeed. At the end you will also see what the same rules would mean for the real resources of the sample application - without blocking anything there.

## 2.1  The idea

The effect used here is **Deny**. When you create or update a resource, Azure Resource Manager asks Azure Policy first. If a Deny rule matches, the request stops with the error **`RequestDisallowedByPolicy`**. Nothing is created and nothing is charged.

| Question | Answer |
| --- | --- |
| Does Deny delete things that already exist? | **No.** Existing resources stay. They are reported as non-compliant. |
| Why use a lab? | A Deny rule on production could block a legitimate change at the worst moment. The lab is empty and disposable, so you can switch enforcement on safely. |
| How long until a new Deny rule works? | About **5 minutes** for the first rule and up to **10 minutes** for every rule. Section 2.3 gives you a self-cleaning test and a waiting block. |
| Where do the friendly sentences in the errors come from? | From the *non-compliance messages* you attach in step 2.2 (the file `c1-messages.json`). |

Here are the ten rules of the Chapter 1 initiative and where you will test them:

| Reference ID | Family | Built-in or custom | Tested in |
| --- | --- | --- | --- |
| `AllowedLocations` | F1 | Built-in: Allowed locations | Test 1 |
| `NoPublicIpOnNic` | F2 | Built-in: Network interfaces should not have public IPs | Test 2 |
| `NsgNoInternetMgmtPorts` | F2 | Custom `alz-pd-nsg-no-internet-mgmt` | Test 3 |
| `StorageSecureTransfer` | F3 | Built-in: Secure transfer to storage accounts should be enabled | Test 4 |
| `StorageMinTls` | F3 | Built-in: Storage accounts should have the specified minimum TLS version | Refused together with `StorageSecureTransfer` in Test 4 |
| `AppServiceHttpsOnly` | F3 | Built-in: App Service apps should only be accessible over HTTPS | Reported in section 2.6 (no live test) |
| `KeyVaultPurgeProtection` | F4 | Built-in: Key vaults should have deletion protection enabled | Test 5 |
| `RouteDefaultViaFirewall` | F8 | Custom `alz-pd-route-default-via-fw` | Test 6 |
| `RequireCostCenterTag`, `RequireOwnerTag` | F9 | Built-in: Require a tag on resources (used twice) | Test 7 |
| (separate) VNet peering rule | F8 | Your existing custom `alz-deny-vnet-peering` | Test 8 |
| (subscription level) resource-group rules | F1, F9 | Custom `alz-pd-rg-...` | Test 9 |

## 2.2  Assign Chapter 1 to the lab - with enforcement still OFF

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

Always assign first with `DoNotEnforce`. Then prove that nothing is blocked. Then switch enforcement on. This is the same habit you would use in a real landing zone.

```powershell
az policy assignment create --name "alz-pd-c1-lab" `
  --display-name "ALZ PD - Chapter 1 PREVENT (LAB)" `
  --description "Chapter 1 guardrails on the disposable lab. Enforcement is switched on during the demo." `
  --policy-set-definition "$SCOPE_SUB/providers/Microsoft.Authorization/policySetDefinitions/alz-pd-c1-prevent" `
  --scope $SCOPE_LAB --enforcement-mode DoNotEnforce `
  --non-compliance-messages "@$WORK/c1-messages.json"
```

> **What you should see**
>
> A JSON block that contains `"enforcementMode": "DoNotEnforce"` and the scope `.../resourceGroups/rg-alz-policy-lab`.

### Option B - create the same assignment with the Azure Portal wizard

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Assignments** > **Assign initiative**.

> [!CAUTION]
> **Use either the command or the wizard - not both**
>
> If you already ran the `az policy assignment create` command above, **do not** create the assignment a second time. Use these steps only to learn the wizard, or instead of the command.
>
> A **Portal-created assignment gets an automatic internal name** (a long hexadecimal string, visible in *Assignment ID*), not `alz-pd-c1-lab`. If you use the wizard, every later command that says `--name alz-pd-c1-lab` must use that automatic name. Find it with `az policy assignment list --scope $SCOPE_LAB --query "[].{name:name, displayName:displayName}" -o table`.

1. Policy > **Authoring** > **Assignments** > toolbar **Assign initiative**. (Fields with a red star are required.)
2. Tab **Basics**. Next to **Scope** click the blue **...** button. In the **Scope** blade choose your **Subscription** and **Resource Group** = `rg-alz-policy-lab`, then click **Select**.
3. Next to **Initiative definition** click the blue **...** button. In **Available Definitions** click the pill **Policy type**, tick **Custom**, **Apply**. Type `ALZ PD` in **Search**, tick **ALZ PD - Chapter 1 PREVENT: block unsafe deployments**, click **Add**.
4. In **Assignment name** type `ALZ PD - Chapter 1 PREVENT (LAB)`. In **Description** type a short sentence.
5. Under **Policy enforcement** choose the radio button **Do not enforce**. (The other choices are **Default (enforcement)** and **Enroll**.)
6. Click **Next** until you reach **Non-compliance messages**. Type a sentence in **Default non-compliance message**, for example *Guardrail (Chapter 1 - Prevent): read the policy name in this error*. (The one sentence per rule that the command adds needs the JSON file.)
7. On the tabs **Parameters**, **Remediation** and **Managed identity** change nothing: Chapter 1 has default values and needs no identity.
8. Click **Review + create**, check the summary (*Policy enforcement: Do not enforce*), and click **Create**.

> [!NOTE]
> **The tabs of the wizard**
>
> Basics, Parameters, Remediation, Managed identity, Non-compliance messages, Review + create. There is **no Advanced tab** in the current Portal: **Resource selectors** and **Overrides** are collapsible sections on the Basics tab.

### Prove that nothing is blocked yet

Create something that **breaks the tag rule** (no tags at all). With enforcement off it must succeed:

```powershell
az network nsg create -g $RG_LAB -n nsg-pd-notags -l $LOC --query NewNSG.provisioningState -o tsv
az network nsg delete -g $RG_LAB -n nsg-pd-notags
```

> **What you should see**
>
> `Succeeded`. The NSG was created even though it has no `CostCenter` or `Owner` tag, because the assignment is `DoNotEnforce`. (The second command removes it again.)

> **What to say**
>
> This is the **safety switch**. The rule exists and is watching, but it cannot block anything yet. In production we leave it like this until we are sure that no legitimate work would be refused.

## 2.3  Switch enforcement ON in the lab and wait until it is active

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

```powershell
az policy assignment update --name "alz-pd-c1-lab" --scope $SCOPE_LAB --enforcement-mode Default
```

### Option B - switch enforcement on in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Authoring** > **Assignments**.

1. Policy > **Authoring** > **Assignments**. Click the **Scope** pill, choose the resource group `rg-alz-policy-lab`, **Select**.
2. Click **ALZ PD - Chapter 1 PREVENT (LAB)**. In **Essentials** you now see *Policy enforcement : DoNotEnforce*.
3. Click **Edit assignment** in the toolbar. On the **Basics** tab, under **Policy enforcement**, choose **Default (enforcement)**.
4. Click **Review + save**, then **Save**. Open the assignment again: *Policy enforcement : Default*.

> [!WARNING]
> **Common trap**
>
> The Portal does **not** call this setting *Enabled / Disabled* any more (older documents do). The CLI values are `Default` and `DoNotEnforce`; the Portal labels are **Default (enforcement)** and **Do not enforce**.

**Wait until the rule is really active.** The next block tries to create an untagged NSG once a minute. While the policy is not active yet, the NSG is created and the block deletes it again and waits. The moment Azure refuses, the block stops and tells you. It is self-cleaning.

```powershell
for ($i = 1; $i -le 15; $i++) {
  $out = az network nsg create -g $RG_LAB -n nsg-pd-probe -l $LOC 2>&1 | Out-String
  if ($out -match 'RequestDisallowedByPolicy') { "Policy is ACTIVE after $i attempt(s)."; break }
  az network nsg delete -g $RG_LAB -n nsg-pd-probe 2>$null | Out-Null
  "Attempt $i : not active yet - waiting 60 seconds"
  Start-Sleep -Seconds 60
}
```

> **What you should see**
>
> `Attempt 1 : not active yet...` a few times, then `Policy is ACTIVE after N attempt(s).` Expect N between 1 and 8 (in the dry run it was 1).

**Then wait 10 more minutes.** The probe tests one rule only (the tag rule). Azure Policy does not switch on every rule of an initiative at the same moment. In the dry run the probe was refused on the first attempt, yet Tests 1 and 3 were still *allowed* two to three minutes later, and were refused only when they were run again about ten minutes after enforcement was switched on.

```powershell
"Probe done. Waiting 10 more minutes so that every rule of the initiative is active ..."
Start-Sleep -Seconds 600
```

> [!WARNING]
> **Common trap**
>
> If you try a test **too early**, the 'unsafe' resource is simply created and you think the policy is broken. It is not: it is not active yet. Use the probe above, wait the extra 10 minutes, and if a test creates something by mistake, delete it with the matching `az ... delete` command, wait a few minutes and run the test again.

## 2.4  The tests - try the unsafe thing, then the safe thing

Every test has the same shape: **(a)** run the unsafe command and read the error; **(b)** run the safe command and see it succeed. Read the error from the top. You only need three things from it: the **code** (`RequestDisallowedByPolicy`), the **friendly sentence** after *Reasons*, and the **policy assignment name** (it must start with `ALZ PD`).

### What a Deny error looks like

*Example output - do not type this:*

```text
ERROR: (RequestDisallowedByPolicy) Resource 'stalzpdbad01a1b2' was disallowed by policy.
       Reasons: 'F3 Data in transit: storage accounts must require HTTPS.'.
       See error details for policy resource IDs.
Code: RequestDisallowedByPolicy
Additional Information: Type: PolicyViolation
  policyAssignment : "ALZ PD - Chapter 1 PREVENT (LAB)"   <- who is blocking you
  policyDefinition : "Secure transfer to storage accounts should be enabled"   <- which rule
```

> [!NOTE]
> The exact layout differs a little between Azure CLI versions and between the CLI and the Portal. The three items above are always present (Tests 8 and 9 show the assignment name but no friendly sentence, because those two assignments have no non-compliance message). Resource names in the message come back in lowercase.

### Test 1 - F1 Locations: a region that is not approved

> **Where to do this:** **PowerShell window.**

**(a) Unsafe:** create an NSG in East US. (The tags are correct, so the *only* rule that can object is the location rule. East US is used because it is not in the approved list and, in most tenants, nothing else blocks it.)

```powershell
az network nsg create -g $RG_LAB -n nsg-pd-eastus -l eastus --tags $TAGS
```

> **What you should see**
>
> **Denied.** The error names the rule *Allowed locations* and the sentence *'F1 Locations: deploy only in Indonesia Central or Southeast Asia.'*

**(b) Safe:** the same NSG in Indonesia Central:

```powershell
az network nsg create -g $RG_LAB -n nsg-pd-ok -l $LOC --tags $TAGS --query NewNSG.provisioningState -o tsv
```

> **What you should see**
>
> `Succeeded`.

> **What to say**
>
> Only the approved regions are possible. A developer cannot accidentally put data in a region that the organisation has not approved. This is the *technical* part of data-location control; the decision about *which* workloads need it stays with the organisation.

### Test 2 - F2 Public exposure: a network interface with a public IP

> **Where to do this:** **PowerShell window.**

A public IP address by itself is allowed. The rule blocks **attaching** one to a network interface. First create the address (it works), then try to attach it:

```powershell
az network public-ip create -g $RG_LAB -n pip-pd-lab -l $LOC --sku Standard --allocation-method Static `
  --tags $TAGS --query publicIp.provisioningState -o tsv

# (a) Unsafe: a NIC that uses the public IP
az network nic create -g $RG_LAB -n nic-pd-bad -l $LOC --vnet-name vnet-pd-lab --subnet snet-pd-lab `
  --public-ip-address pip-pd-lab --tags $TAGS
```

> **What you should see**
>
> `Succeeded` for the public IP. **Denied** for the NIC, naming *Network interfaces should not have public IPs* and the sentence *'F2 Public exposure: a network interface must not have a public IP.'*

**(b) Safe:** the same NIC without a public IP:

```powershell
az network nic create -g $RG_LAB -n nic-pd-ok -l $LOC --vnet-name vnet-pd-lab --subnet snet-pd-lab `
  --tags $TAGS --query NewNIC.provisioningState -o tsv
```

> **What you should see**
>
> `Succeeded`.

> **What to say**
>
> No compute can get a public IP by accident. Anything that must be reachable from the Internet has to go through the Application Gateway and its WAF, which is the design in the landing zone.

### Test 3 - F2 Public exposure: an NSG rule that opens RDP to the Internet

> **Where to do this:** **PowerShell window.**

```powershell
# (a) Unsafe: allow RDP (3389) from the Internet
az network nsg rule create -g $RG_LAB --nsg-name nsg-pd-lab -n allow-rdp-from-internet --priority 100 `
  --direction Inbound --access Allow --protocol Tcp --source-address-prefixes Internet --destination-port-ranges 3389

# (b) Safe: allow RDP only from the Bastion subnet of the hub
az network nsg rule create -g $RG_LAB --nsg-name nsg-pd-lab -n allow-rdp-from-bastion --priority 110 `
  --direction Inbound --access Allow --protocol Tcp --source-address-prefixes 10.110.2.0/26 --destination-port-ranges 3389 `
  --query provisioningState -o tsv
```

> **What you should see**
>
> (a) **Denied** by the custom rule *ALZ PD - NSG rules must not allow Internet access to SSH or RDP*. (b) `Succeeded`.

> **What to say**
>
> The platform will not accept a rule that opens RDP or SSH to the Internet - not even the shortcut people use when they are in a hurry: 'allow from anywhere, I will fix it later'. Administrators use the hub's Bastion instead.

### Test 4 - F3 Data in transit: a storage account without HTTPS

> **Where to do this:** **PowerShell window.**

```powershell
# (a) Unsafe: allow plain HTTP
az storage account create -g $RG_LAB -n $ST_BAD -l $LOC --sku Standard_LRS --kind StorageV2 `
  --https-only false --tags $TAGS

# (b) Safe: HTTPS only, TLS 1.2, double encryption at rest, no public network access
az storage account create -g $RG_LAB -n $ST_OK -l $LOC --sku Standard_LRS --kind StorageV2 `
  --https-only true --min-tls-version TLS1_2 --require-infrastructure-encryption true --public-network-access Disabled --tags $TAGS `
  --query provisioningState -o tsv
```

> **What you should see**
>
> (a) **Denied** - in the dry run by **two** rules: *Secure transfer to storage accounts should be enabled* and *Storage accounts should have the specified minimum TLS version* (the unsafe command does not set a TLS version, so Azure's default is refused as well). (b) `Succeeded` after about 30 seconds.

> [!WARNING]
> **COMMON TRAP - why not test anonymous blob access?**
>
> Some tenants have an inherited Modify policy that silently sets `allowBlobPublicAccess=false` on every new storage account **before** any Deny rule is evaluated (the order is Modify first, Deny second). A Deny rule for that setting would then never fire, which makes it a poor demonstration. HTTPS-only is rarely touched by such policies, so it makes a clean demonstration.

> [!NOTE]
> The unsafe command does not set a TLS version, so Azure's default is refused by *Storage accounts should have the specified minimum TLS version* as well (see above). A dedicated old-TLS test is not run: Azure has been retiring TLS 1.0 and 1.1, so an old-TLS request may be refused by Azure itself rather than by policy.

> **What to say**
>
> Every storage account must use encrypted transport. The second account also turns on **infrastructure encryption**, which is a Chapter 2 finding on the existing storage account of the sample application - you will see the contrast later.

### Test 5 - F4 Stored data and keys: a Key Vault without purge protection

> **Where to do this:** **PowerShell window.**

```powershell
# (a) Unsafe: no purge protection
az keyvault create -g $RG_LAB -n $KV_BAD -l $LOC --retention-days 7 --enable-rbac-authorization true --tags $TAGS
```

> **What you should see**
>
> **Denied** by *Key vaults should have deletion protection enabled* with the sentence *'F4 Stored data and keys: a Key Vault needs purge protection.'*

> [!NOTE]
> The **safe** version of this test (a vault with `--enable-purge-protection true`) is created later, in section 4.5, because it is also the best example of Chapter 3's automatic diagnostic settings. Purge protection cannot be switched off once enabled, so the vault is created only once.

> **What to say**
>
> A deleted vault, or a key inside it, can be recovered for a retention period - and with purge protection nobody, not even an administrator, can destroy it early. That protects your keys against accidents and against a malicious insider.

### Test 6 - F8 Network segmentation: a default route that bypasses the firewall

> **Where to do this:** **PowerShell window.**

```powershell
az network route-table create -g $RG_LAB -n rt-pd-lab -l $LOC --tags $TAGS -o none
az network route-table show -g $RG_LAB -n rt-pd-lab --query provisioningState -o tsv

# (a) Unsafe: send all Internet traffic straight out
az network route-table route create -g $RG_LAB --route-table-name rt-pd-lab -n default-to-internet `
  --address-prefix 0.0.0.0/0 --next-hop-type Internet

# (b) Safe: send it through the hub firewall
az network route-table route create -g $RG_LAB --route-table-name rt-pd-lab -n default-to-firewall `
  --address-prefix 0.0.0.0/0 --next-hop-type VirtualAppliance --next-hop-ip-address 10.110.0.4 `
  --query provisioningState -o tsv
```

> **What you should see**
>
> The route table shows `Succeeded`. (a) **Denied** by *ALZ PD - The default route must go through the hub firewall*. (b) `Succeeded`.

> **What to say**
>
> Every workload's outbound traffic must pass the hub firewall, where it can be inspected and logged. A team cannot 'optimise' this away with a quick route to the Internet. This is exactly how `rt-alz-corp-prod` for the sample application is built.

> [!NOTE]
> **What tests 3 and 6 prove - and do not prove**
>
> Both tests prove what the policy **accepts and refuses** when someone writes a rule. They do not carry traffic: the lab network is deliberately **not connected** to the hub, and the lab route table is not attached to a subnet. So the safe version (b) does not prove that Bastion can reach a lab VM, or that packets really pass the firewall. For the real, end-to-end picture use the sample application's own network (Figure 1).

### Test 7 - F9 Ownership: a resource without tags

> **Where to do this:** **PowerShell window.**

```powershell
# (a) Unsafe: no tags at all
az network nsg create -g $RG_LAB -n nsg-pd-notags -l $LOC
```

> **What you should see**
>
> **Denied.** The error lists **two** policies: *Require a tag on resources* for `CostCenter` **and** for `Owner`. (The two sentences begin with *F9 Ownership*.) The safe version is the NSG you created in Test 1(b).

> **What to say**
>
> Every resource has an owner and a cost centre from the moment it exists. Nobody has to chase 'who owns this?' months later. In Chapter 3 you will see a smarter way: instead of *refusing* an untagged resource, Azure can *add* the tags itself.

### Test 8 - F8 Network segmentation: peering two isolated networks

> **Where to do this:** **PowerShell window.**

This test reuses the custom policy `alz-deny-vnet-peering` that the reference landing zone already created (it keeps the sandbox isolated). Assign it to the lab with enforcement on, then try to peer two throw-away networks:

```powershell
az policy assignment create --name "alz-pd-lab-nopeering" `
  --display-name "ALZ PD - No VNet peering (LAB)" `
  --policy "$SCOPE_SUB/providers/Microsoft.Authorization/policyDefinitions/alz-deny-vnet-peering" `
  --scope $SCOPE_LAB --enforcement-mode Default

az network vnet create -g $RG_LAB -n vnet-pd-peer-a -l $LOC --address-prefixes 10.251.0.0/24 `
  --tags $TAGS --query newVNet.provisioningState -o tsv
az network vnet create -g $RG_LAB -n vnet-pd-peer-b -l $LOC --address-prefixes 10.252.0.0/24 `
  --tags $TAGS --query newVNet.provisioningState -o tsv
```

Wait about 5 minutes for the new assignment, then try the peering:

```powershell
az network vnet peering create -g $RG_LAB -n a-to-b --vnet-name vnet-pd-peer-a `
  --remote-vnet vnet-pd-peer-b --allow-vnet-access
```

> **What you should see**
>
> **Denied** by *ALZ - Deny virtual network peering (isolated landing zone)*. The error names the assignment `ALZ PD - No VNet peering (LAB)` but, in the dry run, showed **no friendly sentence** (that assignment has no non-compliance message). If it succeeds, the assignment is not active yet: delete the peering with `az network vnet peering delete -g $RG_LAB --vnet-name vnet-pd-peer-a -n a-to-b`, wait 5 minutes and try again.

> **What to say**
>
> An isolated sandbox stays isolated. Nobody can quietly connect it to the corporate network, because the platform refuses the peering - it is not a convention people have to remember.

### Test 9 - F1 and F9 at resource-group level

> **Where to do this:** **PowerShell window.**

Resource groups are created at **subscription** level, so these two rules are assigned to the subscription. Remember: they only match groups named `rg-alz-*`, so other resource groups are not affected. They are switched on for the test and switched off straight after.

```powershell
az policy assignment create --name "alz-pd-rg-tags" --display-name "ALZ PD - rg-alz-* need required tags" `
  --policy "$SCOPE_SUB/providers/Microsoft.Authorization/policyDefinitions/alz-pd-rg-required-tags" `
  --scope $SCOPE_SUB --enforcement-mode Default
az policy assignment create --name "alz-pd-rg-loc" --display-name "ALZ PD - rg-alz-* need an approved region" `
  --policy "$SCOPE_SUB/providers/Microsoft.Authorization/policyDefinitions/alz-pd-rg-allowed-locations" `
  --scope $SCOPE_SUB --enforcement-mode Default
```

Wait about 5 minutes. Then:

```powershell
# (a) Unsafe: wrong region and no tags
az group create -n rg-alz-pd-bad -l eastus

# (b) Safe: approved region and both tags (a different name, on purpose)
az group create -n rg-alz-pd-ok -l $LOC --tags $TAGS --query properties.provisioningState -o tsv
az group delete -n rg-alz-pd-ok --yes
```

> **What you should see**
>
> (a) **Denied** by both rules (the error names the two `ALZ PD` assignments, without a friendly sentence). (b) `Succeeded`, and the group is deleted again. **If (a) was not denied**, the new assignments are not active yet: delete the group that (a) created with `az group delete -n rg-alz-pd-bad --yes`, wait 3 minutes and run (a) again. **Then switch both rules off so that nothing at subscription level stays enforcing:**

```powershell
az policy assignment update --name "alz-pd-rg-tags" --scope $SCOPE_SUB --enforcement-mode DoNotEnforce
az policy assignment update --name "alz-pd-rg-loc"  --scope $SCOPE_SUB --enforcement-mode DoNotEnforce
```

> [!CAUTION]
> Do not forget the last two commands. While these assignments are enforcing, **nobody** (not even you) can create a resource group named `rg-alz-...` without the tags. Part 5 checks that they are off.

### Test 10 - See the same denial in the Azure Portal

> **Where to do this:** **Azure Portal** - **Storage accounts** > **Create**, and then the **Activity log**. You will **not** create anything: you only want to see the refusal.

**Part A - provoke the denial in the wizard.** Do this only after the lab policy is enforcing (step 2.3).

1. Top search box: type `Storage accounts` and click **Storage accounts** (under Services). Click **Create** (first button in the toolbar).
2. Tab **Basics**: **Resource group** = `rg-alz-policy-lab`; **Storage account name** = `stalzpdportal01a1b2`; **Region** = **(Asia Pacific) Indonesia Central**; **Performance** = Standard; **Redundancy** = **Locally-redundant storage (LRS)** (the default *Geo-redundant storage* needs a paired region, and Indonesia Central has none).
3. Click **Next** until you reach the tab **Security**. **Un-tick** **Require secure transfer for REST API operations**. (It is on the **Security** tab, not on *Advanced*. The drop-down **Minimum TLS version** on the same tab offers only *Version 1.2*, so an old-TLS test is not possible in the Portal.)
4. Tab **Tags**: add **CostCenter** = `ALZ-Demo` and **Owner** = your alias, so that HTTPS is the *only* rule you break.
5. Click the tab **Review + create** and wait for the validation. **What you should see:** a red **Validation failed** message (or, if you click **Create**, a failed deployment) whose text contains **was disallowed by policy** and names the policy *Secure transfer to storage accounts should be enabled* and the assignment *ALZ PD - Chapter 1 PREVENT (LAB)*.
6. Close the wizard with the **X** (top right). Nothing was created.

> [!NOTE]
> **Not verified live**
>
> The Portal denial was not captured in the dry run (the Portal boxes and this test have not been run yet), so the exact wording of the validation banner is **not** quoted. What the Microsoft documentation guarantees: the message contains *was disallowed by policy* and the *policy identifiers* (assignment and definition names), and the refusal is an HTTP 403 that appears as a failed deployment and in the Activity log.

**Part B - see every denial in the Activity log.** This works because the lab assignment is enforcing. (A `DoNotEnforce` assignment writes no deny entries.)

1. Open the resource group `rg-alz-policy-lab` (top search box) and click **Activity log** in its left menu - or open the **subscription** and click **Activity log**.
2. Click **+ Add Filter** and choose **Operation** in the first drop-down. Click the value drop-down, press the **down arrow key** on the keyboard (a mouse click may not open the list), type `deny`, and tick **'deny' Policy action. (Microsoft.Authorization/policies/deny/action)**. Set the **Timespan** pill to **Last 6 hours**.
3. Click one row. In the blade on the right open the tab **JSON** and look for `policyAssignment` and `policyDefinition`: the exact rule that refused you.

> [!TIP]
> You can also type `RequestDisallowedByPolicy` into the Activity log search box (*Find text in logs*).

## 2.5  What the lab now contains

> **Where to do this:** **PowerShell window.**

```powershell
az resource list -g $RG_LAB --query "[].{name:name, type:type}" -o table
```

> **What you should see**
>
> Only the **safe** things exist: `nsg-pd-lab`, `nsg-pd-ok`, `vnet-pd-lab`, `vnet-pd-peer-a`, `vnet-pd-peer-b`, `pip-pd-lab`, `nic-pd-ok`, `rt-pd-lab`, `$ST_OK` (the storage account), and the VM with its NIC and disk. None of the 'bad' names (`nsg-pd-eastus`, `nic-pd-bad`, the storage account `$ST_BAD`, the vault `$KV_BAD`) exists - the policy stopped them.

```powershell
Show-Compliance -RG $RG_LAB -Assignment alz-pd-c1-lab
```

> **What you should see**
>
> `No NonCompliant rows for alz-pd-c1-lab in rg-alz-policy-lab` (shown in green). Policy prevented every non-compliant resource, so none exists. (Compliance data can take 10 to 20 minutes to appear.)

## 2.6  The impact on the sample application - the same rules, without blocking

> **Where to do this:** **PowerShell window.** The Portal alternative follows the commands.

Now answer the question every stakeholder asks: *'What would these rules do to the application we already run?'* Assign the **same initiative** to production, but with enforcement **off**. It cannot block anything; it only reports.

```powershell
az policy assignment create --name "alz-pd-c1-prod" `
  --display-name "ALZ PD - Chapter 1 PREVENT (PROD what-if)" `
  --description "Impact preview only. Enforcement is OFF and must stay OFF." `
  --policy-set-definition "$SCOPE_SUB/providers/Microsoft.Authorization/policySetDefinitions/alz-pd-c1-prevent" `
  --scope $SCOPE_CORP --enforcement-mode DoNotEnforce `
  --non-compliance-messages "@$WORK/c1-messages.json"

az policy state trigger-scan -g $RG_CORP --no-wait
```

Wait **10 to 20 minutes** (this is a good moment for a break), then look at the result:

```powershell
Show-Compliance -RG $RG_CORP -Assignment alz-pd-c1-prod
Show-Compliance -RG $RG_CORP -Assignment alz-pd-c1-prod -State Compliant
```

> **What you should see**
>
> The non-compliant list contains **27 rows** in the dry run (resource names come back in lowercase):
>
> - **1 x `KeyVaultPurgeProtection`** - the Key Vault `kv-alz-a1b2` (family F4).
> - **26 x `RequireOwnerTag`** - every sample-application resource lacks an `Owner` tag (family F9).
>
> Everything else is **compliant**: the locations, the NICs (private endpoints have no public IP), the NSG rules, the HTTPS and TLS settings on the storage account and the two web apps, the route table, and the `CostCenter` tag.

> **What to say**
>
> The sample application was built well: of the ten Chapter 1 rules, **eight are already satisfied** by the real application. Two are not: the Key Vault has no purge protection, and no resource has an owner tag. If we switched enforcement on today, those resources would be reported - and a change to them could be refused until they are fixed. That is why we **audit first**. Chapter 3 fixes the tags; the Key Vault needs a deliberate decision because purge protection cannot be undone.

### Prove the application is untouched

```powershell
Test-SampleApp
```

> **What you should see**
>
> Still **403** directly and backend health **Healthy** (and **200** through the gateway from a client the gateway accepts) - the same values as in step 1.4. Nothing was blocked, changed or restarted.

### See the impact in the Azure Portal

> **Where to do this:** **Azure Portal** - **Policy** > **Quick Access** > **Compliance**.

1. Policy > left menu > **Compliance**. Click the **Scope** pill. In the **Scope** blade choose your **Subscription** and **Resource Group** = `rg-alz-corp-prod`, then **Select**.
2. Type `ALZ PD` in the **Search** box. Find **ALZ PD - Chapter 1 PREVENT (PROD what-if)**. The columns show **Compliance state** (*Non-compliant*), **Resource compliance** (a percentage) and **Non-compliant resources**.
3. Click the row. You see the tiles *Compliance state* and *Resources by compliance state*, and two tabs: **Policies** and **Non-compliant resources**.
4. On the **Policies** tab sort by **Non-compliant resources**. You see **Require a tag on resources** (26, the `Owner` tag) and **Key vaults should have deletion protection enabled** (1).
5. Click **Require a tag on resources**. On the tab **Resource Compliance** click **Details** in the **Compliance reason** column of one row: the side blade **Compliance details** shows the state and *Last evaluated*.

> [!NOTE]
> **Resource group shortcut**
>
> In a resource group's left menu, **Settings** > **Policies** opens the same Compliance page already scoped to that resource group.

## 2.7  Chapter 1 recap

| Family | What you proved | Evidence |
| --- | --- | --- |
| F1 Locations | A resource cannot be created outside the approved regions. | Test 1 and Test 9 |
| F2 Public exposure | No public IP on a NIC; no Internet-open SSH or RDP. | Tests 2 and 3 |
| F3 Data in transit | A storage account must require HTTPS. | Test 4 |
| F4 Stored data and keys | A Key Vault must have purge protection. | Test 5; production impact in 2.6 |
| F8 Network segmentation | The default route must use the hub firewall; isolated networks cannot be peered. | Tests 6 and 8 |
| F9 Ownership | A resource must have `CostCenter` and `Owner` tags. | Tests 7 and 9; production impact in 2.6 |

> [!IMPORTANT]
> **CHECKPOINT - do not continue until all of this is true**
>
> - Every 'unsafe' command was **denied**, and every 'safe' command **succeeded**.
> - `Show-Assignments` shows `alz-pd-c1-lab` and `alz-pd-lab-nopeering` as **Default** (enforcing, lab only) and `alz-pd-c1-prod`, `alz-pd-rg-tags`, `alz-pd-rg-loc` as **DoNotEnforce**.
> - `Test-SampleApp` still shows **403** directly and backend health **Healthy** (and **200** through the gateway, if your client can reach it).

---

[Runbook index](README.md) &middot; Previous: [Part 1 - Prepare the stage](01-prepare-the-stage.md) &middot; Next: [Part 3 - Chapter 2: DETECT - find the gaps](03-chapter-2-detect.md)
