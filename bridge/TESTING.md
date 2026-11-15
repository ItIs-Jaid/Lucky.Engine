# Testing

## Local

```bash
python test_suite.py
python tests/run_tests.py
python eval/runner.py --budget 200
```

Expected: test_suite 4/4, unittest 19/19, eval 25 queries.

## Docker (provider-agnostic)

```bash
docker run --rm -v "$PWD":/app -w /app python:3.14 bash -c "python test_suite.py && python tests/run_tests.py"
```

Optional LLM path smoke test uses a local OpenAI-compatible endpoint and sets
`LUCKY_LLM_API_KEY`, `LUCKY_LLM_API_URL`.

## Scope

- Tests use synthetic fixtures only (`tests/fixtures/`).
- No real `graph.json`, `USER.md`, `MEMORY-SSOT.md`, or audit logs are read.