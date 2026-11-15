# PUBLIC-CATALOG — generic, public, publishable

Purpose: when this project goes public, **no skill name, description, or path may carry an
operator identifier**. This file is the bridge: it lists the generic skills that already exist
in public repos, and the rename map from local names to publishable ones.

Rule of thumb: **publish the pattern, never the person.** A skill named after your town, your
employer, your handle, or your machine is a leak, not a feature.

## 1. Verified public sources

| Source | Repo | What it is |
|---|---|---|
| anthropics | https://github.com/anthropics/skills | official Agent Skills reference set |
| obra | https://github.com/obra/superpowers | agentic skills framework for software dev |
| addyosmani | https://github.com/addyosmani/agent-skills | production-grade engineering skills |
| ComposioHQ | https://github.com/ComposioHQ/awesome-claude-skills | curated index |
| VoltAgent | https://github.com/VoltAgent/awesome-agent-skills | large curated index |

Verified 2026-10-19. Star counts intentionally omitted — they go stale and are not evidence.

## 2. Generic skill inventory (safe to publish as-is)

Names below are generic by construction: they describe a task, not a person or a place.

| Group | Skills | Source |
|---|---|---|
| planning | brainstorming, writing-plans, executing-plans, spec-driven-development, context-engineering | superpowers / addyosmani |
| build | test-driven-development, incremental-implementation, systematic-debugging, verification-before-completion | superpowers / addyosmani |
| review | code-review-and-quality, requesting-code-review, receiving-code-review | addyosmani / superpowers |
| vcs | using-git-worktrees, finishing-a-development-branch | superpowers |
| orchestration | dispatching-parallel-agents, subagent-driven-development | superpowers |
| docs | documentation-and-adrs | addyosmani |
| meta | writing-skills, using-superpowers, skill-creator, mcp-builder | superpowers / anthropics |
| quality | webapp-testing | anthropics |
| frontend | artifacts-builder | anthropics |
| design | canvas-design | anthropics |
| documents | docx, pdf, pptx, xlsx | anthropics |
| agent-infra | context-router-maintenance, memory-knowledge-graph, codebase-graph | this project |
| life-ops | relocation-planning, relocation-logistics, rental-listing-verification | this project (genericized) |
| security | host-security-monitoring, identity-monitoring | this project (genericized) |
| product | ecommerce-launch | this project (genericized) |

Machine-readable: `public/catalog.json`.

## 3. Rename map — pattern, not literals

The literal mapping from local names to publishable names **stays in the private ledger**
and is never published, because the left column is itself the leak. What is published is the
transformation rule:

| Local name shape | Publish as | Leak class |
|---|---|---|
| `<product>-engine-maintenance` | `context-router-maintenance` | product codename |
| `<vault>-graph` | `memory-knowledge-graph` | private workspace name |
| `<tool>-fork` | `codebase-graph` | identifies the operator's toolchain |
| `<city>-move-<year>` | `relocation-planning` | location + timeline |
| `<city>-move-<employer>-transfer` | `relocation-logistics` | location + employer |
| `<codename>-monitoring` | `host-security-monitoring` | project codename |
| `<handle>-shop` / `<handle>-*` | `ecommerce-launch` | personal handle |
| anything named after a person, town, employer, or date | `<function>-<object>` | direct identifier |

Rule: if the name would let a stranger find your town, your job, or your account, it is a
leak. Publish the function; file the mapping privately.

## 4. Naming contract

A publishable skill name is `^[a-z][a-z0-9-]{2,40}$` and must pass all four:

1. Describes a **function**, not an owner (`rental-listing-verification`, not `mycity-hunt`).
2. Contains no proper noun: no person, city, employer, product codename, handle.
3. Contains no date, version-of-me, or ordinal that reveals a timeline.
4. Description starts with a trigger and contains no first-person detail.

## 5. Text rules for descriptions and bodies

| Never publish | Instead |
|---|---|
| `C:\Users\<name>\...`, `/home/<name>/...` | `<project>/...` or `$HOME/...` |
| personal email, GitHub handle, phone | `you@example.com`, `<org>` |
| hostnames, tailnet IPs (`100.x.y.z`), MACs | `<host>`, `<tailnet-ip>` |
| employer, school, town, county | `<employer>`, `<region>` |
| dates of birth, deadlines, court dates | `<date>` |
| named family, friends, coworkers | `<person>` |
| API keys, tokens, cookies, session ids | `<redacted>` |

## 6. Publication gate (executable, not advice)

```sh
python check_public.py --path public/        # must exit 0
python check_public.py --path .              # expected to FAIL: internal docs leak
python test_public.py                        # proves the scanner catches real leaks
```

`check_public.py` scans names **and** text. A finding is a hard fail, not a warning, because a
warning gets ignored and a leaked identifier cannot be un-leaked from a git history.

## 7. Order of operations for going public

1. `check_public.py --path public/` -> 0 findings.
2. Copy the seven publishable code/config files (`router.py`, `gateway.py`, `check_public.py`, `chains.yaml`, `test_router.py`, `test_gateway.py`, `test_public.py`), plus `segments/*.md` and `public/catalog.json` into a clean tree. Leave `ANALYSIS.md`,
   `README.md`, `RESUME-EVIDENCE.md`, `test_*.md` artefacts behind — they cite local telemetry.
3. Re-run the gate on the clean tree.
4. `git init` only there. Never publish from inside the private workspace.
5. Add `.gitignore` for `*.log`, `.lucky/`, `segments/*.local.md`.
