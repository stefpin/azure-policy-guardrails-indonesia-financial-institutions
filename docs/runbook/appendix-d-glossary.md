# Appendix D - Glossary

[Runbook index](README.md) &middot; Previous: [Appendix C - Inherited policies: what to look for](appendix-c-inherited-policies.md) &middot; Next: [Appendix E - One-page crib sheet](appendix-e-crib-sheet.md)

| Term | Meaning |
| --- | --- |
| Alias | The name Azure Policy uses for a property of a resource, for example `Microsoft.Storage/storageAccounts/supportsHttpsTrafficOnly`. |
| Assignment | Switches a policy or initiative on for a scope. |
| Audit / AuditIfNotExists | Effects that only report non-compliance. |
| Compliance state | Compliant, Non-compliant, Exempt or Not started. |
| Definition | One policy rule written in JSON. |
| Deny | Effect that blocks a create or update request. |
| DeployIfNotExists (DINE) | Effect that deploys a missing related resource. |
| DoNotEnforce | Enforcement mode in which effects are not applied but compliance is still reported. In the Portal the radio button is called **Do not enforce**. |
| Effect | What a policy does when its rule matches. |
| Enforcement mode | `Default` (Portal: **Default (enforcement)**) applies effects; `DoNotEnforce` (Portal: **Do not enforce**) does not. |
| Exemption | A recorded, time-limited exception for a resource. Categories: Mitigated and Waiver. |
| Initiative (policy set) | A package of policy definitions. |
| Landing zone | A prepared, governed Azure environment for workloads (network, identity, policy, monitoring). |
| Log Analytics workspace | The Azure Monitor store that holds logs and answers KQL queries. |
| Managed identity | An identity that belongs to an Azure resource or assignment, so that no password is needed. |
| Mode (Indexed / All) | Whether a definition looks only at taggable resources (Indexed) or at everything (All). |
| Modify | Effect that changes a resource property, for example adds a tag. |
| Non-compliance message | A custom sentence shown when a rule blocks or flags a resource. |
| Purge protection | A Key Vault setting that prevents a deleted vault or secret from being destroyed before its retention period ends. It cannot be turned off. |
| RBAC | Role-based access control: **who** may do what. Different from Azure Policy: **what** is allowed to exist. |
| Remediation task | A job that applies a Modify or DeployIfNotExists fix to existing resources. |
| Scope | Where something applies: management group, subscription, resource group or resource. |
| Soft delete | Azure keeps deleted data (Azure Backup data, Key Vault items) for a retention period before it is removed for good. In new Azure Backup vaults it is always on (14 days by default). |
| Trusted Launch | A VM security type with Secure Boot and a virtual TPM. |

---

[Runbook index](README.md) &middot; Previous: [Appendix C - Inherited policies: what to look for](appendix-c-inherited-policies.md) &middot; Next: [Appendix E - One-page crib sheet](appendix-e-crib-sheet.md)
