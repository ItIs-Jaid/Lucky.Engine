# Cache Benchmark Tests

## Purpose
Tests the efficiency of the ContextCache system for reducing latency and token usage across conversation turns.

## Running Benchmarks
```bash
python benchmark_cache.py
```

## Expected Results

### First Query (Cold Cache)
- Latency: ~150-250ms
- Token Count: Full graph traversal

### Same Query (Cached)
- Latency: ~5-10ms (10-20x faster)
- Token Count: 0 (returned from cache)

### Different Query (Same Intent)
- Latency: ~200ms
- Token Count: Reduced by intent matching

## Sample Output
```
=== Cache Performance Test ===
Query 1: "What is my move plan?" [COLD]
  Time: 215ms | Tokens: 1320

Query 2: "What is my move plan?" [HIT]
  Time: 8ms | Tokens: 0 (cached)

Query 3: "What are my finances?" [MISS]
  Time: 205ms | Tokens: 320

Cache Stats: {hits: 1, misses: 2, evictions: 0}
```

## Configuration
Edit `lucky-config.yaml` to tune cache settings:
```yaml
cache:
  enabled: true
  max_size: 100
  ttl_seconds: 3600
```

## Integration
To disable caching for development, set `cache.enabled: false` in config.
