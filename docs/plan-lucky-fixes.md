# Lucky.Engine fixes — implementation plan

Branch: `lucky/fixes`. One commit per step. All tests synthetic: never edit the
real `graph.json`, `USER.md`, `MEMORY-SSOT.md`, or audit logs.

Scope guardrails (apply to every step):

- stdlib only; ask before adding a dependency.
- Write a failing test first, then fix.
- Run `python test_suite.py` AND chunk-local `python -m unittest` after each step; no failures allowed.
- No tests reference the real graph; use fixtures under `tests/fixtures/`.
- Every test asserts observable behavior tied to the stated goal (not just API presence).
- Benchmarks: deterministic synthetic data, fixed seed, committed expected values, human-rerun commands.
- Testing documentation: update `TESTING.md` each run with exact commands and expected output.
- No commit unless the step's listed test(s) pass.

Evidence & audit loop:

- Each commit message includes the test result line summary.
- `TESTING.md` records commands and last-run results.
- eval runner prints a machine-readable JSON block Summary plus a human table.
- A subagent is used once (Chunk 1) to independently draft tests before implementation; remaining chunks implemented inline with its cache as reference.

## Chunk 0 — fixtures and test scaffolding

Files:

- `tests/` (new)
- `tests/__init__.py` (empty)
- `tests/conftest-ish` helpers inline in `_fixtures.py`
- `tests/fixtures/graph_minimal.json` (synthetic 6 nodes + hyperedges)
- `tests/fixtures/bridge_nodes_fixture.json`
- `tests/run_tests.py` (runner that invokes unittest discovery)

Synthetic graph shape:

```
{ "directed": false, "multigraph": false,
  "graph": {"hyperedges":[{"nodes":["move_plan","move_fund"],"relation":"related"}]},
  "nodes": [{"id":"move_plan","label":"Move Plan","rationale":"Olympia primary target by Oct 2026"}] }
```

Synthetic bridge node shape matches existing. Gitignore `tests/__pycache__/` (already).

## Chunk 1 — `extract_intent` / `classify_intent_llm` NameError

Goal: key read inside function; auth header only when set; catch all request errors;
fallback to keyword intent (not `"general"`).

Current bug: `classify_intent_llm` references `api_key` not in scope.

Edits:

- `engine.py::classify_intent_llm`:
  - read `api_key = _env("LUCKY_LLM_API_KEY" / "HLCO_LLM_API_KEY")`
  - build headers; add `Authorization` only if `api_key`.
  - remove except specific tuple; use `except Exception` + return a keyword fallback computed separately.
  - Keep function signature `(query)` for tests but test via mocked `urllib.request.urlopen`.
- Add `_env(primary, *fallbacks)` helper.
- Rename env reads in `extract_intent` and `__main__` flow.

New tests: `tests/test_intent.py`

- `test_classify_llm_no_key_falls_back_keyword` (no URL call when env missing)
- `test_classify_llm_key_sends_auth_and_returns_intent`
- `test_classify_llm_request_error_falls_back_keyword`
- `test_extract_intent_keyword_fallback_not_general`

Acceptance: all 4 pass; `HLCO_LLM_API_KEY=dummy` no longer raises; module test mocks only stdlib.

Commit msg: `fix(intent): resolve NameError, env rename, safe fallback`

## Chunk 2 — nested config parser + LUCKY_* naming

Goal: `skill_weights` populated; cache_enabled and fallback_budget read; threshold
applied on every branch incl. fallback.

Edits:

- `load_config()` rewrite stdlib-only nested YAML subset:
  - handle top-level and one-level indentation (`skill_weights:` block).
  - cache load per call (no global) but cheap; simplest: parse each call.
  - env var names: read either `LUCKY_CONFIG_FILE` / `HLCO_CONFIG_FILE`.
  - return keys: max_tokens, confidence_threshold, audit_max_lines, default_budget,
    fallback_budget, cache_enabled, skill_weights (dict), intent_priorities (dict).
  - fallback default config must include all keys and match.
- Apply confidence_threshold in find_relevant_nodes always (already does 0.85 vs
  0.8 hardcoded? change fallback to use config threshold; do after Chunk 3).

New tests: `tests/test_config.py`

- `test_nested_skill_weights_loaded`
- `test_cache_enabled_read`
- `test_fallback_budget`
- `test_threshold_every_branch`

Acceptance: config loads weights dict non-empty; mocked config default.

Commit msg: `feat(config): nested yaml, weights, cache flags, thresholds`

## Chunk 3 — token-overlap matching

Goal: `"what is my move plan?"` matches `"Move Plan"` without hardcoded fallback.

Edits:

- Add stopwords set.
- `tokenize(s)` -> set of lowercase alphanumeric tokens minus stopwords.
- `find_relevant_nodes`:
  - label score = len(tokens intersection) / len(label_tokens).
  - match if score > 0.
  - keep confidence thresholds.
  - remove intent_priorities hardcoded reliance (use config, optional).
  - fallback (if no matches) uses config intent_priorities; if missing, none.

New tests: `tests/test_matching.py`

- token stem case, stopword drops, move plan.
- no match returns empty list unless fallback config absent -> empty.

Acceptance test count.

Commit msg: `feat(matching): token-overlap scoring, stopwords`

## Chunk 4 — real bridge + config-driven priorities

Goal: skill match pulls linked memory node via memory_ref resolution; intents and priority
labels moved to config.

Edits:

- Load config intent_priorities.
- `resolve_memory_ref(ref, graph)` finds node by label or norm_label.
- In find_relevant_nodes, for each matched skill bridge node, append the resolved memory node with confidence+0.05 (if present).
- Move `intents` list and intent_priorities from `extract_intent` to config
  (`intent_keywords`, `intent_priorities`).
- bridge_edges.json: drop usage; document. Remove load_bridge_edges (not present already).
  Keep `bridge_edges.json` untouched.

New tests: `tests/test_bridge.py`

- skill match pulls memory node.
- no duplicate ids.
- works on any graph (synthetic with different labels).

Commit msg: `feat(bridge): resolve memory_ref, config-driven intents`

## Chunk 5 — budget + content payload

Goal: return label + short content (rationale truncated to 120 chars, None if missing);
estimate tokens from returned data (chars/4, labelled estimate); greedy fill by confidence.

Edits:

- `estimate_tokens` -> uses nodes already in returned shape: sum over `(len(label)+len(content or "") )/4 + 2 (overhead)`, int.
- node dict gets "content": rationale[:120] or None.
- resolve_query: build `all_matched`, sort by confidence, then greedily add without
  exceeding budget (estimate incrementally). Edge expansion included.
- Budget param behavior tests.

New tests: `tests/test_budget.py`

- greedy won't exceed.
- content present when rationale.
- node without rationale content None.

Commit msg: `feat(budget): greedy fill, content payload, chars/4 estimate`

## Chunk 6 — audit log fixes

Goal: gitignore (already), append not rewrite, set excluded, utf-8 all I/O.

Edits:

- `write_audit`:
  - use append open with encoding; prepend header only if file empty.
  - trimming: keep last N lines; rewrite via `write_text` encoding utf-8 (atomic enough).
  - exclude check `excluded_ids = {m["id"] ...}`? Actually excluded = nodes not in matched; use `set`.
  - all open uses encoding="utf-8".
- load_config/memory_graph open encoding.

New tests: `tests/test_audit.py`

- append preserves prior;
- set performance not list membership (behavioral);
- utf-8 roundtrip non-ascii.

Commit msg: `fix(audit): append, set, utf-8`

## Chunk 7 — eval suite + doc softening

Goal: eval/ with ~25 synthetic queries + expected nodes. Report hit rate + tokens for
Lucky vs plain keyword vs dump-everything. Update BENCHMARKS.md real numbers; drop/soften
unverified claims.

Files:

- `eval/queries.json`
- `eval/runner.py` (stdlib)
- `eval/__init__.py`
- `eval/report.md` generated output (committed? generator)
- BENCHMARKS.md edits
- README.md edits

Acceptance: runner exits 0, prints JSON or markdown summary; numbers match.

Commit msg: `feat(eval): synthetic eval + benchmarks update`

## Chunk 8 — housekeeping env + docs

Goal: rename HLCO_* -> LUCKY_* primary (keep old as deprecated fallback); fix/remove
docker command in BENCHMARKS.md; note graphify dependency README.

Edits mostly covered env rename in prior chunks. Ensure complete sweep via grep.

Commit msg: `chore(env): complete HLCO->LUCKY rename, docs`

## Order of operations

Chunks 1-8 sequential. Keep commits small.

## Ambiguity log

- Content field: rationale trunc 120 (decided).
- cache_enabled default true.
- env var deprecation keep fallback.
- bridge_edges handling: keep file, no usage.
- docker command: remove docker block, replace with python runner instructions.

## Definition of done

- `python test_suite.py` green.
- `python -m unittest discover -s tests` green.
- eval runner green.
- grep for HLCO no public docs claim; code retains fallback.
- Branch lucky/fixes with 8 commits.