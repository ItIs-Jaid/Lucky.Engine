#!/usr/bin/env python3
"""AXIS 1 — Lucky.Engine routing-accuracy eval.

Deterministic: for each eval task with a ground-truth chain, run the router and
compare predicted chain vs expected. Produces precision / recall / f1 + confidence
coverage. No LLM involved.

Usage:  python evals/routing.py
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
import router  # noqa: E402
from chainlib import load_chains  # noqa: E402

EVAL = [
    # id, task, expected_chain
    ("t001", "research the latest AI agent frameworks and write a cited survey report", "research-synthesis"),
    ("t002", "fix the failing tests in the repo and add a regression test", "delegated-build"),
    ("t003", "find and verify 5 rental listings for a cross-state relocation move", "move-and-relocate"),
    ("t004", "audit the skill pool for duplicates and create a new skill", "skill-forging"),
    ("t005", "review my homelab for security gaps and write a posture report", "security-review"),
    ("t006", "plan my day and pick a next action", "fallback"),
    ("t007", "measure a utility transfer plan for a relocation move with costs", "move-and-relocate"),
    ("t008", "write a competitor analysis with citations and sources", "research-synthesis"),
    ("t009", "implement a feature: add retry with backoff to the gateway", "delegated-build"),
    ("t010", "harden the firewall, monitor for threats, write a report", "security-review"),
    ("t011", "audit skills, test a route, and ship the skill", "skill-forging"),
    ("t012", "what is the weather today?", "fallback"),
    ("t013", "how do I relocate my family to the pacific northwest", "move-and-relocate"),
    ("t014", "debug the production outage on the critical path now", "delegated-build"),
]

def main():
    chains, _defaults = load_chains(os.path.join(BASE, "chains.yaml"))
    by_id = {c["id"]: c for c in chains}
    print("Lucky.Engine 1.6.0 routing eval")
    print("=" * 60)
    correct = 0
    results = []
    for tid, task, expected in EVAL:
        res = router.resolve(task)
        pred = res["chain"]
        ok = pred == expected
        correct += ok
        results.append({"tid": tid, "task": task, "expected": expected, "predicted": pred,
                        "matched": res["matched"], "confidence": round(res["confidence"], 3),
                        "score": res["score"], "ok": ok})
        print(f"{tid} expected={expected:<20} predicted={pred:<20} {'OK' if ok else 'MISMATCH'} conf={res['confidence']}")

    n = len(EVAL)
    acc = correct / n
    print("=" * 60)
    print(f"accuracy={acc:.2f}  ({correct}/{n})")

    # per-chain precision/recall
    from collections import Counter, defaultdict
    gt_by_chain = Counter(c[2] for c in EVAL)
    pred_by_chain = Counter(r["predicted"] for r in results)
    print("\nGround-truth chain counts:", dict(gt_by_chain))
    print("Predictions by chain:   ", dict(pred_by_chain))

    # precision/recall/f1 for the non-fallback chains
    print("\nPer-chain precision/recall (vs ground truth):")
    for c in ["research-synthesis", "delegated-build", "move-and-relocate",
              "skill-forging", "security-review"]:
        gt = gt_by_chain.get(c, 0)
        pred_c = sum(1 for r in results if r["predicted"] == c)
        correct_c = sum(1 for r in results if r["predicted"] == c and r["expected"] == c)
        p = correct_c / pred_c if pred_c else 0
        r_ = correct_c / gt if gt else 0
        f1 = 2 * p * r_ / (p + r_) if (p + r_) else 0
        print(f"  {c:<20} P={p:.2f} R={r_:.2f} F1={f1:.2f} (gt={gt}, pred={pred_c})")

    # confidence coverage
    low_conf = sum(1 for r in results if r["confidence"] < 0.7)
    print(f"\nlow-confidence predictions (<0.7): {low_conf}/{n}")
    return results

if __name__ == "__main__":
    main()
