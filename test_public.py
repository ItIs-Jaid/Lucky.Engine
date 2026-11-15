#!/usr/bin/env python3
"""Prove the publication gate works: clean on public/, loud on real leaks."""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import check_public  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        FAILS.append(name)


cat = json.load(open(os.path.join(BASE, "public", "catalog.json"), encoding="utf-8"))
names = [s["name"] for s in cat["skills"]]
check("catalog parses", len(names) >= 30, len(names))
check("catalog names unique", len(set(names)) == len(names))
bad = [n for n in names if not __import__("re").fullmatch(r"[a-z][a-z0-9-]{2,40}", n)]
check("all names match the naming contract", not bad, bad)
known = {s["id"] for s in cat["sources"]} | {"local"}
check("all sources known", all(s["source"] in known for s in cat["skills"]),
      {s["source"] for s in cat["skills"]} - known)

# clean path must be clean
findings, files = check_public.scan_path(os.path.join(BASE, "public"))
check(f"public/ is clean ({files} files)", not findings,
      findings[:3])

# publishable bundle (code + config + segments) must be 100% clean
bundle_targets = [
    "router.py", "gateway.py", "chainlib.py", "check_public.py",
    "chains.yaml", "test_router.py", "test_gateway.py", "test_public.py",
    "segments",
]
bundle_findings = []
for item in bundle_targets:
    target_path = os.path.join(BASE, item)
    f_list, _ = check_public.scan_path(target_path)
    bundle_findings.extend(f_list)
check(f"publishable bundle is clean ({len(bundle_targets)} targets)", not bundle_findings,
      bundle_findings[:3])

# in v1.6.0 unified public repo, the repo root itself must also be clean
root_findings, _ = check_public.scan_path(BASE)
check("repo root is clean (0 leaks)", len(root_findings) == 0, root_findings[:3])

# synthetic leaks, one per rule family
with tempfile.TemporaryDirectory() as td:
    cases = {
        "path.md": r"config at C:\\Users\\somebody\\app and /home/somebody/x",
        "mail.md": "contact somebody@realdomain.dev",
        "net.md": "peer 100.112.198.52 is up",
        "name.md": "name: olympia-hunt",
        "secret.md": "token sk-abcdefghijklmnop123456",
    }
    for fn, body in cases.items():
        open(os.path.join(td, fn), "w", encoding="utf-8").write(body + "\n")
    found, _ = check_public.scan_path(td)
    rules = {f["rule"] for f in found}
    for want in ("personal-path", "email", "tailnet-ip", "skill-name", "secret"):
        check(f"catches {want}", want in rules, sorted(rules))

# a filename alone is enough to fail
with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "teethgirl-shop.md"), "w", encoding="utf-8").write("clean body\n")
    found, _ = check_public.scan_path(td)
    check("catches identifier in filename", any("[name]" in f["file"] for f in found), found)

# example.com is allowed so docs can show a safe pattern
with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "ok.md"), "w", encoding="utf-8").write("mail you@example.com\n")
    found, _ = check_public.scan_path(td)
    check("example.com allowlisted", not found, found)

print()
if FAILS:
    print(f"FAILED {len(FAILS)}: {FAILS}")
    sys.exit(1)
print("ALL PUBLICATION GATES PASSED")
