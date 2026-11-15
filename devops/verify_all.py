#!/usr/bin/env python3
"""Unified DevOps verification gate for Lucky.Engine v1.6.0 (stdlib-only)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = [
    ("Layer 2: test_router.py", [sys.executable, "test_router.py"], ROOT),
    ("Layer 2: test_gateway.py", [sys.executable, "test_gateway.py"], ROOT),
    ("Bandit: test_bandit.py", [sys.executable, "test_bandit.py"], ROOT),
    ("Layer 1: bridge/test_suite.py", [sys.executable, "test_suite.py"], ROOT / "bridge"),
    ("Layer 1: bridge unittest", [sys.executable, "-m", "unittest", "discover", "-s", "tests"], ROOT / "bridge"),
    ("Layer 1: bridge/eval/runner.py", [sys.executable, "eval/runner.py"], ROOT / "bridge"),
    ("Eval: evals/routing.py", [sys.executable, "evals/routing.py"], ROOT),
    ("Eval: evals/stochastic_ablation.py", [sys.executable, "evals/stochastic_ablation.py"], ROOT),
    ("Eval: harness axis1", [sys.executable, "harness/run_experiment.py", "--axis1"], ROOT),
    ("Eval: harness axis2 local", [sys.executable, "harness/run_experiment.py", "--axis2", "local"], ROOT),
    ("Public Gate: public/", [sys.executable, "check_public.py", "--path", "public/"], ROOT),
    ("Public Gate: public_bench/", [sys.executable, "check_public.py", "--path", "public_bench/"], ROOT),
]


def _clean_runtime_artifacts() -> None:
    for rel in ("bridge/.lucky_cache.json", "bridge/lucky-audit.md"):
        p = ROOT / rel
        if p.exists():
            p.unlink()


def main() -> int:
    failed = 0
    for name, cmd, cwd in CHECKS:
        print(f"\n=== {name} ===")
        proc = subprocess.run(cmd, cwd=cwd)
        if proc.returncode != 0:
            print(f"FAILED: {name} (exit {proc.returncode})")
            failed += 1
        else:
            print(f"PASSED: {name}")

    _clean_runtime_artifacts()

    for name, cmd, cwd in (
        ("Layer 2: test_public.py", [sys.executable, "test_public.py"], ROOT),
        ("Public Gate: full repo", [sys.executable, "check_public.py", "--path", "."], ROOT),
    ):
        print(f"\n=== {name} ===")
        proc = subprocess.run(cmd, cwd=cwd)
        if proc.returncode != 0:
            print(f"FAILED: {name} (exit {proc.returncode})")
            failed += 1
        else:
            print(f"PASSED: {name}")

    total = len(CHECKS) + 2
    print(f"\nSummary: {total - failed}/{total} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
