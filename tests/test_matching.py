"""Tests for Lucky.Engine Chunk 3 token-overlap matching."""

import os
import tempfile
import unittest
from pathlib import Path

import engine


class TestMatching(unittest.TestCase):
    def setUp(self):
        self._orig_graph = None
        self._tmp = Path(tempfile.mkdtemp())
        import json
        g = {
            "directed": False, "multigraph": False,
            "graph": {"hyperedges": []},
            "nodes": [
                {"id": "move_plan", "label": "Move Plan", "rationale": "r", "type": "memory_node"},
                {"id": "move_fund", "label": "Move Fund", "rationale": "r", "type": "memory_node"},
            ],
        }
        self.gp = self._tmp / "g.json"
        self.gp.write_text(json.dumps(g), encoding="utf-8")

    def test_token_overlap_matches_move_plan(self):
        graph = __import__("json").loads(self.gp.read_text(encoding="utf-8"))
        bridge = []
        result_nodes = engine.find_relevant_nodes("what is my move plan?", "relocation", bridge, graph)
        ids = [n["id"] for n in result_nodes]
        self.assertIn("move_plan", ids)

    def test_stopwords_dropped(self):
        toks = engine._tokenize("What is my Move Plan?")
        self.assertNotIn("what", toks)
        self.assertNotIn("is", toks)
        self.assertIn("move", toks)
        self.assertIn("plan", toks)

    def test_query_substring_not_required(self):
        graph = __import__("json").loads(self.gp.read_text(encoding="utf-8"))
        bridge = []
        # "move plan?" with punctuation still matches
        result_nodes = engine.find_relevant_nodes("MOVE PLAN!!!", "relocation", bridge, graph)
        self.assertTrue(any(n["id"] == "move_plan" for n in result_nodes))


if __name__ == "__main__":
    unittest.main()
