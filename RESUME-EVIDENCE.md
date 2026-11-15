# RESUME-EVIDENCE — Lucky.Engine 1.5.0

Framing: agentic infrastructure + MLDevSecOps. Every claim below points at a file in this
folder you can open, or a command you can re-run. No invented metrics.

## One-liners (safe to put on a resume, all verifiable)

- Built a deterministic, zero-dependency **task-to-chain router** that maps a natural-language
  task onto a root goal, an ordered 4-phase node plan, and a loop contract in one pass with no
  LLM call and no network access.
- Designed a **phase-separated agent chain grammar** (start / pre_loop / loop / end) that fixes
  two recurring agent failure modes: repeated convergence work and false completion.
- Authored **26 token-budgeted node cards (<=147 tokens each)** so the same chain runs on a
  frontier model and on a free-tier fallback by swapping orchestration, not content.
- Wrote a **316-gate executable test suite** (142 router gates + 174 gateway gates, plus 14 publication scanner gates) over routing semantics, phase invariants, token budgets, disk determinism, and CLI behaviour — and used it to catch a real scoring bug.
- Mined **1,076 sessions / 28,951 tool calls** from the operator's own telemetry to derive
  routing roots from observed co-occurrence instead of intuition.

## Metrics with provenance

| Claim | Value | How to reproduce |
|---|---|---|
| Sessions analysed | 1,076 | `state.db`, read-only |
| Tool calls analysed | 28,951 | same |
| Distinct chains shipped | 6 (5 roots + fallback) | `chains.yaml` |
| Node cards | 26, max 147 tok | `ls segments/`, test gate 3 |
| Test gates | 316 pass / 0 fail | `python test_router.py` (142), `python test_gateway.py` (174) |
| Context pack size | 117 tokens | `python router.py --task ... --pack` |
| Router dependencies | 0 (stdlib only) | test gate 7 |
| Never-loaded skills identified | ~45 of 261 | `ANALYSIS.md` F1 |
| Skill index tax | 194 KB / 261 skills | `.skills_prompt_snapshot.json` |

## MLDevSecOps / DevSecOps fit

| Practice | Evidence here |
|---|---|
| Deterministic evaluation | 316 gates across router and gateway, exact expected values, no snapshots |
| Reproducibility | stdlib-only, no network, determinism asserted twice-run |
| Supply-chain hygiene | zero third-party imports by design; venv-in-skills-dir flagged as F4 |
| Provenance | every routing decision carries score + confidence band + source signals |
| Fail-safe defaults | unmatched task -> minimal fallback chain, never a guess |
| Budget enforcement | per-node token ceiling asserted in tests, not documented |
| Auditability | `chains.yaml` readable by a human reviewer; ledgers are append-only JSONL |

## Interview-ready narrative (60 seconds)

> "My agent had 261 skills and no dispatcher, so selection was emergent. I instrumented the
> session store, found that only 127 of 1,076 sessions ever loaded three skills together, and
> about 45 skills had never fired at all. I replaced 'hope the model notices' with a
> deterministic pre-pass: a router reads a declarative trigger table and returns one root goal,
> a phase-ordered node plan, and a loop contract with a computable exit predicate. The chain
> grammar separates convergence from iteration, because repeated convergence is the actual
> token sink. Every node is a 150-token card with a binary gate, which is what lets the same
> chain degrade gracefully to a free-tier model. I gate the whole thing with 316 executable
> tests across router and gateway — and they caught a scoring bug where the third skill in a combination was worth five
> points, not three, which is exactly why I test the router rather than trusting it."

## Gaps to close before this is senior-level work

1. **Live integration.** No hook yet; it is a CLI. Wiring it to task start is the credibility step.
2. **Measured precision.** Trigger keywords are hand-authored. Fitting against 200 historical
   tasks and reporting precision ≥0.8 converts "designed" into "evaluated".
3. **Ablation.** Run the same 20 tasks with and without the router and publish tokens + turns
   + completion rate. That is the number a hiring manager actually wants.
4. **Publication.** A sanitized skeleton (placeholder paths, no personal identifiers) turns this
   from a local artifact into a portfolio piece.

## What not to claim

- Do not claim production scale, multi-tenant use, or team adoption. It is single-operator.
- Do not claim the router improves outcomes yet — that is the Phase 2/4 measurement, not a result.
- Do not claim DevSecOps ownership from this alone; it is the *practice* (gates, budgets,
  provenance, fail-safe defaults) applied to an agent system, which is a fair and specific claim.
