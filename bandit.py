#!/usr/bin/env python3
"""bandit.py — Pure-stdlib Stochastic Trial-and-Error Bandit for Lucky.Engine.

Grounds adaptive low-compute agent execution in:
  - RouteLLM / MasRouter: cost-aware dynamic routing across capability tiers
  - Green AI (Schwartz et al., 2020) & Small Language Models for Agentic AI (Belcak et al., 2025)
  - Reflexion (Shinn et al., 2023): verifier-gated trial-and-error feedback

Zero third-party dependencies. Runs on any CPU.
"""
from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional, Tuple

DEFAULT_ARMS = (
    {"id": "heuristic_fast", "est_tokens": 0, "tier": 0},
    {"id": "slm_compact", "est_tokens": 60, "tier": 1},
    {"id": "slm_ppr", "est_tokens": 120, "tier": 2},
    {"id": "escalate_hitl", "est_tokens": 240, "tier": 3},
)


@dataclass
class ArmStats:
    pulls: int = 0
    successes: float = 0.0
    failures: float = 0.0
    reward_sum: float = 0.0
    total_tokens_est: int = 0

    def mean_reward(self) -> float:
        return self.reward_sum / self.pulls if self.pulls > 0 else 0.0


def compute_reward(passed: bool, tokens_est: int, budget: int = 240, cost_weight: float = 0.35) -> float:
    """Cost-aware verifier reward: passes with fewer estimated tokens score higher."""
    if not passed:
        return 0.0
    norm_cost = min(1.0, max(0.0, float(tokens_est) / max(1, int(budget))))
    return round(max(0.05, 1.0 - cost_weight * norm_cost), 6)


class StochasticBandit:
    """Contextual UCB1 / Thompson-Sampling bandit keyed by (chain, urgency)."""

    def __init__(
        self,
        arms: Optional[List[dict]] = None,
        state_path: Optional[str] = None,
        policy: str = "ucb1",
        exploration_c: float = 1.2,
        seed: Optional[int] = None,
    ):
        self.arms = list(arms or DEFAULT_ARMS)
        self.arm_ids = [a["id"] for a in self.arms]
        self.state_path = state_path
        self.policy = policy
        self.exploration_c = exploration_c
        self.rng = random.Random(seed)
        self.buckets: Dict[str, Dict[str, ArmStats]] = {}
        if state_path and os.path.exists(state_path):
            self.load(state_path)

    def _bucket(self, context_key: str) -> Dict[str, ArmStats]:
        if context_key not in self.buckets:
            self.buckets[context_key] = {aid: ArmStats() for aid in self.arm_ids}
        else:
            for aid in self.arm_ids:
                self.buckets[context_key].setdefault(aid, ArmStats())
        return self.buckets[context_key]

    def select_arm(self, context_key: str, exclude: Optional[set] = None) -> dict:
        bucket = self._bucket(context_key)
        candidates = [a for a in self.arms if not exclude or a["id"] not in exclude]
        if not candidates:
            candidates = list(self.arms)

        # Cold-start: explore untried arms in ascending compute cost order
        for arm in candidates:
            if bucket[arm["id"]].pulls == 0:
                return arm

        total_pulls = sum(bucket[a["id"]].pulls for a in candidates)
        if self.policy == "thompson":
            best_arm, best_val = candidates[0], -1.0
            for arm in candidates:
                st = bucket[arm["id"]]
                sample = self.rng.betavariate(1.0 + st.successes, 1.0 + st.failures)
                # Slight cost-tiebreak using average observed reward
                score = 0.7 * sample + 0.3 * st.mean_reward()
                if score > best_val:
                    best_val = score
                    best_arm = arm
            return best_arm

        # Default: UCB1
        best_arm, best_ucb = candidates[0], -1.0
        log_n = math.log(max(1, total_pulls))
        for arm in candidates:
            st = bucket[arm["id"]]
            bonus = self.exploration_c * math.sqrt(log_n / st.pulls)
            ucb = st.mean_reward() + bonus
            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm
        return best_arm

    def update(self, context_key: str, arm_id: str, passed: bool, tokens_est: int, budget: int = 240) -> float:
        bucket = self._bucket(context_key)
        st = bucket[arm_id]
        reward = compute_reward(passed, tokens_est, budget=budget)
        st.pulls += 1
        if passed:
            st.successes += 1.0
        else:
            st.failures += 1.0
        st.reward_sum += reward
        st.total_tokens_est += int(tokens_est)
        if self.state_path:
            self.save(self.state_path)
        return reward

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        payload = {
            ctx: {aid: asdict(st) for aid, st in arms.items()}
            for ctx, arms in self.buckets.items()
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

    def load(self, path: str) -> None:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.buckets = {}
        for ctx, arms in (raw or {}).items():
            self.buckets[ctx] = {aid: ArmStats(**vals) for aid, vals in arms.items()}


def run_trial_and_error(
    bandit: StochasticBandit,
    context_key: str,
    executor: Callable[[dict], Tuple[bool, int]],
    max_attempts: int = 3,
    budget: int = 240,
) -> dict:
    """Stochastic trial-and-error loop gated by a deterministic verifier callback.

    `executor(arm)` returns `(passed: bool, tokens_est: int)`.
    Retries untried/higher-ranked arms on failure up to `max_attempts`.
    """
    tried = set()
    attempts = []
    total_tokens = 0
    for idx in range(max(1, max_attempts)):
        arm = bandit.select_arm(context_key, exclude=tried)
        tried.add(arm["id"])
        passed, tokens_est = executor(arm)
        total_tokens += int(tokens_est)
        reward = bandit.update(context_key, arm["id"], passed, tokens_est, budget=budget)
        attempts.append({
            "attempt": idx + 1,
            "arm": arm["id"],
            "passed": bool(passed),
            "tokens_est": int(tokens_est),
            "reward": reward,
        })
        if passed:
            return {
                "passed": True,
                "winning_arm": arm["id"],
                "attempts": attempts,
                "total_tokens_est": total_tokens,
            }
    return {
        "passed": False,
        "winning_arm": None,
        "attempts": attempts,
        "total_tokens_est": total_tokens,
    }
