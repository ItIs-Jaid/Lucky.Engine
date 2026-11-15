# CHAIN-MAP — roots, nodes, triggers

Every root below is justified by an observed co-occurrence pattern in `state.db`, not by taste.
Source: 1,076 sessions, skill loads per session.

## Why these five roots

| Root | Observed pair | Sessions |
|---|---|---|
| R-RESEARCH-SYNTHESIS | research-process + subagent-delegation | 13 |
| | academic-research + research-process | 10 |
| | grounded-citations + research-process | 7 |
| | academic-research + reference-compilation | 7 |
| R-DELEGATED-BUILD | subagent-delegation + subagent-driven-development | 13 |
| | agentic-teams + subagent-delegation | 12 |
| | superpowers:brainstorming + subagent-driven-development | 8 |
| R-MOVE-DECISION | relocation-planning + subagent-delegation | 7 |
| | relocation-logistics + relocation-planning | 5 |
| | apartment-hunting + rental-listing-verification | 5 |
| R-SECURITY-POSTURE | host-security-monitoring + identity-monitoring | 5 |
| | cyber-defense-tools + hermes-agent | 4 |
| R-SKILL-SYSTEM | hermes-agent + hermes-agent-skill-authoring | 5 |
| | ponytail + ponytail-review | 5 |

`R-GENERIC-TASK` (fallback) exists so an unmatched task never guesses. It is minimal by design:
1 start, 1 pre_loop, 1 loop, 1 end — and its gate is "single next action with owner and deadline".

---

## Node tables

### R-RESEARCH-SYNTHESIS -> report.md
| Phase | Node | Token est | Gate |
|---|---|---|---|
| start | S-context-pack | 131 | pack <=350 tok, zero background prose |
| pre_loop | S-question-frame | 96 | answerable + stopping rule |
| pre_loop | S-source-discovery | 92 | pool >=10, incl. one contrarian |
| pre_loop | S-source-triage | 147 | every kept url verified this session |
| loop | S-claim-extract | 96 | one claim per sentence, typed, sourced |
| loop | S-cite-verify | 136 | `claims_cited == claims_total` |
| end | S-synthesis | 128 | artifact on disk + falsifier named |

Loop: `L-EVIDENCE-LOOP`, max_iter 6.
End gate: **every claim maps to a resolvable url or file path.**

### R-DELEGATED-BUILD -> change-set
| Phase | Node | Gate |
|---|---|---|
| start | S-context-pack | context only, no plan prose |
| pre_loop | S-scope-lock | one failing test exists for the right reason |
| pre_loop | S-repo-map | call sites enumerated, invariant written |
| pre_loop | S-test-first | real red output captured |
| loop | S-slice-build | suite green, output pasted |
| loop | S-review-slice | diff reviewed, no deferred findings |
| end | S-gate-verify | full suite + skipped list + risk |

Loop: `L-BUILD-LOOP`, max_iter 4. End gate: **tests pass, lint clean, ponytail review attached.**

### R-MOVE-DECISION -> decision-brief.md
| Phase | Node | Gate |
|---|---|---|
| start | S-context-pack | budget ceiling stated |
| pre_loop | S-criteria-lock | hard filters numeric/binary |
| pre_loop | S-market-scan | >=8 live listings + median |
| loop | S-listing-verify | `verified == candidates` |
| loop | S-cost-model | annual total per survivor |
| end | S-decision | pick + runner-up + switch condition |

Gate: **every listing verified by live url with price and date.**

### R-SKILL-SYSTEM -> SKILL.md
| Phase | Node | Gate |
|---|---|---|
| start | S-context-pack | overlap candidate named |
| pre_loop | S-skill-audit | decision: patch / merge / create |
| pre_loop | S-skill-draft | executable with zero guesses |
| loop | S-skill-test | loads via skill_view, step 1 runs clean |
| loop | S-boost-gate | 9/9 gates |
| end | S-synthesis | artifact on disk |

Gate: **9-gate checklist passes and the skill loads in a live session.**

### R-SECURITY-POSTURE -> posture-review.md
| Phase | Node | Gate |
|---|---|---|
| start | S-context-pack | crown jewels in one line |
| pre_loop | S-asset-scope | owner + exposure per asset |
| pre_loop | S-threat-model | >=2 written paths per crown jewel |
| loop | S-detection-gap | gaps ranked, each with evidence |
| end | S-report | every row: asset, evidence, owner |

Gate: **every gap has asset, evidence, and owner.**

### R-GENERIC-TASK (fallback) -> task-outcome.md
| Phase | Node | Gate |
|---|---|---|
| start | S-context-pack | context only, <=350 tok |
| pre_loop | S-scope-lock | single target outcome locked |
| loop | S-slice-build | verification command exits 0 |
| end | S-synthesis | artifact on disk + single next action with owner and deadline |

Gate: **single next action with owner and deadline.**

---

## Trigger table (what actually arms a loop)

| Chain | `any:` skills | `count_gte` | Keywords |
|---|---|---|---|
| research-synthesis | research-process, academic-research, grounded-citations, reference-compilation | 3 | research, cite, citation, sources, report, literature, survey |
| delegated-build | subagent-delegation, subagent-driven-development, agentic-teams, multi-tier-agentic-build | 3 | build, implement, refactor, feature, fix, code, test |
| move-and-relocate | relocation-planning, relocation-logistics, apartment-hunting, rental-listing-verification, transit-commute-rental-search | 3 | move, relocate, apartment, rent, city, neighborhood, region, relocation, lease, commute |
| skill-forging | hermes-agent, hermes-agent-skill-authoring, agent-skill-management, boost, cli-reference | 3 | skill, skills, agent, hermes, prompt, boost, chain, router |
| security-review | host-security-monitoring, identity-monitoring, cyber-defense-tools, oss-forensics, cisa-kev-briefing | 3 | security, defend, monitor, threat, vuln, harden, incident |

`count_gte: 3` is the answer to "if a certain number or combination of skills is called".
Semantics, verified by test: each matched skill +2, gate +3 once, so the third in-chain skill
is worth +5 and reliably outranks a single keyword hit.

---

## Adding a sixth root

1. Find the co-occurrence pair in `state.db`. No evidence, no root.
2. Write 3 pre_loop nodes that converge the question. If you cannot name three, it is a node
   in an existing chain, not a root.
3. Pick an end artifact whose gate is a **command**, not an opinion.
4. Add 2 tests: one positive routing case, one negative (wrong task must not match).
5. `python test_router.py` must stay green before the root is considered real.
