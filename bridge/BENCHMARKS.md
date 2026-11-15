# 📊 Performance Benchmarks

Measured, reproducible, synthetic. Re-run any time:

```bash
python eval/runner.py --budget 200
```

## Dataset

- Synthetic graph: `tests/fixtures/graph_minimal.json` (7 memory nodes + 2 hyperedges)
- Queries: `eval/queries.json` (25 synthetic queries with expected nodes)
- Budget: 200 tokens per query
- Method comparison: Lucky.Engine vs. plain keyword search vs. dump-everything

## Results (25 queries, budget 200)

| Method | Hit rate | Avg tokens / query | Total tokens |
|--------|----------|-------------------|--------------|
| Lucky.Engine | 1.00 | 56.2 | 1404 |
| Plain keyword search | 1.00 | 16.3 | 407 |
| Dump everything | 1.00 | 86.0 | 2150 |

Numbers from `python eval/runner.py --budget 200`; use `eval/runner.py --json` for exact output. Token counts are `chars/4` estimates (`estimate_tokens`), not billed API tokenizer counts or hardware energy measurements.

## Notes

- Lucky.Engine and plain keyword both hit every expected node on this small graph.
- Lucky.Engine uses ~34.7% fewer estimated tokens than dumping everything on average (1404 vs 2150) on this 7-node fixture while returning rich node + edge rationale context.
- At this size the win is modest; it grows with graph size and query selectivity (verified up to 5000 synthetic nodes in `benchmarks/stress_test.py`).

## Scaling Tips

1. Increase `confidence_threshold` in `lucky-config.yaml` for large graphs
2. Enable caching (`cache_enabled: true`)

## External Dependency Note

A real deployment depends on the external `graphify` tool to build `graph.json`.
Lucky.Engine does not fetch it at runtime. The LLM intent classifier endpoint is
configurable (`LUCKY_LLM_API_URL`, deprecated `HLCO_LLM_API_URL`), so no "no
external access" claim should be made for setups that enable it.
