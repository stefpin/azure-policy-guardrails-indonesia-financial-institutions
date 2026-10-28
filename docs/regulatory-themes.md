# Regulatory themes behind the nine control families

> [!IMPORTANT]
> **Technical guidance, not legal advice.** Azure Policy checks the *configuration of Azure resources*. A green dashboard is evidence for the technical part of a control; it does not prove that an institution complies with any regulation. Always confirm which obligations apply to you with your compliance and legal teams.

## Who the audience is

The repository is written for people who build and govern Azure environments for **financial institutions in Indonesia** - banks, non-bank financial institutions and payment providers. Their supervisors are the Financial Services Authority ([OJK](https://www.ojk.go.id)) and [Bank Indonesia](https://www.bi.go.id) (for payment systems). Their expectations about cloud use are published in regulations, circulars and supervisory guidance, and in the compliance material that cloud providers publish for the sector.

## How the families were chosen

The nine families are not a list of regulations. They are the **technical outcomes** that financial-sector guidance commonly describes, translated into things Azure Policy can inspect:

| Family | Typical outcome in sector guidance | What Azure Policy can evidence | What stays outside Azure Policy |
| --- | --- | --- | --- |
| **F1 Locations** | Know, document and approve where data and the disaster-recovery site are; offshore hosting may need approval | Resources and resource groups exist only in approved regions | Regulator approval; which workloads are location-restricted |
| **F2 Public exposure** | Appropriate security controls for confidentiality, integrity, availability and authentication | No public IPs on NICs; no Internet-open SSH/RDP; public network access disabled on data services | Penetration testing; identity design (MFA, PIM) |
| **F3 Data in transit** | Encryption of data in transit | HTTPS-only and minimum TLS; HTTPS listeners | Certificate lifecycle |
| **F4 Stored data and keys** | Protection against unauthorised access, disclosure, alteration, loss or destruction | Infrastructure encryption, encryption at host, Key Vault purge protection and RBAC | Key management procedures; data classification |
| **F5 Monitoring** | A monitoring plan; regular monitoring of the provider's performance and continuity | Diagnostic settings exist and go to one central workspace | The people and process that read the logs; incident reporting |
| **F6 Backup and recovery** | A tested, adequate disaster-recovery plan; clear backup arrangements | Backup is configured; geo-redundancy is reported | The DR plan, recovery targets and the restore **test** |
| **F7 Compute baseline** | System security standards | Trusted Launch, vulnerability assessment, encryption at host findings | Patching and hardening operations |
| **F8 Network segmentation** | Security of data access and transmission | Default route through the hub firewall; NSGs present; sandbox isolation | Firewall rule review |
| **F9 Ownership** | Clear accountability for systems and their data | Every resource has an `Owner` and a `CostCenter` | Governance and accountability processes |

## What the regulations do *not* say

Regulation and guidance describe **outcomes**. They do **not** name Azure regions, Azure Policy definitions, a TLS version, private endpoints, tag names, customer-managed keys, log-retention days, recovery targets or VM sizes. Every one of those is a **design choice that this repository proposes**. Treat it as a source of technical guardrail ideas that you adapt to your own risk assessment.

## What not to claim

- Do **not** say that these policies make an institution "compliant". Say they provide **technical guardrails and configuration evidence for the Azure part** of a control.
- Do **not** quote a regulation from this repository. It cites none, on purpose: the applicable text and its current version are for your compliance team to confirm.
- Do **not** treat the 38 rules as complete. They cover what Azure Policy can inspect on this particular workload.

## Adapting the policies to your institution

| To change... | Edit... |
| --- | --- |
| The approved regions | `allowedLocations` default in `policies/initiatives/alz-pd-c1-prevent.parameters.json` and `policies/definitions/alz-pd-rg-allowed-locations.parameters.json` |
| The required tags | `costCenterTagName` and `ownerTagName` in the initiative parameters |
| The hub firewall address | `firewallPrivateIp` in the Chapter 1 parameters |
| The minimum TLS version | `minimumTlsVersion` in the Chapter 1 parameters |
| Where the rules are assigned | The runbook assigns at resource-group scope because the demo has one subscription. A real landing zone assigns the same initiatives **once at a management group**; every subscription below inherits them |
| Audit-to-enforce | Roll out in this order: assign with `DoNotEnforce`, read the impact, fix or exempt, then switch to `Default` after approval - exactly the habit the runbook teaches |

## Where to look next

- Financial Services Authority (OJK): https://www.ojk.go.id
- Bank Indonesia: https://www.bi.go.id
- Azure Policy overview: https://learn.microsoft.com/azure/governance/policy/overview
- Azure landing zones: https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/
- Compliance material that your cloud provider publishes for the sector (for Microsoft, the Service Trust Portal and Microsoft Learn compliance offerings).
