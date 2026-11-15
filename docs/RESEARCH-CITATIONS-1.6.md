# Lucky.Engine — Grounded Research, Stochastic Trial-and-Error & Low-Tech Architecture

This document records the scholarly literature (retrieved via OpenAlex and web search), diagnosed system bottlenecks, and novel stdlib-only solutions implemented in **Lucky.Engine** (`router.py`, `chains.yaml`, `bridge/engine.py`, `bandit.py`, `evals/stochastic_ablation.py`).

---

## 1. Grounded Citations (OpenAlex & Scholarly Sources)

1. **Green AI** — Schwartz, Dodge, Smith, Etzioni (2020), *Communications of the ACM* (`cited_by_count: 2142`)
   - OpenAlex: https://openalex.org/W3214897310
   - DOI: https://doi.org/10.1145/3381831
   - **Design Principle**: Prioritize efficiency and low-resource accessibility alongside accuracy rather than scaling compute blindly.

2. **Small Language Models are the Future of Agentic AI** — Belcak et al. (2025) (`cited_by_count: 468`)
   - OpenAlex: https://openalex.org/W4415130727
   - DOI: https://doi.org/10.48550/arxiv.2506.02153
   - **Design Principle**: Most repetitive agentic subtasks can be served by compact local SLMs or deterministic heuristics rather than frontier models.

3. **RouteLLM: Learning to Route LLMs with Preference Data** — Ong et al. (2024) (`cited_by_count: 575`)
   - OpenAlex: https://openalex.org/W4400141368
   - DOI: https://doi.org/10.48550/arxiv.2406.18665
   - **Design Principle**: Dynamic routing between lightweight and heavy capability tiers preserves quality while slashing compute cost.

4. **MasRouter: Learning to Route LLMs for Multi-Agent Systems** (2025), *ACL* (`cited_by_count: 114`)
   - OpenAlex: https://openalex.org/W4412945204
   - DOI: https://doi.org/10.18653/v1/2025.acl-long.757
   - **Design Principle**: Cost-aware multi-agent routing conditioned on task/role context.

5. **HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models** — Jiménez Gutiérrez et al. (2024) (`cited_by_count: 438`)
   - OpenAlex: https://openalex.org/W4415797504
   - DOI: https://doi.org/10.52202/079017-1902
   - **Design Principle**: Seeded Personalized PageRank (PPR) over lightweight entity/memory graphs retrieves multi-hop context without heavy vector databases.

6. **Graph Retrieval-Augmented Generation: A Survey** (2025) (`cited_by_count: 720`)
   - OpenAlex: https://openalex.org/W4416379250
   - DOI: https://doi.org/10.1145/3777378
   - **Design Principle**: Structural graph traversal reduces noisy context-window dumps.

7. **A Survey of Context Engineering for Large Language Models** (2025) (`cited_by_count: 288`)
   - OpenAlex: https://openalex.org/W4417423726
   - DOI: https://doi.org/10.48550/arxiv.2507.13334
   - **Design Principle**: Compact, structured context packing outperforms raw prompt dumping.

8. **Reflexion: language agents with verbal reinforcement learning** — Shinn et al. (2023) (`cited_by_count: 3356`)
   - OpenAlex: https://openalex.org/W7133222210
   - DOI: https://doi.org/10.52202/075280-0377
   - **Design Principle**: Verifier-gated trial-and-error feedback converts execution failures into structured corrective signal.

---

## 2. Novel Low-Tech Implementation (100% Python Stdlib, CPU-Only)

1. **Deterministic Router Accuracy Fix (`router.py`, `chains.yaml`)**:
   - Added inflection/plural normalization (`threat`/`threats`, `gap`/`gaps`, `vuln`/`vulnerabilities`, `debug`, `outage`, `error`, `incident`) and domain phrases (`posture report`, `security gaps`, `production outage`).
   - Result on `evals/routing.py`: **`0.79 (11/14)` -> `1.00 (14/14)`**; `security-review` F1 improved from `0.00` to `1.00`.

2. **Pure-Stdlib Personalized PageRank Lite (`bridge/engine.py: ppr_rank`)**:
   - Implements 10-iteration sparse power-iteration PPR over `graph.edges`, `graph.hyperedges`, and `bridge_edges.json` with zero external libraries (`no networkx`, `no numpy`).
   - Replaces flat `0.6` edge-expansion confidence with PPR-normalized structural scores in `[0.55, 0.79]`.

3. **Stochastic Trial-and-Error Bandit Engine (`bandit.py`)**:
   - Contextual **UCB1** and **Beta Thompson Sampling** across 4 compute-ordered arms (`heuristic_fast` [0 tok], `slm_compact` [60 tok], `slm_ppr` [120 tok], `escalate_hitl` [240 tok]).
   - Cost-aware verifier reward: `1.0 - 0.35 * (tokens_est / budget)` on disk-verified pass, `0.0` on fail.
   - `run_trial_and_error()` tries the lowest-cost promising arm first and escalates within `max_attempts` only if the deterministic verifier fails.

---

## 3. Measured Ablation Results (`python evals/stochastic_ablation.py`)

Evaluated over 12 benchmark task categories x 10 rounds (120 runs, deterministic seed `42`, pure CPU):

| Policy | Pass Rate | Avg Est. Tokens | Total Est. Tokens | Elapsed (ms) |
|---|---:|---:|---:|---:|
| `always_heavy` | 1.0000 | 240.00 | 28,800 | 371.32 |
| `random_arm` | 0.8833 | 95.50 | 11,460 | 338.38 |
| `ucb1_bandit` | 0.9833 | 94.50 | 11,340 | 312.02 |
| `thompson_bandit` | **0.9917** | **62.50** | **7,500** | **283.88** |

*Note: Per `ETHOS.md`, token counts above are `chars/4` / tier estimates in a deterministic simulation, not hardware energy/water measurements.*
