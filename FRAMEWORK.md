---
tags: [projects, lucky-engine, framework, ssot, manifest]
created: 2026-10-19
updated: 2026-10-19
aliases: [Lucky.Engine Framework Manifest, Framework SSOT]
---

# Lucky.Engine 1.5.0 — Framework Manifest (SSOT)

> The framework consists of two distinct architectural layers: Layer 1 (Memory & Skill Subgraph Retriever in `memory/graphify-out/bridge/`, git branch `lucky/fixes`) and Layer 2 (Phase-Gated Workflow & Chain Router in `projects/lucky-engine-1.5.0/`). This note is the verification manifest so reviewers can confirm integrity without duplicating private files.

## Layer 1 — Memory & Skill Subgraph Retriever (`memory/graphify-out/bridge/`)

| file | md5 | role |
|---|---|---|
| `engine.py` | `a1d75a5dc7095dbfbe39ed2316113f39` | Graph-bridged memory & skill context retriever (`graph.json` + `bridge_nodes.json`) |
| `test_suite.py` | `14a764dd5c15f027a375eeaa465a260a` | Core retrieval integration suite (4/4 tests + 19/19 unit tests, 25 eval queries; 59.04%–79.67% token reduction on 34-node memory graph, 79% on 7-node fixture) |
| `lucky-config.yaml` | `1acbb34f51209ba7c76f957e86a42881` | bridge config (memory + skills linking) |
| `bridge_nodes.json` | `1ffd0d3595cd0edfd1956446e87d4d65` | pre-linked skill↔memory bridge nodes |
| `lucky-audit.md` | `bbaca5184d44a5791dfa15e56f9ef91d` | audit narrative |

Verify Layer 1: `md5sum memory/graphify-out/bridge/{engine.py,test_suite.py,lucky-config.yaml,bridge_nodes.json,lucky-audit.md}`

## Layer 2 — Phase-Gated Workflow & Chain Router (`projects/lucky-engine-1.5.0/`)

| file | md5 | role |
|---|---|---|
| `chains.yaml` | `e4537d93cd999480ac23c90f164255a1` | Chain specifications, urgency tiers, loops & gateway configurations |
| `router.py` | `e457d03f30f46914fd9d4fad3924e0fa` | Deterministic task-to-chain router and context packer |
| `gateway.py` | `ee968c80faaf8ba95442070913fe18b1` | Gateway judgment engine, ledger point accounting & artifact validator |
| `check_public.py` | `333e30a7d7ff3aac19718c3ca86553dd` | Privacy and sanitization leak scanner |
| `test_router.py` | `50fcadf23808797cfad61278207c1e61` | Test suite for chain router and node budgeting |
| `test_gateway.py` | `bef300e3d4eb2375d42fbc82ce525e45` | Test suite for gateway judgment and urgency limits |
| `test_public.py` | `bcd1736527be3ad4a90c3e3235ae2f39` | Test suite for public catalog integrity and sanitization |

Verify Layer 2: `md5sum chains.yaml router.py gateway.py check_public.py test_router.py test_gateway.py test_public.py`

## Public mirror (sanitized for GitHub)

`projects/lucky-engine-1.5.0/public_bench/bridge/` — paths replaced with placeholders per the memory-graph skill's public-doc sanitization rule. `engine.py` is byte-identical to SSOT; `lucky-audit.md` and `lucky-config.yaml` intentionally differ. `cache.py` exists only in the public mirror.

## Intentionally NOT byte-identical (and why)

- **audit/config** differ by design (real paths vs placeholders) — do not "fix" by copying.
- **bridge_nodes.json** + **test_suite.py** are absent from the public mirror. Add them only if the public repo should carry them (they reference private memory paths; sanitize first).

## Related
- `README.md` — proposal, status, roadmap
- `CHAIN-MAP.md` — the 5 roots + fallback
- `GATEWAY.md` — gateway protocol
