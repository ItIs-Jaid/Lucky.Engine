# /boost 1.5 — Chain Boost

A customized successor to `/boost` (antigravity-home, 2026-10-18), fitted to this host:
desktop-first, terminal-native, cheap/free model tiers, 40+ model churn, 261 skills.

**What changed and what didn't.** P1-P5 are sound and are inherited unchanged. 1.5.0 adds
P6-P8 and one structural idea: *a skill is a node, not a document.* A skill's job is to move
one part of a chain from a known state to a gated state, and then get out of the way.

---

## Part 1 — Inherited pillars (unchanged, restated for the record)

| # | Pillar | Kept because |
|---|---|---|
| P1 | Thinking-level modulation | extraction/formatting tasks should not burn reasoning |
| P2 | Token-budget fact grounding | any doc >2k tokens gets pre-digested into cards |
| P3 | Deterministic schema output | never require markdown-wrapped JSON |
| P4 | Native tools over shell **scraping** | see local amendment below |
| P5 | Two-mode execution | quick (<30s) vs detached with checkpointing |

### P4 local amendment (measured, not stylistic)

/boost Pillar 4 in `02-boost-skill-optimization-blueprint.md` targeted cloud google-genai server-side tools (`google_search`, `url_context`, `code_execution`). On this local Hermes host, `terminal` (33% of all tool calls, 9,687) is the primary execution substrate and only shell HTML scraping is prohibited in favor of `web_search`/`web_extract`. Reading, executing, and testing locally through `terminal` is correct and preferred.

### P5 local amendment

Speed is not the constraint here — turn budget is (`agent.max_turns: 15`). So detached mode
means "checkpointed ledger a later session can resume", not "overnight batch".

---

## Part 2 — The three new pillars

### P6 — Chain role in frontmatter

Every skill declares what it is in a chain. Without this the router can only guess.

```yaml
---
name: S-cite-verify
description: "Use when claims need sources before publication."   # <=57 chars trigger
metadata:
  hermes:
    boost:
      role: segment            # root | segment | loop
      chain: research-synthesis
      phase: loop              # start | pre_loop | loop | end
      context_budget: 350      # hard token ceiling for this node
      end_output: "ratio == 1.0"
---
```

Root skills carry `role: root` and the chain's `end_output` gate. Loop skills carry
`role: loop` and the contract (`max_iter`, `exit`, `checkpoint`) and no content.

### P7 — Trigger declaration (machine-readable)

This is what makes skills get *invoked* instead of *noticed*. The model no longer has to
remember the pool; the router matches on data.

```yaml
triggers:
  any: [research-process, academic-research, grounded-citations]
  count_gte: 3               # a combination of N in-chain skills arms the loop
  keywords: [research, cite, sources, report]
```

Scoring, as implemented and tested in `router.py`:

| Signal | Points |
|---|---|
| Primary domain noun or multi-word phrase hit | +2 each |
| Secondary keyword hit + word-stem normalization | +1 each |
| in-chain skill already invoked | +2 each |
| `count_gte` met **and** at least one hit | +3 once |

Bands: >=6 → 0.95 confidence, >=3 → 0.75, >=1 → 0.55, no match → fallback at 0.0.
Rationale: Turn-0 prompts can reach high confidence (>=0.75) purely from specific domain queries (e.g. "write a cited competitor report" scores 4 points -> 0.75), while in-chain skills loaded mid-session escalate confidence up to 0.95.

### P8 — Loop contract

A loop node is a procedure with an exit predicate — not a vibe.

```yaml
loop_params:
  max_iter: 6
  exit: "claims_cited == claims_total"
  checkpoint: .lucky/ledger-research.jsonl
```

`exit` must be **computable from artifacts on disk**, never from self-assessment.
`checkpoint` is append-only JSONL: `{iter, node, action, result, ts}`.

---

## Part 3 — Node grammar (the structural change)

```
        ┌─────────┐   ┌──────────────────────────┐   ┌───────────────┐   ┌──────────┐
        │  START  │──▶│        PRE_LOOP          │──▶│     LOOP      │──▶│   END    │
        │  once   │   │  once — converge + lock  │   │  repeat body │   │  once    │
        │ 1-2     │   │  2-4 nodes               │   │  1-3 nodes    │   │  1-2     │
        └─────────┘   └──────────────────────────┘   └───────────────┘   └──────────┘
             ▲                     │                        │                  │
             │                     └── exit criterion ──────┘                  │
             └──────────────── end_output gate decides root done ──────────────┘
```

**Rule 1 — pre_loop runs once.** Work that converges the question (framing, discovery,
triage, scope lock, repo map, threat model) belongs there. If it repeats, it drifts and it
burns the turn budget.

**Rule 2 — only the loop repeats.** The loop body must be thin enough to finish in one turn.
Two nodes is the practical ceiling; three is the limit.

**Rule 3 — the end node owns the gate.** It emits the artifact and checks it. If the gate
fails, the root is **not done** and the loop resumes. "Done" is never a sentence.

**Rule 4 — one node at a time.** The router names the chain; the agent loads one card, not
the chain. Loading the whole chain defeats the token budget it exists to enforce.

---

## Part 4 — The 9-gate compliance checklist

Ship no skill that fails any gate.

| # | Gate | Check |
|---|---|---|
| 1 | Size | `SKILL.md` <= 10 KB; bulk in `references/` |
| 2 | Trigger | description <= 57 chars, starts with a trigger, no marketing |
| 3 | Node budget | if `role: segment`, card <= 350 tokens |
| 4 | Thinking | mechanical work declares the lowest reasoning budget that is correct |
| 5 | Output | deterministic JSON schema (response_format / GBNF / XGrammar) enforced at sampler, never plain-text pleas |
| 6 | Tools | no HTML scraping via shell when a native search/extract tool exists |
| 7 | Role | `role`, `chain`, `phase` declared in frontmatter |
| 8 | Triggers | `triggers.any` / `count_gte` present on every root and loop |
| 9 | End state | `end_output` gate is computable from disk; loop has `max_iter` + `exit` |

Gates 3, 7, 8, 9 are machine-checkable. `test_router.py` already enforces 3, 7, 8, 9 for the
nodes in this project; extending it to the whole pool is Phase 3.

---

## Part 5 — Templates

### Segment card (<=350 tokens, fixed skeleton)

```md
# <id> — <PHASE>

**Purpose** — one sentence: what state this moves the chain out of.

## Do
1. Four to six numbered imperatives. Exact paths, exact commands.
2. No rationale prose. Rationale belongs in BOOST or the chain map.

## Gate
One binary condition. If it cannot be checked, it is not a gate.

## Output
```<format>```
```

### Root skill

```md
# R-<NAME>

**Goal** — one sentence.
**End output** — artifact path + the exact validation command that proves it.
**Chain** — start -> pre_loop -> loop -> end.
**Loop** — exit predicate, max_iter.
**Not done if** — the three ways this is falsely declared complete.
```

---

## Part 6 — Executing on a weak model (Two-Zone Prefix-Safe Injection)

Chains must survive a fallback to a sub-30B local SLM (e.g. 3B–14B GGUF via llama.cpp / Ollama).
Per `SLM Token Reduction vs. Recall` (§7.1–7.2), mutating the top system prompt prefix across node transitions invalidates the llama.cpp server prefix KV cache (`--cache-reuse`).

Orchestration is therefore structured for **Two-Zone Prefix-Safe Injection**:
- **Zone 1 (Static Prefix — Immutable Across All Steps)**: `SOUL.md` + `_DISPATCH.md` + the 117-token ROOT chain header (`router.py --pack`), pinned inside the first 32+ attention sink tokens (`--tri-keep-first 32`). Reused across 100% of turns without cache eviction.
- **Zone 2 (Dynamic Step Tail — Appended at End of Turn)**: The active 147-token `segments/S-<node>.md` card + Layer 1 memory subgraph (`engine.py --format prompt`), placed immediately before the current step instruction so llama.cpp reuses 100% of the KV cache for Zone 1 and prior conversation turns.

Furthermore, plain-text formatting pleas fail on 3B–14B models. The node output contract must be enforced at the local sampler via JSON schema (`response_format` / GBNF grammar):

```json
{
  "type": "object",
  "properties": {
    "node": {"type": "string"},
    "gate_passed": {"type": "boolean"},
    "gate_reason": {"type": "string"},
    "output": {"type": "string"}
  },
  "required": ["node", "gate_passed", "gate_reason", "output"]
}
```

A frontier model receives the context pack and may run `start -> pre_loop -> end` in fewer turns, stopping only when a gateway predicate requires iteration. Same node cards, different orchestration — that is the multimodal-readiness requirement satisfied structurally.

---

## Part 7 — What /boost 1.5 is not

- Not a rewrite of your skills. Spec only until you approve per-skill patches.
- Not a model router. Picking a model is a separate concern from picking a chain.
- Not an embedding system. Keyword + count matching on 5 roots costs nothing and is auditable;
  revisit past ~15 roots.
