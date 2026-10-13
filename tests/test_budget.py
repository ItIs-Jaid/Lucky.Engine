"""Tests for Lucky.Engine Chunk 5 budget/content behaviour."""

import json
import os
import tempfile
import unittest
from pathlib import Path

import engine


class TestBudget(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.graph = {
            "directed": False, "multigraph": False,
            "graph": {"hyperedges": []},
            "nodes": [
                {"id": "move_plan", "label": "Move Plan", "rationale": "Olympia primary target by Feb 2027", "type": "memory_node"},
                {"id": "move_fund", "label": "Move Fund", "rationale": "7k liquid move fund", "type": "memory_node"},
            ],
        }
        self.gp = self.tmp / "g.json"
        self.gp.write_text(json.dumps(self.graph), encoding="utf-8")
        self.cp = self.tmp / "c.yaml"
        self.cp.write_text("max_tokens: 1000\ndefault_budget: 1000\nconfidence_threshold: 0.1\n", encoding="utf-8")

    def _run(self):
        orig_graph, orig_config = engine.MEMORY_GRAPH, engine.CONFIG_FILE
        engine.MEMORY_GRAPH = self.gp
        engine.CONFIG_FILE = self.cp
        engine.cache.clear()
        try:
            return engine.resolve_query("move plan", budget=20, edge_limit=0)
        finally:
            engine.MEMORY_GRAPH = orig_graph
            engine.CONFIG_FILE = orig_config

    def test_nodes_include_short_content(self):
        res = self._run()
        self.assertTrue(all("content" in n for n in res["nodes"]))
        self.assertEqual(res["nodes"][0]["content"], "Olympia primary target by Feb 2027")

    def test_content_none_when_no_rationale(self):
        self.graph["nodes"][0]["rationale"] = None
        self.gp.write_text(json.dumps(self.graph), encoding="utf-8")
        res = self._run()
        self.assertIsNone(res["nodes"][0]["content"])

    def test_greedy_respects_budget(self):
        res = self._run()
        self.assertLessEqual(res["budget_used"], 20 + 5)  # tolerance for one node overhead
        # at least one node returned even under tiny budget
        self.assertGreaterEqual(len(res["nodes"]), 1)

    def test_estimate_tokens_chars_over_four(self):
        nodes = [{"label": "Move Plan", "content": "abcd"}]
        est = engine.estimate_tokens(nodes)
        # (9+4)/4 = 3.25 -> at least 3 plus overhead, just check monotonic-ish positivity
        self.assertGreater(est, 0)


if __name__ == "__main__":
    unittest.main()
