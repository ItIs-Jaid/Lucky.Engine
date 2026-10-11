#!/usr/bin/env python3
"""HLCO Test Suite - run before public deployment"""

import json
import subprocess
import sys
import os

# Add bridge directory to path so cache.py can be imported directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import cache

def test_cache_basic():
    """Test basic cache set/get functionality"""
    cache.clear()
    
    # Test miss
    result = cache.get("test_key_missing")
    assert result is None, "Expected None on cache miss"
    assert cache.stats["misses"] == 1, "Expected 1 miss"
    
    # Test set
    cache.set("test_key", {"data": "value"})
    
    # Test hit
    result = cache.get("test_key")
    assert result is not None, "Expected cached value"
    assert result["value"]["data"] == "value", "Expected value to match"
    assert cache.stats["hits"] == 1, "Expected 1 hit"
    
    print("✓ test_cache_basic passed")

def test_cache_eviction():
    """Test LRU eviction when cache is full"""
    cache.clear()
    cache.max_size = 3
    
    cache.set("key1", {"data": "1"})
    cache.set("key2", {"data": "2"})
    cache.set("key3", {"data": "3"})
    
    # Access key1 to make it recently used
    cache.get("key1")
    
    # Add key4, should evict key2 (least recently used)
    cache.set("key4", {"data": "4"})
    
    assert cache.get("key1") is not None, "key1 should still be cached"
    assert cache.get("key3") is not None, "key3 should still be cached"
    assert cache.get("key4") is not None, "key4 should be cached"
    assert cache.get("key2") is None, "key2 should be evicted"
    assert cache.stats["evictions"] == 1, "Expected 1 eviction"
    
    print("✓ test_cache_eviction passed")

def test_cache_stats():
    """Test cache statistics tracking"""
    cache.clear()
    cache.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    # Generate some hits and misses
    cache.get("nonexistent1")
    cache.get("nonexistent2")
    cache.set("key1", {"data": "value1"})
    cache.get("key1")
    cache.get("key1")
    
    assert cache.stats["hits"] == 2, f"Expected 2 hits, got {cache.stats['hits']}"
    assert cache.stats["misses"] == 2, f"Expected 2 misses, got {cache.stats['misses']}"
    
    print("✓ test_cache_stats passed")

def test_engine_cache():
    """Test that resolve_query properly caches results"""
    # Run first query (should be a cache miss)
    result1 = subprocess.run(
        ["python", "engine.py", "finances"],
        capture_output=True,
        text=True,
        timeout=10
    )
    output1 = json.loads(result1.stdout)
    
    # Verify it ran
    assert result1.returncode == 0, f"First query failed: {result1.stderr}"
    assert "nodes" in output1, "Expected nodes in response"
    
    print("✓ test_engine_cache passed")

# Run all tests
if __name__ == "__main__":
    tests = [test_cache_basic, test_cache_eviction, test_cache_stats, test_engine_cache]
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
