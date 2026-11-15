# ANALYSIS — what the session history actually says

Measured read-only from the local agent `state.db` on 2026-10-19.
1,076 sessions · 55,231 messages · 28,951 tool calls.

## 1. Surface and spend

| Metric | Value |
|---|---|
| Sessions by source | desktop **980**, cron 79, cli 14, kanban 2 |
| Lifetime estimated spend | **$46.13** |
| Tokens | in 192.8M · out 20.3M · reasoning 7.8M |
| Avg tool calls / session | 27 |

**Read:** this is a desktop-first, single-operator environment running on cheap and free
model tiers. Any design that assumes paid frontier reasoning or a cloud browser is wrong here.

## 2. Tool reality (top 10 of 53)

| Calls | Tool | Note |
|---|---|---|
| 9,687 | `terminal` | 33% of everything. The shell is the primary interface |
| 4,351 | `read_file` | file-native work, not scraping |
| 3,808 | `web_search` | heavy search, shallow extraction (932 `web_extract`) |
| 2,076 | `write_file` | |
| 1,871 | `patch` | surgical edits preferred over rewrites |
| 1,848 | `execute_code` | |
| 1,216 | `skill_view` | only 4.2% of calls touch a skill |
| 525 | `delegate_task` | |
| 104 | `browser_exec` | browser path is effectively dead here |
| 177 | `clarify` | you do answer questions — use them |

**Read:** /boost Pillar 4 in `02-boost-skill-optimization-blueprint.md` targeted cloud google-genai server-side tools (`google_search`, `url_context`, `code_execution`), whereas on the local Hermes host, `terminal` (33% of tool calls) is the primary execution substrate and only shell HTML scraping is prohibited in favor of `web_search`/`web_extract`. Reading, executing, and testing locally through `terminal` is correct and preferred.

## 3. Models

| Sessions | Model | Cost |
|---|---|---|
| 279 | deepseek-v4-flash-0731 | $4.27 |
| 148 | tencent/hy3:free | $0.08 |
| 94 | stealth/space-bunny-alpha | $2.66 |
| 85 | stepfun/step-5-preview:free | $0.00 |
| 40 | deepseek-v4.1-flash | $6.25 |

Fallbacks are free tier (`stepfun/step-3.7-flash:free`, `poolside/laguna-xs-2.1:free`).
`agent.max_turns: 15`, `reasoning_effort: low`.

**Read:** chains must survive a model downgrade mid-session. A chain whose nodes assume
frontier reasoning fails on the free fallback. That is why every node card is a procedure
with a gate, not an essay — it is executable by the smallest model in the fallback list.

## 4. Findings

**F1 — Skills are under-invoked.** 216 of 261 indexed skills have been loaded at least once;
~45 never. 409 sessions loaded a skill, 220 loaded 2+, only 127 loaded 3+.

**F2 — There is no routing layer.** Chain selection is emergent, so the same patterns get
re-derived. Observed pairs: research-process+subagent-delegation (13), subagent-delegation+
subagent-driven-development (13), agentic-teams+subagent-delegation (12), academic-research+
research-process (10), brainstorming+subagent-driven-development (8), academic-research+
reference-compilation (7), grounded-citations+research-process (7), relocation-move+
subagent-delegation (7), apartment-hunting+rental-listing-research (5), target-move+
origin-move (7), ponytail+ponytail-review (5), sentinel-ops+sentinel-monitoring (5).

Those twelve pairs are the empirical justification for the five roots in `chains.yaml`.

**F3 — The skill index is the tax you pay every turn.** `.skills_prompt_snapshot.json` is
194 KB for 261 skills; 262 SKILL.md files total 1.86 MB. The index is paid on every session
whether or not a skill runs. Coverage is 82% and falling as the pool grows, so growth without
routing makes the tax worse, not better.

**F4 — Skill hygiene: a venv lives inside the skills dir.**
`AppData/Local/hermes/skills/uv/tools/graphifyy/.../SKILL.md` (41.8 KB) is an installed
package tree, which is why there are 306 skill *directories* but 262 real skills.
`skills/graphify/SKILL.md` is also 43 KB, far over the 10 KB boost ceiling.

**F5 — Environment is terminal + files + search.** Working dirs cluster on skill-registry-repo (64),
cloud-archive worktrees (84), agentic-DevSecLocHostOps (91), LuckyChat (17),
web-client (16), local-home-workspace. Resume-worthy work already lives in agentic + DevSec + local
ops — 1.5.0 continues that line rather than inventing a new one.

**F6 — Model churn is normal.** 40+ distinct models. Routing must be model-agnostic and
deterministic or it will break on every switch.

## 5. Optimization opportunities, ranked by real payoff

| # | Move | Why it pays | Cost |
|---|---|---|---|
| O1 | Router pre-pass (this project) | skills get named instead of noticed; 117-token pack vs 3-4 files | built |
| O2 | Split pre-loop from loop | stop re-running convergence work; fewer max-turns deaths | built |
| O3 | End-state gate per root | "done" becomes a validated artifact, kills false completion | built |
| O4 | Prune/merge the never-loaded skills | cuts the 194 KB per-turn index and a 306-dir tree | needs your yes |
| O5 | Quarantine `skills/uv/**` | removes 41.8 KB of package tree from the index | needs your yes |
| O6 | Fit triggers against history | turns hand-guessed keywords into measured precision | Phase 4 |
| O7 | Ledger-driven resume | `.lucky/ledger-*.jsonl` lets a cron or a fresh session pick up mid-loop | built into contract, not yet wired |

## 6. What I rejected (and why)

- **A vector/embedding router.** Adds a dependency, a model, and latency to solve a matching
  problem that keywords + counts solve at zero cost on 5-6 roots. Revisit only if root count
  passes ~15.
- **Rewriting `/boost` P1-P5.** They are sound. 1.5.0 adds P6-P8 and leaves the originals intact.
- **Auto-editing skills.** Your `skills/` tree is a read-only convention. Patching 12 skills
  without approval would break the SSOT/mirror model. Spec only, until you say go.
- **YAML dependencies.** A 40-line subset parser beats a pip install for a config this small.
