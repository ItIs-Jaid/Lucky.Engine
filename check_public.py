#!/usr/bin/env python3
"""Publication gate: find operator identifiers in names and text. Stdlib only.

Exit 0 = clean, 1 = findings. A finding is a hard fail, not a warning.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SKIP_FILES = {"check_public.py", "test_public.py"}
SKIP_DIRS = {".git", "__pycache__", ".lucky", "node_modules", ".venv"}
TEXT_EXT = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".csv", ""}

RULES = [
    ("personal-path", r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9_.-]+", "absolute Windows user path"),
    ("personal-path", r"/c/Users/[A-Za-z0-9_.-]+", "absolute Windows user path (msys)"),
    ("personal-path", r"/home/[A-Za-z0-9_.-]+/", "absolute POSIX home path"),
    ("email", r"\b[\w.+-]+@(?!example\.com)[\w-]+\.[A-Za-z]{2,}\b", "email address"),
    ("tailnet-ip", r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b",
     "tailnet address"),
    ("handle", r"\b(?:jaide|jaidedking|itis-jaid|teethgirl\w*|luckykat\w*)\b", "personal handle"),
    ("workspace", r"Hemes\s+Home", "private workspace name"),
    ("codename", r"\b(?:RAINCLOUD|SkillClaw|identity-guard-core|guard-dog)\b", "private codename"),
    ("location", r"\b(?:Safford|Olympia|Graham\s+County|Seattle)\b", "personal location"),
    ("employer", r"\bWalmart\b", "named employer"),
    ("dob", r"\b12/13/2000\b", "date of birth"),
    ("phone", r"\b\d{3}[-.]\d{3}[-.]\d{4}\b", "phone number"),
    ("secret", r"\b(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b",
     "credential-shaped string"),
    ("skill-name", r"^\s*(?:name:\s*)?(?:[a-z0-9-]*)(?:olympia|seattle|walmart|jaide|teethgirl)"
                   r"[a-z0-9-]*\s*$", "skill name carrying a personal identifier"),
]
COMPILED = [(rid, re.compile(rx, re.IGNORECASE | re.MULTILINE), why) for rid, rx, why in RULES]


def scan_text(text: str, rel: str):
    out = []
    for rid, rx, why in COMPILED:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            out.append({"rule": rid, "why": why, "file": rel, "line": line,
                        "match": m.group(0)[:80]})
    return out


def scan_path(path: str):
    findings = []
    files = 0
    targets = [path] if os.path.isfile(path) else None
    if targets is None:
        targets = []
        for root, dirs, names in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for n in names:
                targets.append(os.path.join(root, n))
    for fp in targets:
        if os.path.basename(fp) in SKIP_FILES:
            continue
        if os.path.splitext(fp)[1].lower() not in TEXT_EXT:
            continue
        rel = os.path.relpath(fp, path if os.path.isdir(path) else os.path.dirname(path))
        # the file NAME is part of the leak surface too
        findings += scan_text(os.path.basename(fp), rel + " [name]")
        try:
            text = open(fp, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        files += 1
        findings += scan_text(text, rel)
    return findings, files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="publication leak gate")
    ap.add_argument("--path", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max", type=int, default=40)
    a = ap.parse_args(argv)
    findings, files = scan_path(a.path)
    if a.json:
        print(json.dumps({"files": files, "findings": findings, "clean": not findings}, indent=2))
    else:
        print(f"scanned {files} files under {a.path}")
        for f in findings[: a.max]:
            print(f"  {f['rule']:<13} {f['file']}:{f['line']}  {f['match']!r}  ({f['why']})")
        if len(findings) > a.max:
            print(f"  ... {len(findings) - a.max} more")
        print("CLEAN" if not findings else f"{len(findings)} FINDINGS")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
