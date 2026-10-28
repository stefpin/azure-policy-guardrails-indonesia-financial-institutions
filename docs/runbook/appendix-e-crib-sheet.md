# Appendix E - One-page crib sheet

[Runbook index](README.md) &middot; Previous: [Appendix D - Glossary](appendix-d-glossary.md) &middot; Next: [Appendix F - What was verified, and how](appendix-f-what-was-verified.md)

A one-page summary of the demonstration. Each row is one thing you say and show. All commands are in the parts named in the last column.

| # | Show | Command or page | Expect | Part |
| --- | --- | --- | --- | --- |
| 1 | The app is healthy | `Test-SampleApp` | 200 and 403 (from an allowed client); backend Healthy | 1.4 |
| 2 | Safety switch | Create untagged NSG while DoNotEnforce | Succeeds | 2.2 |
| 3 | Region | NSG in `eastus` | Denied | 2.4 |
| 4 | Public IP on NIC | `az network nic create ... --public-ip-address` | Denied | 2.4 |
| 5 | RDP from Internet | `az network nsg rule create ... Internet ... 3389` | Denied | 2.4 |
| 6 | HTTP storage | `az storage account create --https-only false` | Denied | 2.4 |
| 7 | Key Vault without purge protection | `az keyvault create` (no purge protection) | Denied | 2.4 |
| 8 | Default route to Internet | `az network route-table route create ... Internet` | Denied | 2.4 |
| 9 | No tags / VNet peering / resource group | Tests 7, 8, 9 | Denied | 2.4 |
| 10 | Impact on production (what-if) | `Show-Compliance -RG $RG_CORP -Assignment alz-pd-c1-prod` | About 27 rows | 2.6 |
| 11 | The findings list | `Show-Compliance -RG $RG_CORP -Assignment alz-pd-c2-prod` | About 11 rows | 3.4 |
| 12 | Prove a finding | The 7-line block | Values match | 3.5 |
| 13 | Fix the Owner tag | `az policy remediation create ... InheritOwnerTag` | 26 resources tagged | 4.3 |
| 14 | Fix diagnostics | 5 remediation tasks, then the KQL query | Rows in the workspace | 4.4 |
| 15 | Modify beats Deny | Untagged NSG now succeeds with tags | Tags added | 4.5 |
| 16 | Back up the VM by tag | Vault, assignment, remediation | Backup item exists | 4.6 |
| 17 | Record exceptions | 4 `az policy exemption create` | Exempt state | 4.7 |
| 18 | Scorecard and the app | `Show-Scorecard`, `Test-SampleApp` | Everything fixable is green; what remains is the gateway diagnostics (4.4), four engineering decisions and four exemptions (4.7); 403 and Healthy (200 from an allowed client) | 4.8 |
| 19 | Reset | Level 1 of Part 5 | Nothing enforcing | 5.2 |

---

[Runbook index](README.md) &middot; Previous: [Appendix D - Glossary](appendix-d-glossary.md) &middot; Next: [Appendix F - What was verified, and how](appendix-f-what-was-verified.md)
