# Policies

The JSON behind the demo: five custom policy definitions, three initiatives and a catalogue of all 38 rules.

> The runbook writes the rule, parameter, group and message files from PowerShell here-strings (steps 1.9 and 1.10) so
> that you can follow it from the pages alone. `tools/validate_repo.py` checks in CI that those 15 files here are
> semantically identical to the here-strings. The initiative reference files (`*.definitions.json`) and the assignment
> files are produced by the runbook's PowerShell (`New-Ref`, `ConvertTo-Json`), so they are checked for structure, not
> compared.

## Layout

```text
policies/
  catalog.json                                  all 38 rules: chapter, family, reference ID, policy, definition ID, effect, built-in version
  definitions/                                  the five custom definitions (mode All)
    <name>.rules.json                           the policyRule: "if ... then effect"
    <name>.parameters.json                      the parameters you can change at assignment time
  initiatives/                                  the three initiatives
    alz-pd-c1-prevent.definitions.json          the ten policy references (Prevent)
    alz-pd-c2-detect.definitions.json           the twenty-one policy references (Detect)
    alz-pd-c3-remediate.definitions.json        the seven policy references (Remediate)
    alz-pd-c*.parameters.json                   initiative parameters
    groups.json                                 the nine control families (policy definition groups)
    alz-pd-c1-prevent.non-compliance-messages.json   the friendly sentence shown inside each Deny error
  assignments/                                  parameter files used when assigning
```

## Placeholders

| Placeholder | Where | Replaced by |
|---|---|---|
| `$SUB` | the custom-definition IDs inside the initiative reference files | your subscription ID (the runbook builds the final JSON with the `New-Ref` helper from step 1.10) |
| `$LAW_ID` | `assignments/assign-law.json`, `assignments/actlog-assign.json` | the resource ID of the central Log Analytics workspace |
| `$BACKUP_POLICY_ID` | `assignments/vmbackup-assign.json` | the ID of the vault's `DefaultPolicy` (step 4.6) |

## The five custom definitions

| Name | Family | Default effect | What it checks |
|---|---|---|---|
| `alz-pd-nsg-no-internet-mgmt` | F2 | Deny | An inbound **Allow** rule from the Internet (or `*`, or `0.0.0.0/0`) to port 22, 3389 or any port - both single rules and rules inside a whole NSG |
| `alz-pd-route-default-via-fw` | F8 | Audit (the Chapter 1 initiative sets Deny) | A route to `0.0.0.0/0` must point to the hub firewall's private IP (parameter `firewallPrivateIp`) |
| `alz-pd-appgw-https-listener` | F3 | Audit | An Application Gateway with any listener whose protocol is not HTTPS (an HTTP listener that only redirects to HTTPS is flagged as well) |
| `alz-pd-rg-required-tags` | F9 | Deny | Resource groups named `rg-alz-*` must carry the two required tags (subscription scope) |
| `alz-pd-rg-allowed-locations` | F1 | Deny | Resource groups named `rg-alz-*` must be in an approved region (subscription scope) |

All five use **mode `All`**. The rules for resource groups, NSG rules and routes need it: those are resource groups or
child resources, which the default mode `Indexed` silently skips (a custom policy created in `Indexed` mode would look
healthy while doing nothing). The Application Gateway rule does not strictly need it.

## The initiatives

| Initiative | Rules | Effects | Chapter |
|---|---|---|---|
| `alz-pd-c1-prevent` | 10 | mostly `Deny` | 1 PREVENT |
| `alz-pd-c2-detect` | 21 | `Audit`, `AuditIfNotExists` | 2 DETECT |
| `alz-pd-c3-remediate` | 7 | `Modify`, `DeployIfNotExists` | 3 REMEDIATE |

Built-in definitions are referenced by their public IDs only. [`catalog.json`](catalog.json) records the display name and
the version that each ID was checked against, so you can see when a built-in has moved on.

## Using the files by hand

The runbook is the supported path. If you want to create the objects yourself, the commands look like this (see steps 1.9
and 1.10 for the real ones):

```powershell
az policy definition create --name alz-pd-nsg-no-internet-mgmt --mode All `
  --display-name "ALZ PD - NSG rules must not allow Internet access to SSH or RDP" `
  --rules "@policies/definitions/alz-pd-nsg-no-internet-mgmt.rules.json" `
  --params "@policies/definitions/alz-pd-nsg-no-internet-mgmt.parameters.json" --subscription $SUB
```

Replace `$SUB` in the initiative reference files first (for example with
`(Get-Content <file>) -replace '\$SUB', $SUB | Set-Content <out>`), then pass the result to `az policy set-definition
create --definitions "@<out>" --params "@policies/initiatives/<initiative>.parameters.json" --definition-groups
"@policies/initiatives/groups.json"`.
