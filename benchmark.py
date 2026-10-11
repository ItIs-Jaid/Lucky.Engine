#!/usr/bin/env python3
"""
Benchmark HLCO vs. full graphify queries for token/time savings.
"""
import json
import time
import subprocess
import sys

# Constants
MEMORY_GRAPH = "C:/Users/<your-name>/<your-project>/memory/graphify-out/graph.json"
GRAPHIFY_MAIN = "C:/Users/<your-name>/<your-project>/graphify-out/graph.json"
HLCO_ENGINE = "C:/Users/<your-name>/<your-project>/memory/graphify-out/bridge/engine.py"

# Queries to test
TEST_QUERIES = [
    "finances",
    "move plan",
    "ssh",
    "hermes agent",
    "memory structure",
]

def get_full_graph_stats(graph_path):
    """Get graph statistics from a graph.json file."""
    with open(graph_path) as f:
        g = json.load(f)
    return {
        "node_count": len(g.get("nodes", [])),
        "edge_count": len(g.get("links", [])),
        "estimated_full_tokens": len(g.get("nodes", [])) * 100  # ~100 tokens per node
    }

def run_hlco_query(query, budget=500):
    """Run a query through the HLCO engine and return timing + token data."""
    start = time.time()
    result = subprocess.run(
        [sys.executable, HLCO_ENGINE, query, "--budget", str(budget)],
        capture_output=True,
        text=True,
        timeout=10
    )
    elapsed = time.time() - start
    
    if result.returncode == 0:
        output = json.loads(result.stdout)
        return {
            "success": True,
            "query": query,
            "intent": output.get("intent", "unknown"),
            "tokens_used": output.get("budget_used", 0),
            "nodes_returned": len(output.get("nodes", [])),
            "time_ms": elapsed * 1000,
            "edge_followed": output.get("edge_followed_count", 0)
        }
    else:
        return {
            "success": False,
            "query": query,
            "error": result.stderr
        }

def main():
    # Get full graph stats (representative of what "full context" would load)
    memory_stats = get_full_graph_stats(MEMORY_GRAPH)
    main_stats = get_full_graph_stats(GRAPHIFY_MAIN)
    
    print("=" * 60)
    print("HLCO vs. Full Graphify Benchmark")
    print("=" * 60)
    print(f"\nMemory Graph (used by HLCO): {memory_stats['node_count']} nodes")
    print(f"Main Graph (full corpus): {main_stats['node_count']} nodes (~{main_stats['estimated_full_tokens']:,} tokens if fully loaded)")
    print("\n--- Running HLCO Queries ---")
    
    hlco_results = []
    total_hlco_tokens = 0
    total_time = 0
    
    for query in TEST_QUERIES:
        result = run_hlco_query(query)
        hlco_results.append(result)
        if result["success"]:
            total_hlco_tokens += result["tokens_used"]
            total_time += result["time_ms"]
            status = "✅"
        else:
            status = "❌"
        print(f"{status} {query}: {result.get('tokens_used', 'N/A')} tokens, {result.get('time_ms', 0):.2f}ms")
    
    print("\n--- Benchmark Summary ---")
    print(f"Total HLCO tokens (5 queries): {total_hlco_tokens}")
    print(f"Total HLCO time: {total_time:.2f}ms")
    print(f"\nFull graph query estimate: ~{main_stats['estimated_full_tokens']:,} tokens (if loading all {main_stats['node_count']} nodes)")
    print(f"\nToken savings with HLCO: {main_stats['estimated_full_tokens'] - total_hlco_tokens} tokens ({(1 - total_hlco_tokens/main_stats['estimated_full_tokens'])*100:.1f}% reduction)")
    print(f"Per-query average: {total_hlco_tokens/len(TEST_QUERIES):.0f} tokens vs. ~{main_stats['estimated_full_tokens']/len(TEST_QUERIES):.0f} tokens")
    
    # Build final report
    report = {
        "benchmark_results": {
            "graph_stats": {
                "memory_graph_nodes": memory_stats["node_count"],
                "main_graph_nodes": main_stats["node_count"],
                "main_graph_edges": main_stats["edge_count"]
            },
            "hlco_results": hlco_results,
            "totals": {
                "total_tokens": total_hlco_tokens,
                "total_time_ms": round(total_time, 2),
                "queries_run": len(TEST_QUERIES)
            },
            "savings": {
                "full_graph_tokens_estimated": main_stats["estimated_full_tokens"],
                "hlco_tokens_used": total_hlco_tokens,
                "token_savings": main_stats["estimated_full_tokens"] - total_hlco_tokens,
                "percentage_reduction": round((1 - total_hlco_tokens/main_stats["estimated_full_tokens"])*100, 1)
            }
        }
    }
    
    # Write results to file
    with open("benchmark_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n--- Results saved to benchmark_results.json ---")
    return report

if __name__ == "__main__":
    main()
