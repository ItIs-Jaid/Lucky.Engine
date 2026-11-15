#!/usr/bin/env python3
"""Generate per-task verifier scripts for the evaluation-harness benchmark.

Reads benchmark/task_specs.json and writes one verifier script per task into
benchmark/verifiers/. Each verifier reads inputs/<tid>.json, executes the
task's solution function, and compares output to expected/<tid>.json.

Run from the repo root:  python scripts/gen_verifiers.py
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(BASE, "..", "benchmark")
OUT = os.path.join(BENCH, "verifiers")
SPECS = os.path.join(BENCH, "task_specs.json")

TEMPLATE = '''import json, sys

tid = "__TID__"
inp = json.load(open("inputs/__TID__.json"))
ns = {}
exec(FN, ns)
solution = ns["f"]
__IO__
expected = json.loads(open("expected/__TID__.json").read().strip())
try:
    got = solution(__CALL__)
    if __CHECK__:
        print("PASS")
        sys.exit(0)
    print("FAIL: expected " + repr(expected) + " got " + repr(got))
    sys.exit(1)
except Exception as e:
    print("FAIL: " + type(e).__name__ + ": " + str(e))
    sys.exit(1)
'''

def main():
    with open(SPECS) as fh:
        TASKS = json.load(fh)
    os.makedirs(OUT, exist_ok=True)
    for t in TASKS:
        src = (TEMPLATE
               .replace("__TID__", t["tid"])
               .replace("FN", t["func"])
               .replace("__IO__", t["io"])
               .replace("__CALL__", t["call"])
               .replace("__CHECK__", t["check"]))
        with open(os.path.join(OUT, t["tid"] + ".py"), "w") as fh:
            fh.write(src)
        print("wrote", t["tid"])

if __name__ == "__main__":
    main()
