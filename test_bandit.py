#!/usr/bin/env python3
"""Tests for bandit.py — Stochastic Trial-and-Error Bandit Engine."""

import os
import tempfile
import unittest

import bandit


class TestBandit(unittest.TestCase):
    def test_reward_prefers_cheaper_passing_arm(self):
        r_cheap = bandit.compute_reward(True, 0, budget=240)
        r_mid = bandit.compute_reward(True, 120, budget=240)
        r_heavy = bandit.compute_reward(True, 240, budget=240)
        r_fail = bandit.compute_reward(False, 0, budget=240)
        self.assertGreater(r_cheap, r_mid)
        self.assertGreater(r_mid, r_heavy)
        self.assertEqual(r_fail, 0.0)

    def test_ucb1_learns_cheapest_passing_arm(self):
        b = bandit.StochasticBandit(policy="ucb1", seed=42)
        # heuristic_fast fails, slm_compact passes cheaply, slm_ppr passes expensively
        def exec_fn(arm):
            if arm["id"] == "heuristic_fast":
                return False, 0
            if arm["id"] == "slm_compact":
                return True, 60
            return True, arm["est_tokens"]

        for _ in range(25):
            bandit.run_trial_and_error(b, "delegated-build:normal", exec_fn, max_attempts=3)

        pulls = {aid: st.pulls for aid, st in b.buckets["delegated-build:normal"].items()}
        self.assertGreater(pulls["slm_compact"], pulls["escalate_hitl"])

    def test_thompson_sampling_deterministic_with_seed(self):
        b1 = bandit.StochasticBandit(policy="thompson", seed=7)
        b2 = bandit.StochasticBandit(policy="thompson", seed=7)
        for b in (b1, b2):
            for arm in b.arms:
                b.update("ctx", arm["id"], arm["id"] == "slm_compact", arm["est_tokens"])
        picks1 = [b1.select_arm("ctx")["id"] for _ in range(10)]
        picks2 = [b2.select_arm("ctx")["id"] for _ in range(10)]
        self.assertEqual(picks1, picks2)

    def test_state_persistence_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "bandit_state.json")
            b1 = bandit.StochasticBandit(state_path=path)
            b1.update("research:urgent", "heuristic_fast", True, 0)
            self.assertTrue(os.path.exists(path))

            b2 = bandit.StochasticBandit(state_path=path)
            self.assertEqual(b2.buckets["research:urgent"]["heuristic_fast"].pulls, 1)

    def test_trial_and_error_escalates_within_cap(self):
        b = bandit.StochasticBandit(policy="ucb1")
        seen = []
        def exec_fn(arm):
            seen.append(arm["id"])
            return arm["id"] == "slm_ppr", arm["est_tokens"]

        res = bandit.run_trial_and_error(b, "security:urgent", exec_fn, max_attempts=4)
        self.assertTrue(res["passed"])
        self.assertEqual(res["winning_arm"], "slm_ppr")
        self.assertEqual(len(res["attempts"]), 3)


if __name__ == "__main__":
    unittest.main()
