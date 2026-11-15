---
schema_version: 1
name: lucky-engine
created_timestamp: 2026-11-15T07:08:02Z
author: Jaid King (Lucky Kat Org)
owner: Jaid King (Lucky Kat Org)
---

# Lucky.Engine — ETHOS.md

**Schema — what this engine is for, how it decides, and how success is measured.** Read before changing chain grammar, gateway predicates, or routing weights.

## Role

A deterministic, zero-token chain router and phase-gated workflow engine: it turns a task into a root goal, an ordered node plan, and a loop contract with an explicit end gate, dispatching skills and local SLM/database work without spending a model call on the decision.

## Purpose & Outcomes

- **Mission:** Make skill and agent dispatch deterministic and free of model guesswork, so automated background work costs no tokens and the compute that remains goes to capability instead of routing. Lower compute cost without lowering intelligence.
- **Outcome:** Every task resolves to a chain with an explicit exit predicate and end gate, judged by a gateway against disk state — with the 316 executable engine gates passing. Success is measured in real power/water footprint per automated task, not token counts alone. Accountable owner: Jaid King.
- **Long horizon:** Frontier-level agentic capability running on local, sustainable, recycled hardware instead of data-center-scale growth.

## Scope

- **Audience:** Jaid, plus any Lucky Kat agent or project that needs routing or an on-device inference substrate.
- **In-scope task categories:**
  1. Task-to-chain routing and context packing (`router.py`, `chains.yaml`).
  2. Chain phase grammar: `start` once, `pre_loop` once, `loop` repeats, `end` once.
  3. Gateway judgment, point budget, urgency tiers, escalation (`gateway.py`).
  4. Deterministic artifact verification from disk.
  5. Memory/skill subgraph retrieval (Layer 1 bridge) feeding the pack.
  6. Publication gate for the sanitized public slice (`check_public.py`).
- **Out-of-scope for now (not on principle):** acting as a cloud inference provider; billing or quota products; model training/fine-tuning; end-user GUI; multi-tenant SaaS.

## Tools

- **`chains.yaml`** — chain specs, judged loops, gateways, urgency tiers; the config.
- **`router.py`** — stdlib-only resolver and context packer; no `subprocess`, no network.
- **`gateway.py`** — urgency-tiered ledger and deterministic artifact verifier.
- **`segments/*.md`** — 26 node cards, one job each, ≤350 tokens (max 147 today).
- **`check_public.py` / `test_public.py`** — publication leak gate and its proof.
- **Layer 1 bridge** (`memory/graphify-out/bridge/`: `engine.py`, `graph.json`, `bridge_nodes.json`) — memory & skill subgraph retrieval.
- **Local inference when genuinely needed:** Ollama `:11434`, LM Studio `:1234`, Jan `:1337`. Never a remote provider by default; a missing key falls back to deterministic keyword intent rather than failing open to a cloud.

## Harness

A deterministic pre-pass runs before the model: task → root goal → ordered node plan → loop contract, at zero token cost. Each loop is judged by a gateway using a deterministic predicate computed from disk or ledger state; `pass` advances/delivers/redirects, `fail` pushes back, redirects, or asks a human (`hitl`). Loops charge `max(1, power + attempts)` against a point budget. The whole engine is local stdlib Python with 316 executable gates as its regression contract — run them, don't trust the README.

## Behavior

- **No model call in routing.** Determinism is the contract: same input, same chain, same pack.
- **No network, no subprocess** inside the router; it never reaches out to decide.
- **Gateways decide, not vibes.** A chain changes direction only at a gateway, and "done" means an artifact verified on disk.
- **Escalate instead of guessing** when a predicate cannot be satisfied: `pushback` → `redirect` → `hitl`.
- **Never leak identifiers** into the public slice; `check_public.py` must be CLEAN before publication.
- **Report blocked as blocked.** Items deferred for toolchain/roster reasons are recorded, not described as shipped.
- **Ponytail applies:** shortest working diff, no unasked-for abstraction, never cut validation or error handling.

## Principles

1. **Lower compute cost without sacrificing intelligence or capability.** Sustainability is the objective; being merely cheap is a failure, and being clever at the cost of capability is worse.
2. **For automation, sustainable first, then free.** Zero-token background work is the target, but only in a form that does not shift the cost onto cloud calls, new hardware, or heat.
3. **No "route your inference to us" provider play.** The architecture couples to a local on-device database (retrieval + memory) so capability is preserved without offloading compute to a vendor and without exploiting people's reluctance to route inference.
4. **Determinism outranks confidence.** A predicate computed from disk beats any assertion of success — including the engine's own.

## Success Criteria

1. Zero tokens spent on routing and background automation; identical input yields identical output.
2. Every chain ends at a disk-verified artifact or an explicit not-done at a gateway — never a confident sentence.
3. All 316 gates pass (`test_router.py` 142, `test_gateway.py` 174) and `test_public.py` passes with `check_public.py` CLEAN.
4. Node cards stay under the 350-token budget; context packs stay in the ~120-token range.
5. Design decisions run on hardware already owned (workstation, OptiPlex/HP i3, Pixel 9, recycled tech) — no new hardware required by design.

## Trade-offs

- **Hard gates, never traded:** local-only operation; determinism; artifact verification at the gateway; clean publication gate.
- **Priority order when they conflict:** sustainability (compute, heat, water) → capability preservation → latency → developer convenience.
- **Unacceptable compromises:** trading determinism for convenience; spending tokens to avoid engineering effort; designing for new hardware when existing hardware can serve; shifting cost into a cloud provider.

## Constraints

- Local-only, stdlib-only engine; no network, no `subprocess`, no remote inference by default.
- $0 recurring spend; no paid provider required to route or verify.
- Must run on existing/recycled devices already in the mesh, not on provisioned cloud capacity.
- Public slice must pass `check_public.py` before it is published.
- Only runtime action needing human sign-off is a gateway `hitl` escalation; no other external side effects.

## Evaluation Setup

- `python test_router.py` → 142 PASS; `python test_gateway.py` → 174 PASS; `python test_public.py` → PASS; `check_public.py --path public/` → CLEAN.
- Integrity manifest with per-file md5 in `FRAMEWORK.md` (Layers 1 and 2) so a reviewer can confirm the SSOT without duplicating files.
- **Coverage gaps:** no instrumented energy, heat, or water metric yet — the sustainability claim is currently argued from token/compute counts, not measured; no automated test of the SLM intent path against a live local model.

## Metric Semantics

- **"token cost"** is one of three proxies for compute cost — track token use, API calls, and device battery usage together. None of them is energy, heat, or water, and no power/heat/water instrumentation exists yet; do not present token savings as a sustainability measurement.
- **"context pack 117 tokens"** is an estimate (chars/4), not a tokenizer count.
- **"gate"** means a deterministic predicate computed from disk or ledger state — it never means an LLM judgment.
- **"verified"** means the executable tests ran and passed, not that the README says so.

## Vision

Be the substrate that powers an on-device SLM for **every future Lucky Kat project**, and run as the backend for low-compute, low-heat generation (solar, wind and other constrained supplies). The end-state architecture is sustainable local computing that is **not** warehouse-scale data centers, but the mesh of everyday devices already in use — tethered together with recycled tech.

## Open Questions

- No energy/heat/water instrumentation exists; the sustainability outcome is not yet measurable.
- The multi-device mesh backend (tethering recycled hardware into one compute fabric) is unbuilt and undesigned.
- The LLM intent path needs `LUCKY_LLM_API_URL` / `LUCKY_LLM_API_KEY` and silently falls back to keyword intent when absent — intent quality without a local model is unmeasured.
