# Appendix C - Inherited policies: what to look for

[Runbook index](README.md) &middot; Previous: [Appendix B - Policy catalogue](appendix-b-policy-catalogue.md) &middot; Next: [Appendix D - Glossary](appendix-d-glossary.md)

Policies assigned above your subscription - at a management group or at the Tenant Root Group, if your tenant has any - apply to everything you create. You did not create them and this runbook does not change them. They can explain a 'surprise'. This table lists the **kinds** of inherited policy that can change the result of a test, and what this runbook does about each one. Step 1.6 shows you how to find the ones in your own tenant.

| Kind of inherited policy | What it can contain | Why it matters here |
| --- | --- | --- |
| **Modify** or **DeployIfNotExists**: hardening | Settings changed on new resources (for example storage account access settings) and diagnostic settings created for many service types | A resource can be changed before a Deny rule is evaluated. This is why Test 4 uses HTTPS-only. A diagnostic setting created by an inherited policy can also pre-empt the settings that Chapter 3 deploys. |
| **Audit**: a security benchmark | For example the Microsoft cloud security benchmark initiative, and other audit rules | Adds findings to the compliance screens that are not yours. It may already report, for example, Key Vault purge protection and encryption at host. Filter by `alz-pd`. |
| **Deny**: regions or resource types | Blocks some regions, VM sizes or resource types | The 'wrong region' test uses East US; pick another unapproved region if yours is blocked. Use small B-series VMs in the lab. |

---

[Runbook index](README.md) &middot; Previous: [Appendix B - Policy catalogue](appendix-b-policy-catalogue.md) &middot; Next: [Appendix D - Glossary](appendix-d-glossary.md)
