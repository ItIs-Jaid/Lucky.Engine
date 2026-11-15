#!/usr/bin/env python3
"""Real Lucky.Engine scaling benchmark."""

import argparse
import json
import os
import random
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engine

random.seed(42)

QUERIES = ["finances", "move plan", "ssh", "what can I afford for relocation?", "check tailscale network"]

CORE_EXPECTED = {
    "finances": {"live_memory_finances", "live_user_liabilities", "live_user_move_fund", "live_user_income_bridge", "memory_ssot_income_bridge", "memory_ssot_move_fund"},
    "move plan": {"memory_ssot_move_plan", "live_memory_move_plan", "live_user_move_plan", "live_user_move_target", "live_user_move_fund", "live_user_income_bridge"},
    "ssh": {"live_memory_ssh_lane"},
    "what can i afford for relocation?": {"memory_ssot_move_plan", "live_user_move_target", "live_user_move_fund", "live_user_income_bridge"},
    "check tailscale network": {"live_memory_tailnet"},
}


def make_graph(size):
    base = engine.load_memory_graph() if False else None
    import json as _j
    # load real core graph directly
    real_path = ROOT / ".." / "graph.json" if False else ROOT.parent / "graph.json"
    core = _j.loads((real_path).read_text(encoding="utf-8"))
    core_nodes = list(core.get("nodes", []))
    core_edges = list(core.get("edges", core.get("links", [])))
    core_hypers = list(core.get("hyperedges") or (core.get("graph") or {}).get("hyperedges", []))

    nodes = [dict(n) for n in core_nodes]
    edges = [dict(e) for e in core_edges]
    hypers = [dict(h) for h in core_hypers]

    next_id = len(nodes)
    for i in range(size - len(core_nodes)):
        nid = f"distractor_{i}"
        nodes.append({"id": nid, "label": f"Distractor Node {i}", "type": "memory_node", "rationale": "noise"})
        if i > 0 and i % 7 == 0:
            edges.append({"source": nid, "target": f"distractor_{i-1}"})
        if i % 17 == 0:
            hypers.append({"id": f"noise_{i}", "nodes": [nid, f"distractor_{max(0, i-1)}"], "relation": "related"})

    graph = {
        "directed": False,
        "multigraph": False,
        "graph": {"hyperedges": hypers},
        "nodes": nodes,
        "links": edges,
        "edges": edges,
        "hyperedges": hypers,
    }
    return graph


def baseline_tokens(graph):
    nodes = [{"label": n.get("label"), "content": engine._short_content(n)} for n in graph.get("nodes", [])]
    return engine.estimate_tokens(nodes)


def expected_ids(q):
    return set(CORE_EXPECTED.get(q.lower(), set()))


def run_scale(size):
    graph = make_graph(size)
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    Path(path).write_text(json.dumps(graph), encoding="utf-8")
    base = baseline_tokens(graph)

    orig_graph = engine.MEMORY_GRAPH
    engine.MEMORY_GRAPH = Path(path)
    engine.cache.clear()

    rows = []
    for q in QUERIES:
        t0 = time.perf_counter()
        cold = engine.resolve_query(q, budget=500, edge_limit=3)
        cold_ms = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        warm = engine.resolve_query(q, budget=500, edge_limit=3)
        warm_ms = (time.perf_counter() - t0) * 1000.0

        ids = {n.get("id") for n in warm.get("nodes", [])}
        exp = expected_ids(q)
        recall = 100.0 if not exp else (len(exp & ids) / len(exp)) * 100.0
        comp = round((1 - (warm.get("budget_used", 0) / max(1, base))) * 100.0, 2)
        rows.append({
            "graph_size": size,
            "query": q,
            "baseline_tokens": base,
            "lucky_tokens": warm.get("budget_used", 0),
            "compression_ratio_pct": comp,
            "recall_at_budget_pct": round(recall, 2),
            "cold_latency_ms": round(cold_ms, 2),
            "warm_latency_ms": round(warm_ms, 2),
            "nodes_returned": len(warm.get("nodes", [])),
        })
        print(f"  {size}: {q!r} tokens {warm.get('budget_used')} recall {recall:.1f}% cold {cold_ms:.1f}ms warm {warm_ms:.1f}ms")

    engine.MEMORY_GRAPH = orig_graph
    Path(path).unlink(missing_ok=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-llm", action="store_true")
    args = ap.parse_args()

    all_rows = []
    for size in (34, 1000, 5000):
        print(f"Testing {size} nodes...")
        all_rows.extend(run_scale(size))

    json.dump(all_rows, open(ROOT / "benchmark_results.json", "w"), indent=2)

    report = ["# Lucky.Engine Benchmark Report", "", "| Graph | Query | Baseline tokens | Lucky tokens | Compression % | Recall@Budget % | Cold ms | Warm ms |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in all_rows:
        report.append(f"| {r['graph_size']} | {r['query']} | {r['baseline_tokens']} | {r['lucky_tokens']} | {r['compression_ratio_pct']} | {r['recall_at_budget_pct']} | {r['cold_latency_ms']} | {r['warm_latency_ms']} |")
    if args.live_llm:
        report.append("")
        report.append("Live LLM A/B requested; requires LUCKY_LLM_API_URL and a running local model. This runner validates retrieval path only.")
    text = "\n".join(report) + "\n"
    for d in (ROOT / "benchmark", ROOT / "benchmarks"):
        d.mkdir(exist_ok=True)
        (d / "BENCHMARK_REPORT.md").write_text(text, encoding="utf-8")
    print("✅ benchmark results written")


if __name__ == "__main__":
    main()
