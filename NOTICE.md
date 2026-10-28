# Notices

## Not an official product

This repository is an independent teaching resource and reference implementation. It is **not an official Microsoft
publication**, it is not supported or endorsed by Microsoft, by any regulator or by any other company named in it, and
it comes with no warranty (see [LICENSE](LICENSE)). Use it at your own risk: read every command before you run it, and
start in a subscription you can afford to experiment in.

## Not legal or regulatory advice

The regulatory themes in [`docs/regulatory-themes.md`](docs/regulatory-themes.md) and in Part 0 of the runbook are a
technical aid for designing guardrails. They are **not** legal advice, do not restate any regulation, and are not a
statement of what any regulator requires of you. Azure Policy checks the configuration of Azure resources; it does not
establish regulatory compliance. Confirm the obligations that apply to your institution with your compliance and legal
teams.

## Trademarks

Microsoft, Azure, Azure Policy, Azure Firewall, Azure Application Gateway, Azure Key Vault, Azure Backup, Azure Monitor,
Azure Cloud Shell, Microsoft Defender for Cloud and PowerShell are trademarks of the Microsoft group of companies. All
other product and organisation names (including the regulators named for context, OJK and Bank Indonesia) are
trademarks or names of their respective owners. They are used only to identify the products and bodies the material
discusses; no affiliation is implied.

## Azure Policy built-in definitions

The runbook refers to Microsoft's built-in Azure Policy definitions by their public IDs (listed in
[`policies/catalog.json`](policies/catalog.json)). The definitions themselves are not copied here; they belong to
Microsoft and change over time, so the catalogue records the version each ID was checked against.

## Diagram icons

The architecture and policy-scope diagrams (`diagrams/azure-policy-demo-*.drawio` and their PNG exports) use Microsoft
Azure architecture icons from the draw.io shape library. Microsoft's terms for the use of Azure icons in architecture
diagrams apply to those icons. The three figures in `diagrams/what-you-will-build.png`,
`diagrams/policy-effect-flow.png` and `diagrams/expected-findings.png` are drawn with plain shapes.

## Foundation

The runbook builds on [`stefpin/azure-landing-zone`](https://github.com/stefpin/azure-landing-zone), a separate,
MIT-licensed repository. Nothing from it is copied here.
