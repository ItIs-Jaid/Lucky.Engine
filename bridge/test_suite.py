#!/usr/bin/env python3
"""HLCO Test Suite - run before public deployment"""

import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import cache
import engine


def test_cache_basic():
    cache.clear()
    result = cache.get("test_key_missing")
    assert result is None
    assert cache.stats["misses"] == 1
    cache.set("test_key", {"data": "value"})
    result = cache.get("test_key")
    assert result is not None
    assert result["value"]["data"] == "value"
    assert cache.stats["hits"] == 1
    print("✓ test_cache_basic passed")


def test_cache_eviction():
    cache.clear()
    cache.max_size = 3
    cache.set("key1", {"data": "1"})
    cache.set("key2", {"data": "2"})
    cache.set("key3", {"data": "3"})
    cache.get("key1")
    cache.set("key4", {"data": "4"})
    assert cache.get("key1") is not None
    assert cache.get("key3") is not None
    assert cache.get("key4") is not None
    assert cache.get("key2") is None
    assert cache.stats["evictions"] == 1
    print("✓ test_cache_eviction passed")


def test_cache_stats():
    cache.clear()
    cache.stats = {"hits": 0, "misses": 0, "evictions": 0}
    cache.get("nonexistent1")
    cache.get("nonexistent2")
    cache.set("key1", {"data": "value1"})
    cache.get("key1")
    cache.get("key1")
    assert cache.stats["hits"] == 2
    assert cache.stats["misses"] == 2
    print("✓ test_cache_stats passed")


def test_engine_cache():
    result1 = subprocess.run(
        ["python", "engine.py", "finances"],
        capture_output=True, text=True, timeout=10
    )
    output1 = json.loads(result1.stdout)
    assert result1.returncode == 0
    assert "nodes" in output1
    print("✓ test_engine_cache passed")


def test_cli_budget_enforcement():
    r150 = subprocess.run(["python", "engine.py", "finances", "--budget", "150"], capture_output=True, text=True, timeout=10)
    r500 = subprocess.run(["python", "engine.py", "finances", "--budget", "500"], capture_output=True, text=True, timeout=10)
    o150 = json.loads(r150.stdout)
    o500 = json.loads(r500.stdout)
    assert r150.returncode == 0 and r500.returncode == 0
    assert o150["budget_used"] <= 150 + 10
    assert o500["budget_used"] <= 500
    print("✓ test_cli_budget_enforcement passed")


def test_cache_hit_schema_consistency():
    engine.cache.clear()
    r1 = engine.resolve_query("finances", budget=500, edge_limit=3)
    r2 = engine.resolve_query("finances", budget=500, edge_limit=3)
    assert r1["nodes"] == r2["nodes"]
    print("✓ test_cache_hit_schema_consistency passed")


def test_all_18_skills_resolve_memory_refs():
    bridge = json.loads(open("bridge_nodes.json", encoding="utf-8").read())
    skills = sorted({n["skill"] for n in bridge})
    assert len(skills) == 18
    for skill in skills:
        q = skill.replace("-", " ").replace("_", " ")
        nodes = engine.find_relevant_nodes(q, engine.extract_intent(q), bridge, engine.load_memory_graph())
        assert any(n["type"] == "skill_reference" and n["id"].startswith("SKILL-" + skill.replace("-", "_")) for n in nodes), skill
    print("✓ test_all_18_skills_resolve_memory_refs passed")


def test_working_memory_write_back():
    tmp = Path(tempfile.mkdtemp())
    graph_path = tmp / "g.json"
    graph_path.write_text(
        json.dumps({"directed": False, "multigraph": False, "graph": {"hyperedges": []},
                    "nodes": [{"id": "move_fund", "label": "Move Fund", "rationale": "old", "type": "memory_node"}],
                    "links": [], "edges": [], "hyperedges": []}),
        encoding="utf-8")
    orig = engine.MEMORY_GRAPH
    engine.MEMORY_GRAPH = graph_path
    engine.cache.clear()
    try:
        out = engine.update_memory_node("move_fund", "new content")
        assert out["status"] == "updated"
        g = json.loads(graph_path.read_text(encoding="utf-8"))
        n = next(n for n in g["nodes"] if n["id"] == "move_fund")
        assert n.get("rationale") == "new content" or n.get("content") == "new content"
    finally:
        engine.MEMORY_GRAPH = orig
    print("✓ test_working_memory_write_back passed")


if __name__ == "__main__":
    tests = [test_cache_basic, test_cache_eviction, test_cache_stats, test_engine_cache,
             test_cli_budget_enforcement, test_cache_hit_schema_consistency,
             test_all_18_skills_resolve_memory_refs, test_working_memory_write_back]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed}/{len(tests)} passed")
    sys.exit(0 if failed == 0 else 1)
