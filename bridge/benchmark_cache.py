#!/usr/bin/env python3
"""
Cache Performance Benchmark
Tests time savings from caching across multiple query turns.
"""

import time
from engine import resolve_query, cache

def run_benchmark():
    print("=== Cache Performance Test ===")
    
    # Test Case 1: Same query twice (should cache)
    query = "What is my move plan?"
    
    # First query (cold cache)
    start = time.time()
    result1 = resolve_query(query, budget=500, edge_limit=0)
    cold_time = (time.time() - start) * 1000
    
    print(f"\nQuery 1: '{query}' [COLD]")
    print(f"  Time: {cold_time:.0f}ms | Budget Used: {result1.get('budget_used', 'N/A')}")
    
    # Second query (cached)
    start = time.time()
    result2 = resolve_query(query, budget=500, edge_limit=0)
    cached_time = (time.time() - start) * 1000
    
    print(f"\nQuery 2: '{query}' [HIT]")
    print(f"  Time: {cached_time:.0f}ms | Budget Used: {result2.get('budget_used', 'N/A')}")
    
    # Test Case 2: Different query
    query2 = "What are my finances?"
    start = time.time()
    result3 = resolve_query(query2, budget=500, edge_limit=0)
    miss_time = (time.time() - start) * 1000
    
    print(f"\nQuery 3: '{query2}' [MISS]")
    print(f"  Time: {miss_time:.0f}ms | Budget Used: {result3.get('budget_used', 'N/A')}")
    
    # Stats
    print(f"\nCache Stats: {cache.stats}")
    
    # Calculate savings
    if cached_time > 0:
        speedup = cold_time / cached_time
        print(f"\n⚡ Speedup: {speedup:.1f}x faster on cached queries")
    else:
        print(f"\n⚡ Speedup: N/A (cached response time: 0)")

if __name__ == "__main__":
    run_benchmark()
