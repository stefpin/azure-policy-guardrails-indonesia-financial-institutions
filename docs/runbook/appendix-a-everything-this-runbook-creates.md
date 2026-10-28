# Appendix A - Everything this runbook creates

[Runbook index](README.md) &middot; Previous: [Part 6 - Troubleshooting](06-troubleshooting.md) &middot; Next: [Appendix B - Policy catalogue](appendix-b-policy-catalogue.md)

Use this list to see exactly what exists and how to remove it. Part 5 contains the commands. 'Level' refers to the clean-up levels in Part 5.

### Policy objects

| Type | Name | Created in | Removed in |
| --- | --- | --- | --- |
| Definition (custom) | `alz-pd-nsg-no-internet-mgmt`, `alz-pd-route-default-via-fw`, `alz-pd-appgw-https-listener`, `alz-pd-rg-required-tags`, `alz-pd-rg-allowed-locations` | 1.9 | Level 3 |
| Initiative | `alz-pd-c1-prevent` (10 rules), `alz-pd-c2-detect` (21), `alz-pd-c3-remediate` (7) | 1.10 | Level 3 |
| Assignment | `alz-pd-c1-lab` (lab, enforced), `alz-pd-c1-prod` (prod, DoNotEnforce), `alz-pd-c2-prod`, `alz-pd-c2-lab` (both with a system-assigned identity that has no role) | 2.2, 2.6, 3.2 | Level 3 (enforcement off in Level 1) |
| Assignment | `alz-pd-c3-prod` (prod, DoNotEnforce, identity), `alz-pd-c3-lab` (lab, enforced, identity), `alz-pd-c3-lab-vmbackup` (lab, identity) | 4.2, 4.6 | Level 3 |
| Assignment | `alz-pd-lab-nopeering` (lab, enforced), `alz-pd-rg-tags`, `alz-pd-rg-loc` (subscription, switched on for minutes), `alz-pd-sub-actlog` (optional) | 2.4, 4.9 | Level 3 (enforcement off in Level 1) |
| Exemption | `alz-pd-ex-appsvc-frontend`, `alz-pd-ex-appsvc-backend`, `alz-pd-ex-appgw-http`, `alz-pd-ex-pg-geobackup` | 4.7 | Level 3 |
| Remediation task | `alz-pd-rem-owner-tag`, `alz-pd-rem-DeployDiag...` (5), `alz-pd-rem-vm-backup` | 4.3, 4.4, 4.6 | Level 3 |
| Role assignment | Prod identity: Contributor on `rg-alz-corp-prod`, Log Analytics Contributor on `law-alz-central`. Lab identity: Contributor on the lab, Log Analytics Contributor on the workspace. Backup identity: Virtual Machine Contributor and Backup Contributor on the lab. | 4.2, 4.6 | Level 3 |

### Lab resources (all in rg-alz-policy-lab)

| Resource | Created in | Note |
| --- | --- | --- |
| `nsg-pd-lab`, `vnet-pd-lab` | 1.7 | Test network |
| `vm-pd-lab01` (+ NIC and disk) | 1.8 | Deliberately weak VM; Standard_B2ls_v2 |
| `nsg-pd-ok`, `pip-pd-lab`, `nic-pd-ok`, `rt-pd-lab`, `vnet-pd-peer-a`, `vnet-pd-peer-b`, `$ST_OK` | 2.4 | The 'safe' halves of the tests |
| `nsg-pd-notags` | 4.5 | Shows Modify beating Deny |
| Key Vault `$KV_OK` | 4.5 | Purge-protected: **IRREVERSIBLE**; soft-deleted for 7 days after deletion |
| Recovery Services vault `rsv-alz-pd-lab` | 4.6 | Deleted in step 5.3. Azure keeps a deleted vault (and the deleted backup data) for 14 days; it is not listed |
| Resource group `AzureBackupRG_indonesiacentral_1` | created by Azure Backup | Not in the lab; deleted in step 5.3 only if it is empty |

### Changes to existing production resources

| Change | Step | How to undo |
| --- | --- | --- |
| Application Gateway and PostgreSQL started | 1.4 | `az network application-gateway stop`, `az postgres flexible-server stop` (step 5.6) |
| `Owner` tag added to the production and lab resource groups (only where it was missing) | 1.3 | Level 4 |
| `Owner` tag added to the sample-application resources | 4.3 | Level 4 |
| Diagnostic setting `setByPolicy-LogAnalytics` on four resources (the gateway keeps its own `diag-agw-alz`) | 4.4 | Level 4 |
| Four exemptions on the two web apps, the gateway and the PostgreSQL server | 4.7 | Level 3 (step 5.4) |
| Role assignments for the policy identities (Contributor on the resource group, Log Analytics Contributor on the workspace) and the production assignments `alz-pd-c1-prod`, `alz-pd-c2-prod`, `alz-pd-c3-prod` | 2.6, 3.2, 4.2 | Level 3 |
| Provider `Microsoft.RecoveryServices` registered | 1.5 | Not needed; harmless |

Local files: the folder `alz-policy-demo` in your user folder (JSON files and the `evidence` subfolder). It stays on your PC on purpose, as your evidence; see the note at the end of step 5.7.

---

[Runbook index](README.md) &middot; Previous: [Part 6 - Troubleshooting](06-troubleshooting.md) &middot; Next: [Appendix B - Policy catalogue](appendix-b-policy-catalogue.md)
