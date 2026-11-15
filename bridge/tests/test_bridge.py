"""Tests for Lucky.Engine Chunk 4 bridge resolution."""

import json
import os
import tempfile
import unittest
from pathlib import Path

import engine

ROOT = Path(__file__).resolve().parent


class TestBridge(unittest.TestCase):
    def test_skill_match_pulls_linked_memory_node(self):
        graph = json.loads((ROOT / "fixtures" / "graph_minimal.json").read_text(encoding="utf-8"))
        bridge = json.loads((ROOT / "fixtures" / "bridge_nodes_fixture.json").read_text(encoding="utf-8"))
        nodes = engine.find_relevant_nodes("finances check", "financial", bridge, graph)
        ids = [n["id"] for n in nodes]
        self.assertIn("SKILL-finances_0", ids)
        self.assertIn("move_fund", ids)

    def test_no_duplicate_ids(self):
        graph = json.loads((ROOT / "fixtures" / "graph_minimal.json").read_text(encoding="utf-8"))
        bridge = json.loads((ROOT / "fixtures" / "bridge_nodes_fixture.json").read_text(encoding="utf-8"))
        nodes = engine.find_relevant_nodes("finances productivity goals", "financial", bridge, graph)
        ids = [n["id"] for n in nodes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_resolve_memory_ref_helper(self):
        graph = json.loads((ROOT / "fixtures" / "graph_minimal.json").read_text(encoding="utf-8"))
        node = engine._resolve_memory_ref("Income Bridge", graph)
        self.assertIsNotNone(node)
        self.assertEqual(node["id"], "income_bridge")


if __name__ == "__main__":
    unittest.main()
