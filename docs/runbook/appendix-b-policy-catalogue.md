# Appendix B - Policy catalogue

[Runbook index](README.md) &middot; Previous: [Appendix A - Everything this runbook creates](appendix-a-everything-this-runbook-creates.md) &middot; Next: [Appendix C - Inherited policies: what to look for](appendix-c-inherited-policies.md)

All 38 rules of the three initiatives. Names and IDs were read from the live Azure Policy catalogue in October 2026. 'Effect' is the effect the initiative sets, spelled as the definition spells it (so a few are in lower case). Thirty-five of the 38 rules are built-in definitions; three are custom (marked `alz-pd-...`). The other two custom definitions (resource-group tags and locations) are assigned separately.

| Chapter | Fam. | Reference ID | Policy | Definition ID | Effect |
| --- | --- | --- | --- | --- | --- |
| 1 Prevent | F1 | `AllowedLocations` | Allowed locations | `e56962a6-4747-49cd-b67b-bf8b01975c4c` | Deny |
| 1 Prevent | F2 | `NoPublicIpOnNic` | Network interfaces should not have public IPs | `83a86a26-fd1f-447c-b59d-e51f44264114` | deny |
| 1 Prevent | F2 | `NsgNoInternetMgmtPorts` | ALZ PD - NSG rules must not allow Internet access to SSH or RDP | `alz-pd-nsg-no-internet-mgmt` | Deny |
| 1 Prevent | F3 | `StorageSecureTransfer` | Secure transfer to storage accounts should be enabled | `404c3081-a854-4457-ae30-26a93ef643f9` | Deny |
| 1 Prevent | F3 | `StorageMinTls` | Storage accounts should have the specified minimum TLS version | `fe83a0eb-a853-422d-aac2-1bffd182c5d0` | Deny |
| 1 Prevent | F3 | `AppServiceHttpsOnly` | App Service apps should only be accessible over HTTPS | `a4af4a39-4135-47fb-b175-47fbdf85311d` | Deny |
| 1 Prevent | F4 | `KeyVaultPurgeProtection` | Key vaults should have deletion protection enabled | `0b60c0b2-2dc2-4e1c-b5c9-abbed971de53` | Deny |
| 1 Prevent | F8 | `RouteDefaultViaFirewall` | ALZ PD - The default route must go through the hub firewall | `alz-pd-route-default-via-fw` | Deny |
| 1 Prevent | F9 | `RequireCostCenterTag` | Require a tag on resources | `871b6d14-10aa-478d-b590-94f262ecfa99` | deny |
| 1 Prevent | F9 | `RequireOwnerTag` | Require a tag on resources | `871b6d14-10aa-478d-b590-94f262ecfa99` | deny |
| 2 Detect | F2 | `AppServicePublicAccess` | App Service apps should disable public network access | `1b5ef780-c53c-4a64-87f3-bb9c8c8094ba` | Audit |
| 2 Detect | F2 | `StoragePublicAccess` | Storage accounts should disable public network access | `b2982f36-99f2-4db5-8eff-283140c09693` | Audit |
| 2 Detect | F2 | `KeyVaultPublicAccess` | Azure Key Vault should disable public network access | `405c5871-3e91-4644-8a63-58e19d68ff5b` | Audit |
| 2 Detect | F2 | `PostgresPublicAccess` | Public network access should be disabled for PostgreSQL flexible servers | `5e1de0e3-42cb-4ebc-a86d-61d0c619ca48` | Audit |
| 2 Detect | F2 | `ManagedRedisPublicAccess` | [Preview]: Azure Managed Redis should disable public network access | `0f8a6cc3-040f-4b9b-8828-b37490729517` | Audit |
| 2 Detect | F2 | `VmManagementPortsClosed` | Management ports should be closed on your virtual machines | `22730e10-96f6-4aac-ad84-9383d35b5917` | AuditIfNotExists |
| 2 Detect | F3 | `AppGatewayHttpsListener` | ALZ PD - Application Gateway listeners must use HTTPS | `alz-pd-appgw-https-listener` | Audit |
| 2 Detect | F3 | `AppServiceMinTls` | App Service apps should use the latest TLS version | `f0e6e85b-9b9f-4a4b-b67b-f730d42f1b0b` | AuditIfNotExists |
| 2 Detect | F4 | `KeyVaultUsesRbac` | Azure Key Vault should use RBAC permission model | `12d4fa5e-1f9f-4c21-97a9-b99b3c6611b5` | Audit |
| 2 Detect | F4 | `StorageInfrastructureEncryption` | Storage accounts should have infrastructure encryption | `4733ea7b-a883-42fe-8cac-97454c2a9e4a` | Audit |
| 2 Detect | F4 | `EncryptionAtHost` | Virtual machines and virtual machine scale sets should have encryption at host enabled | `fc4d8e41-e223-45ea-9bf5-eada37891d87` | Audit |
| 2 Detect | F5 | `DiagKeyVault` | Enable logging by category group for Key vaults (microsoft.keyvault/vaults) to Log Analytics | `6b359d8f-f88d-4052-aa7c-32015963ecc1` | AuditIfNotExists |
| 2 Detect | F5 | `DiagAppService` | Enable logging by category group for App Service (microsoft.web/sites) to Log Analytics | `c0d8e23a-47be-4032-961f-8b0ff3957061` | AuditIfNotExists |
| 2 Detect | F5 | `DiagPostgres` | Enable logging by category group for PostgreSQL flexible server (microsoft.dbforpostgresql/flexibleservers) to Log Analytics | `cdd1dbc6-0004-4fcd-afd7-b67550de37ff` | AuditIfNotExists |
| 2 Detect | F5 | `DiagAppGateway` | Enable logging by category group for Application gateways (microsoft.network/applicationgateways) to Log Analytics | `92012204-a7e4-4a95-bbe5-90d0d3e12735` | AuditIfNotExists |
| 2 Detect | F5 | `DiagRedisEnterprise` | Enable logging by category group for Caches (microsoft.cache/redisenterprise/databases) to Log Analytics | `fa570aa1-acca-4eea-8e5a-233cf2c5e4c2` | AuditIfNotExists |
| 2 Detect | F6 | `VmBackupEnabled` | Azure Backup should be enabled for Virtual Machines | `013e242c-8828-4970-87b3-ab247555486d` | AuditIfNotExists |
| 2 Detect | F6 | `PostgresGeoBackup` | Geo-redundant backup should be enabled for Azure Database for PostgreSQL flexible servers | `cee2f9fd-3968-44be-a863-bd62c9884423` | Audit |
| 2 Detect | F7 | `VmTrustedLaunch` | Virtual Machine should have TrustedLaunch enabled | `c95b54ad-0614-4633-ab29-104b01235cbf` | Audit |
| 2 Detect | F7 | `VmVulnerabilityAssessment` | A vulnerability assessment solution should be enabled on your virtual machines | `501541f7-f7e7-4cd6-868c-4190fdad3ac9` | AuditIfNotExists |
| 2 Detect | F8 | `SubnetHasNsg` | Subnets should be associated with a Network Security Group | `e71308d3-144b-4262-b144-efdc3cc90517` | AuditIfNotExists |
| 3 Remediate | F9 | `InheritOwnerTag` | Inherit a tag from the resource group if missing | `ea3f2387-9b95-492a-a190-fcdc54f7b070` | modify |
| 3 Remediate | F9 | `InheritCostCenterTag` | Inherit a tag from the resource group if missing | `ea3f2387-9b95-492a-a190-fcdc54f7b070` | modify |
| 3 Remediate | F5 | `DeployDiagKeyVault` | Enable logging by category group for Key vaults (microsoft.keyvault/vaults) to Log Analytics | `6b359d8f-f88d-4052-aa7c-32015963ecc1` | DeployIfNotExists |
| 3 Remediate | F5 | `DeployDiagAppService` | Enable logging by category group for App Service (microsoft.web/sites) to Log Analytics | `c0d8e23a-47be-4032-961f-8b0ff3957061` | DeployIfNotExists |
| 3 Remediate | F5 | `DeployDiagPostgres` | Enable logging by category group for PostgreSQL flexible server (microsoft.dbforpostgresql/flexibleservers) to Log Analytics | `cdd1dbc6-0004-4fcd-afd7-b67550de37ff` | DeployIfNotExists |
| 3 Remediate | F5 | `DeployDiagAppGateway` | Enable logging by category group for Application gateways (microsoft.network/applicationgateways) to Log Analytics | `92012204-a7e4-4a95-bbe5-90d0d3e12735` | DeployIfNotExists |
| 3 Remediate | F5 | `DeployDiagRedisEnterprise` | Enable logging by category group for Caches (microsoft.cache/redisenterprise/databases) to Log Analytics | `fa570aa1-acca-4eea-8e5a-233cf2c5e4c2` | DeployIfNotExists |

> [!NOTE]
> **Other built-in policies used directly**
>
> `Configure backup on virtual machines with a given tag to an existing recovery services vault in the same location` - `345fa903-145c-4fe1-8bcd-93ec2adccde8` (step 4.6)
>
> `Configure Azure Activity logs to stream to specified Log Analytics workspace` - `2465583e-4e78-4c15-b6be-a36cbc7c8b0f` (step 4.9)
>
> The reference landing zone's custom policy `alz-deny-vnet-peering` (Test 8).

---

[Runbook index](README.md) &middot; Previous: [Appendix A - Everything this runbook creates](appendix-a-everything-this-runbook-creates.md) &middot; Next: [Appendix C - Inherited policies: what to look for](appendix-c-inherited-policies.md)
