# Lucky.Engine 1.6.0 — Unified Graph-Memory Bridge, Chain Router & Eval Harness

**Status:** v1.6.0 unified release — local-first, Python stdlib-only core (`dependencies = []`).
**Scope:** Layer 1 (`bridge/`) graph-memory retrieval + Layer 2 (`router.py`, `gateway.py`, `chainlib.py`) deterministic task-to-chain routing + Eval & DevOps Harness (`evals/`, `harness/`, `devops/`).

---

## The problem this solves

Skills in this pool are dispatched by the model *noticing* a description. Measured from
1,076 real sessions (`state.db`, 55,231 messages, 28,951 tool calls):

- 409 sessions loaded a skill; **220 loaded 2+, only 127 loaded 3+**
- **~45 of 261 indexed skills have never been loaded once**
- the same 3-skill patterns recur without an owner: the model re-derives them every time

So the pool is not short on skills. It is short on **routing**. 1.5.0 makes routing
deterministic and free, and gives every chain an explicit end-state gate so "done" means
an artifact validated, not a confident sentence.

## What is in here

```
README.md          this file — proposal, status, roadmap
CHAIN-MAP.md       the 5 roots + fallback: node tables, triggers, loop contracts
chains.yaml        chains: judged loops + gateways + urgency tiers (the config)
GATEWAY.md         the gateway protocol: judges, outcomes, point budget, escalation
public/            publishable slice (catalog.json)
check_public.py    publication gate: fails on leaked identifiers
test_public.py     proves the gate catches real leaks
router.py          working resolver, stdlib only, no LLM call
test_router.py     142 executable gates (run it, don't trust this README)
gateway.py         urgency-tiered gateway ledger & deterministic artifact verifier
test_gateway.py    174 executable gates (disk verification + retry headroom)
segments/*.md      26 node cards, each <=350 tokens, one job each
```

## Quickstart

```sh
python devops/verify_all.py
python router.py --task "write a cited competitor report" --pack
python router.py --task "fix the failing tests" --invoked subagent-delegation,agentic-teams,subagent-driven-development
python test_router.py
```

Real output of the first command (117 tokens, versus loading 3-4 skill files):

```
ROOT: R-RESEARCH-SYNTHESIS  (chain research-synthesis, confidence 0.75)
START (once): S-context-pack
PRE-LOOP (once): S-question-frame -> S-source-discovery -> S-source-triage
LOOP (repeat): S-claim-extract -> S-cite-verify  max_iter=6
END (once): S-synthesis
EXIT: claims_cited == claims_total   CHECKPOINT: .lucky/ledger-research.jsonl
END OUTPUT: report.md
DONE WHEN: every claim maps to a resolvable url or file path
RULE: pre_loop runs once. Only the loop repeats. Load one node, never the whole chain.
```

## The node grammar (the answer to "more nodes before the loop")

Every chain is four phases. The pre-loop spine is where convergence happens; the loop
body should be small and repeatable, not a container for everything.

| Phase | Runs | Job | Budget |
|---|---|---|---|
| `start` | once | orient, load context pack, no side effects | 1-2 nodes |
| `pre_loop` | **once** | converge the question, lock scope, gather candidates | 2-4 nodes |
| `loop` | repeats until `exit` | act + verify one thin slice per iteration | 1-3 nodes |
| `end` | once | emit artifact, apply gate, declare done or not-done | 1-2 nodes |

Splitting pre-loop from loop is the whole trick: pre-loop work that gets *repeated* is
what burns tokens and produces drift, and loop work that only needed doing *once* is what
makes "done" arrive by accretion instead of by gate.

## Verified state

- `python test_router.py` -> **142 PASS** · `python test_gateway.py` -> **174 PASS** (316 total engine gates)
- `python test_public.py` -> **PASS**; `check_public.py --path public/` -> CLEAN
- 26 node cards, **max 147 tokens** (estimate: chars/4), all under the 350 budget
- context pack: **117 tokens**, includes exit predicate + end gate
- router: stdlib only, no `subprocess`, no network, deterministic (same input, same output)
- one real bug found and fixed by the tests: `count_gte` adds +2 per matched skill *plus*
  +3 gate bonus, so a 3rd skill is worth +5, not +3. The test now asserts the real semantics.

## Not done (honest scope)

- No Hermes hook: the router is not yet called automatically at task start. That is Phase 2.
- No live skill files were patched. External workspace skill trees remain untouched.
- Unified v1.6.0 merges Layer 1 (`bridge/`), Layer 2 (`router.py` / `gateway.py` / `chainlib.py`), Eval Harness (`evals/`, `harness/`, `benchmark/`), and Optional Firebase/DAK DevOps (`harness/firebase/`, `devops/`, `docs/DEVOPS-FIREBASE-DAK.md`).
- `chains.yaml` keywords are hand-authored from query vocabulary, not fitted. Phase 4 fits them
  against the session DB and measures whether routing matches what you actually asked.

## Roadmap

| Phase | Deliverable | Gate |
|---|---|---|
| 1 ✅ | router + gateway + 5 chains + 26 nodes | 316 executable gates pass (142 router + 174 gateway) |
| 2 | wire `router.py --pack` into task start via a Hermes skill | 20 live sessions, chain matches intent |
| 3 | target the 45 never-loaded skills: patch, merge, or quarantine | indexed 261 -> ~220, zero loss |
| 4 | fit triggers against `state.db` history; measure hit rate | precision >= 0.8 on 200 past tasks |
| 5 | publish a sanitized skeleton (placeholder paths) | no personal identifiers in repo |

**Decision gates you own:** Phase 3 deletes or merges skills. Phase 5 publishes. Neither
runs without your explicit yes.
