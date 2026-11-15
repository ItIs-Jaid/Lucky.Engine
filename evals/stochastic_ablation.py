#!/usr/bin/env python3
"""Controlled stochastic trial-and-error ablation for Lucky.Engine v1.6.0.

Compares 4 execution policies over the 12-task benchmark workload:
  1. always_heavy   — always sends full 240-tok frontier/heavy context
  2. random_arm     — uniform random arm selection (1 attempt)
  3. ucb1_bandit    — UCB1 cost-aware trial-and-error (up to 2 attempts)
  4. thompson_bandit — Beta Thompson Sampling trial-and-error (up to 2 attempts)

Pure Python stdlib, deterministic seed, zero network/API cost.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import bandit  # noqa: E402
import router  # noqa: E402

META = json.load(open(os.path.join(BASE, "benchmark", "meta.json"), encoding="utf-8"))

# Simulated capability thresholds by task category (models real SLM vs heuristic success profiles)
CATEGORY_MIN_TIER = {
    "loop": 0,       # heuristic_fast suffices
    "string": 0,
    "math": 0,
    "array": 1,      # slm_compact suffices
    "dict": 1,
    "sort": 1,
    "search": 1,
    "tree": 2,       # needs slm_ppr
    "graph": 2,
    "dp": 2,
    "recursion": 2,
    "number": 0,
}


def make_executor(category: str):
    min_tier = CATEGORY_MIN_TIER.get(category, 1)
    def _exec(arm: dict):
        passed = arm["tier"] >= min_tier
        return passed, arm["est_tokens"]
    return _exec


def eval_policy(name: str, rounds: int = 10, seed: int = 42):
    rng = random.Random(seed)
    b = None
    if name == "ucb1_bandit":
        b = bandit.StochasticBandit(policy="ucb1", seed=seed)
    elif name == "thompson_bandit":
        b = bandit.StochasticBandit(policy="thompson", seed=seed)

    total_tasks = 0
    total_passes = 0
    total_tokens = 0
    t0 = time.perf_counter()

    for _ in range(rounds):
        for t in META["tasks"]:
            total_tasks += 1
            cat = t.get("category", "array")
            res = router.resolve(t["prompt"])
            ctx = f"{res['chain']}:{cat}"
            exec_fn = make_executor(cat)

            if name == "always_heavy":
                arm = bandit.DEFAULT_ARMS[-1]
                ok, tok = exec_fn(arm)
                total_passes += int(ok)
                total_tokens += tok
            elif name == "random_arm":
                arm = rng.choice(bandit.DEFAULT_ARMS)
                ok, tok = exec_fn(arm)
                total_passes += int(ok)
                total_tokens += tok
            else:
                out = bandit.run_trial_and_error(b, ctx, exec_fn, max_attempts=2)
                total_passes += int(out["passed"])
                total_tokens += out["total_tokens_est"]

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "policy": name,
        "tasks": total_tasks,
        "pass_rate": round(total_passes / total_tasks, 4),
        "avg_tokens_est": round(total_tokens / total_tasks, 2),
        "total_tokens_est": total_tokens,
        "elapsed_ms": round(dt_ms, 2),
    }


def main():
    print("Lucky.Engine Stochastic Trial-and-Error Ablation (12 tasks x 10 rounds = 120 runs)")
    print("=" * 78)
    rows = [eval_policy(p) for p in ("always_heavy", "random_arm", "ucb1_bandit", "thompson_bandit")]
    print(f"{'Policy':<18} {'PassRate':>10} {'AvgTokEst':>12} {'TotalTokEst':>13} {'Time(ms)':>10}")
    print("-" * 78)
    for r in rows:
        print(f"{r['policy']:<18} {r['pass_rate']:>10.4f} {r['avg_tokens_est']:>12.2f} "
              f"{r['total_tokens_est']:>13d} {r['elapsed_ms']:>10.2f}")


if __name__ == "__main__":
    main()
