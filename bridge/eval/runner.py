#!/usr/bin/env python3
"""Deterministic eval for Lucky.Engine on synthetic graph fixture."""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import engine


def plain_keyword(query, graph):
    toks = engine._tokenize(query)
    out = []
    for node in graph.get("nodes", []):
        node_toks = engine._tokenize(node.get("label", "")) | engine._tokenize(node.get("rationale") or "")
        if toks & node_toks:
            out.append({"id": node["id"], "label": node["label"], "type": node.get("type"),
                        "confidence": 1.0, "content": engine._short_content(node)})
    return out


def dump_everything(graph):
    out = []
    for node in graph.get("nodes", []):
        out.append({"id": node["id"], "label": node["label"], "type": node.get("type"),
                    "confidence": 1.0, "content": engine._short_content(node)})
    return out


def hit_rate(results, expected):
    returned = {n["id"] for n in results}
    if not expected:
        return 1.0
    return len(returned & set(expected)) / len(expected)


def run(graph_path, config_path, budget):
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    orig_graph, orig_config = engine.MEMORY_GRAPH, engine.CONFIG_FILE
    engine.MEMORY_GRAPH = Path(graph_path)
    engine.CONFIG_FILE = Path(config_path)
    bridge = engine.load_bridge() if (ROOT / "bridge_nodes.json").exists() else []
    # use fixture bridge if present
    bridge_path = ROOT / "tests" / "fixtures" / "bridge_nodes_fixture.json"
    if bridge_path.exists():
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))

    engine.cache.clear()

    queries = json.loads(Path(ROOT / "eval" / "queries.json").read_text(encoding="utf-8"))
    rows = []
    agg = {"lucky": {"hits": 0, "tokens": 0}, "keyword": {"hits": 0, "tokens": 0},
           "dump": {"hits": 0, "tokens": 0}, "n": 0}

    for q in queries:
        # Lucky
        engine.cache.clear()
        lucky_res = engine.resolve_query(q["query"], budget=budget, edge_limit=0)
        lucky_nodes = lucky_res["nodes"]
        lucky_tok = lucky_res["budget_used"]

        kw_nodes = plain_keyword(q["query"], graph)
        kw_tok = engine.estimate_tokens(kw_nodes)

        dump_nodes = dump_everything(graph)
        dump_tok = engine.estimate_tokens(dump_nodes)

        lh = hit_rate(lucky_nodes, q["expected"])
        kh = hit_rate(kw_nodes, q["expected"])
        dh = hit_rate(dump_nodes, q["expected"])

        agg["lucky"]["hits"] += lh
        agg["lucky"]["tokens"] += lucky_tok
        agg["keyword"]["hits"] += kh
        agg["keyword"]["tokens"] += kw_tok
        agg["dump"]["hits"] += dh
        agg["dump"]["tokens"] += dump_tok
        agg["n"] += 1

        rows.append({
            "id": q["id"],
            "query": q["query"],
            "expected": q["expected"],
            "lucky_hit": lh,
            "lucky_tokens": lucky_tok,
            "keyword_hit": kh,
            "keyword_tokens": kw_tok,
            "dump_hit": dh,
            "dump_tokens": dump_tok,
        })

    engine.MEMORY_GRAPH = orig_graph
    engine.CONFIG_FILE = orig_config

    n = agg["n"]
    summary = {
        "queries": n,
        "lucky": {"hit_rate": agg["lucky"]["hits"] / n, "avg_tokens": agg["lucky"]["tokens"] / n, "total_tokens": agg["lucky"]["tokens"]},
        "keyword": {"hit_rate": agg["keyword"]["hits"] / n, "avg_tokens": agg["keyword"]["tokens"] / n, "total_tokens": agg["keyword"]["tokens"]},
        "dump": {"hit_rate": agg["dump"]["hits"] / n, "avg_tokens": agg["dump"]["tokens"] / n, "total_tokens": agg["dump"]["tokens"]},
    }

    return summary, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default=str(ROOT / "tests" / "fixtures" / "graph_minimal.json"))
    parser.add_argument("--config", default=str(ROOT / "lucky-config.yaml"))
    parser.add_argument("--budget", type=int, default=200)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary, rows = run(args.graph, args.config, args.budget)
    if args.json:
        print(json.dumps({"summary": summary, "rows": rows}, indent=2))
    else:
        print("Lucky.Engine eval (deterministic, synthetic)")
        print(f"queries: {summary['queries']}  budget: {args.budget}")
        print(f"{'method':10} {'hit_rate':>9} {'avg_tokens':>11} {'total_tokens':>13}")
        for m in ("lucky", "keyword", "dump"):
            s = summary[m]
            print(f"{m:10} {s['hit_rate']:>9.2f} {s['avg_tokens']:>11.1f} {s['total_tokens']:>13}")
        print("\nPer-query (lucky hit / tokens):")
        for r in rows:
            print(f"  {r['id']}: hit={r['lucky_hit']:.2f} tok={r['lucky_tokens']}")


if __name__ == "__main__":
    main()
