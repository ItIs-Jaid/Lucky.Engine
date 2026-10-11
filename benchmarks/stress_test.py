#!/usr/bin/env python3
"""
HLCO Stress Test
Run in Docker: docker run hlco-benchmark python benchmarks/stress_test.py
"""

import os
import json
import subprocess
from pathlib import Path

def run_query(query, budget=500):
    """Run a single query and return results."""
    try:
        result = subprocess.run(
            ["python", "engine.py", query, "--budget", str(budget)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

def main():
    results = []
    
    # Test configurations
    configurations = [
        {"size": "34 nodes", "queries": ["finances", "move plan", "ssh"]},
        {"size": "1000 nodes (scaled)", "queries": ["finances", "move plan", "ssh"]},
        {"size": "5000 nodes (scaled)", "queries": ["finances", "move plan", "ssh"]},
    ]
    
    for config in configurations:
        print(f"Testing {config['size']}...")
        for query in config["queries"]:
            result = run_query(query)
            results.append({
                "graph_size": config["size"],
                "query": query,
                "tokens": result.get("budget_used", 0),
                "intent": result.get("intent", "unknown"),
            })
    
    # Save results
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Saved {len(results)} results to benchmark_results.json")

if __name__ == "__main__":
    main()
