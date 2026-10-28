#!/usr/bin/env python3
"""Repository checks. Run from anywhere:  python tools/validate_repo.py

Checks
  1. every JSON file parses
  2. the three initiatives hold 10 / 21 / 7 = 38 rules and agree with policies/catalog.json
  3. every initiative reference points at a built-in GUID from the catalogue or at a custom definition in this repo
  4. every group name used by an initiative exists in groups.json
  5. the JSON that the runbook pages write with PowerShell here-strings equals the JSON in policies/
  6. every relative link and image in the Markdown files resolves
  7. scripts/ is up to date with docs/runbook/ (tools/extract_scripts.py --check)
  8. hygiene: no unexpected GUIDs, e-mail addresses, user-profile paths, private keys or public IP addresses
"""
import glob
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def err(msg):
    errors.append(msg)


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def load(path):
    try:
        with io.open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        err("%s: not valid JSON (%s)" % (rel(path), exc))
        return None


GUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")

# ------------------------------------------------------------------ 1. JSON
json_files = [p for p in glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True) if "/.git/" not in p.replace("\\", "/")]
for p in json_files:
    load(p)

# ------------------------------------------------------------------ 2-4. initiatives
catalog = load(os.path.join(ROOT, "policies", "catalog.json")) or []
groups = load(os.path.join(ROOT, "policies", "initiatives", "groups.json")) or []
group_names = {g["name"] for g in groups}
chapters = {"alz-pd-c1-prevent": ("1 Prevent", 10), "alz-pd-c2-detect": ("2 Detect", 21), "alz-pd-c3-remediate": ("3 Remediate", 7)}
definitions_dir = os.path.join(ROOT, "policies", "definitions")
custom = {os.path.basename(p)[: -len(".rules.json")] for p in glob.glob(os.path.join(definitions_dir, "*.rules.json"))}
catalog_ids = {c["id"] for c in catalog}

if len(custom) != 5:
    err("expected 5 custom definitions, found %d" % len(custom))
for name in sorted(custom):
    rules = load(os.path.join(definitions_dir, name + ".rules.json"))
    params = load(os.path.join(definitions_dir, name + ".parameters.json"))
    if rules is not None and not ({"if", "then"} <= set(rules)):
        err("%s.rules.json needs 'if' and 'then'" % name)
    if params is not None and "effect" not in params:
        err("%s.parameters.json needs an 'effect' parameter" % name)

total = 0
for init, (chapter, want) in chapters.items():
    defs = load(os.path.join(ROOT, "policies", "initiatives", init + ".definitions.json")) or []
    load(os.path.join(ROOT, "policies", "initiatives", init + ".parameters.json"))
    total += len(defs)
    if len(defs) != want:
        err("%s: expected %d rules, found %d" % (init, want, len(defs)))
    refs = [d.get("policyDefinitionReferenceId") for d in defs]
    if len(set(refs)) != len(refs):
        err("%s: duplicate policyDefinitionReferenceId" % init)
    expected_refs = [c["ref"] for c in catalog if c["chapter"] == chapter]
    if refs != expected_refs:
        err("%s: references differ from policies/catalog.json" % init)
    for d in defs:
        pid = d.get("policyDefinitionId", "")
        tail = pid.rsplit("/", 1)[-1]
        if GUID.fullmatch(tail):
            if tail not in catalog_ids:
                err("%s: built-in %s is not in policies/catalog.json" % (init, tail))
        elif tail not in custom:
            err("%s: custom definition %s has no file in policies/definitions/" % (init, tail))
        for g in d.get("groupNames", []):
            if g not in group_names:
                err("%s: unknown group %s" % (init, g))
if total != 38:
    err("expected 38 rules in total, found %d" % total)
if len(catalog) != 38:
    err("policies/catalog.json should list 38 rules, found %d" % len(catalog))

# ------------------------------------------------------------------ 5. here-string parity
HERE = re.compile(r"@'\n(.*?)\n'@ \| Set-Content \"\$WORK/([\w.-]+\.json)\"", re.S)
CUSTOM = {"d1-nsg": "alz-pd-nsg-no-internet-mgmt", "d2-route": "alz-pd-route-default-via-fw", "d3-appgw": "alz-pd-appgw-https-listener",
          "d4-rgtags": "alz-pd-rg-required-tags", "d5-rgloc": "alz-pd-rg-allowed-locations"}
INITS = {"c1": "alz-pd-c1-prevent", "c2": "alz-pd-c2-detect", "c3": "alz-pd-c3-remediate"}


def target_for(fname):
    stem = fname[:-5]
    m = re.fullmatch(r"(d\d-[a-z]+)-(rule|params)", stem)
    if m:
        suffix = "rules" if m.group(2) == "rule" else "parameters"
        return os.path.join("policies", "definitions", "%s.%s.json" % (CUSTOM[m.group(1)], suffix))
    m = re.fullmatch(r"(c\d)-params", stem)
    if m:
        return os.path.join("policies", "initiatives", INITS[m.group(1)] + ".parameters.json")
    if stem == "groups":
        return os.path.join("policies", "initiatives", "groups.json")
    if stem == "c1-messages":
        return os.path.join("policies", "initiatives", "alz-pd-c1-prevent.non-compliance-messages.json")
    return None


seen = 0
for page in sorted(glob.glob(os.path.join(ROOT, "docs", "runbook", "*.md"))):
    text = io.open(page, encoding="utf-8").read()
    for body, fname in HERE.findall(text):
        target = target_for(fname)
        if target is None:
            continue
        seen += 1
        try:
            doc_json = json.loads(body)
        except Exception as exc:  # noqa: BLE001
            err("%s: here-string for %s is not valid JSON (%s)" % (rel(page), fname, exc))
            continue
        repo_json = load(os.path.join(ROOT, target))
        if repo_json != doc_json:
            err("%s differs from the here-string for %s in %s" % (target.replace("\\", "/"), fname, rel(page)))
if seen < 15:
    err("expected at least 15 JSON here-strings in the runbook pages, found %d" % seen)

# ------------------------------------------------------------------ 6. markdown links
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
for md in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
    if "/.git/" in md.replace("\\", "/"):
        continue
    text = io.open(md, encoding="utf-8").read()
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for target in LINK.findall(text):
        if re.match(r"^(https?:|mailto:|#)", target):
            continue
        path = target.split("#", 1)[0]
        if not path:
            continue
        full = os.path.normpath(os.path.join(os.path.dirname(md), path))
        if not os.path.exists(full):
            err("%s: broken link %s" % (rel(md), target))

# ------------------------------------------------------------------ 7. scripts in sync
res = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "extract_scripts.py"), "--check"], capture_output=True, text=True)
if res.returncode != 0:
    err((res.stdout + res.stderr).strip() or "scripts are out of date")

# ------------------------------------------------------------------ 8. hygiene
allowed_guids = {g.lower() for g in catalog_ids} | {"345fa903-145c-4fe1-8bcd-93ec2adccde8", "2465583e-4e78-4c15-b6be-a36cbc7c8b0f"}
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
OK_IP = re.compile(r"^(0\.0\.0\.0|1\.0\.0\.0|10\..*|127\..*|192\.168\..*|172\.(1[6-9]|2\d|3[01])\..*|255\..*)$")
text_ext = {".md", ".json", ".ps1", ".py", ".yml", ".yaml", ".txt", ".drawio", ".gitignore", ".gitattributes"}
for path in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True):
    if os.path.isdir(path) or "/.git/" in path.replace("\\", "/"):
        continue
    if os.path.splitext(path)[1].lower() not in text_ext and os.path.basename(path) not in ("LICENSE", ".gitignore", ".gitattributes"):
        continue
    if rel(path) == "tools/validate_repo.py":
        continue
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    for g in set(GUID.findall(text)):
        if g.lower() not in allowed_guids:
            err("%s: unexpected GUID %s (only built-in policy IDs from policies/catalog.json are allowed)" % (rel(path), g))
    for e in set(EMAIL.findall(text)):
        if not e.endswith("@users.noreply.github.com"):
            err("%s: e-mail address %s" % (rel(path), e))
    if re.search(r"[A-Za-z]:\\Users\\(?!<)", text):
        err("%s: contains a user-profile path" % rel(path))
    if "-----BEGIN" in text:
        err("%s: contains a key block" % rel(path))
    for ip in set(IPV4.findall(text)):
        if not OK_IP.match(ip):
            err("%s: public-looking IP address %s" % (rel(path), ip))

# ------------------------------------------------------------------ result
if errors:
    print("FAILED - %d problem(s):" % len(errors))
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("OK - %d JSON files, 38 rules (10/21/7), %d here-strings match, links resolve, scripts in sync, hygiene clean" % (len(json_files), seen))
