# Bridge Pattern for Memory + Skills Queries

**Updated: Lucky.Engine (Hermes Local Context Optimizer)**

## Purpose

Reduce token usage (~3–7k saved per query) by creating a lightweight bridge layer that pre-links skill categories to memory concepts. Instead of loading the full 8,276-node corpus graph, you query the 36-node memory graph + skill mappings (~300–1,300 tokens).

## Components

| File | Purpose |
|------|---------|
| `engine.py` | Lucky.Engine core - intent detection, budget enforcement |
| `lucky-config.yaml` | User settings (token limits, confidence thresholds) |
| `lucky-audit.md` | Human-readable decision log |
| `hermes-ql.sh` | Shell wrapper for CLI access |

## Structure

```
memory/graphify-out/
├── graph.json          # Original memory graph (34 nodes, 4 communities)
├── GRAPH_REPORT.md
└── bridge/
    ├── bridge_nodes.json   # Skill-to-memory mapping nodes (14+ nodes)
    ├── bridge_edges.json   # Intra-skill edges (26+ edges)
    ├── README.md           # Quick reference
    └── query_helper.py     # Unified search tool
```

## How It Works

### 1. Bridge Nodes Format

```json
{
  "id": "SKILL_finance_0",
  "label": "finances → Move Fund",
  "type": "skill_reference",
  "skill": "finances",
  "memory_ref": "Move Fund"
}
```

### 2. Bridge Edges Format

```json
{
  "source": "SKILL_finance_0",
  "target": "SKILL_finance_1",
  "type": "skill_related"
}
```

### 3. Query Patterns

| Goal | Command | Token Cost |
|------|---------|------------|
| Memory-only | `graphify query "X" --budget 500` | ~300–500 |
| Skill+memory | `python query_helper.py "X"` | ~300–500 |
| Full corpus | `graphify query "X"` (no budget cap) | ~3k–8k |

## How to Add a New Mapping

1. **Edit `bridge_nodes.json`**:

```json
{
  "id": "SKILL_newskill_0",
  "label": "newskill → Memory Category",
  "type": "skill_reference",
  "skill": "newskill",
  "memory_ref": "Memory Category"
}
```

2. **Run query helper**:

```bash
cd memory/graphify-out/bridge
python query_helper.py "newskill"
```

## Query Helper Usage

```bash
# Basic search (defaults to 500 tokens)
python query_helper.py "move plan"

# Custom budget
python query_helper.py "finances" --budget 300

# Memory-only
python query_helper.py "hermes config" --memory

# Skills-only
python query_helper.py "graphify" --skills
```

## Current Mappings (As of 2026-10-11)

| Skill | Memory Links |
|-------|--------------|
| `memory-graph` | Memory Layer SSOT, User Mirror, Memory Convention |
| `hermes-agent` | Profile & Infrastructure, SSH Lane, Tailscale |
| `graphify` | Memory Graph, Corpus Graph, Table of Contents |
| `agent-skills` | Goals, Aspirations |
| `finances` | Move Fund, Income Bridge, Liabilities |

## Maintenance

- **Add mappings**: Edit `bridge_nodes.json` directly (no rebuild needed)
- **Remove mappings**: Delete the node, then run query helper
- **Update all mappings**: Use `graphify add <file>` or rebuild the memory graph

## When NOT to Use the Bridge

- **Large queries**: If you need the full corpus (e.g., "all code patterns"), use the full graph
- **Unknown concepts**: If the skill category doesn't exist yet, don't force a mapping

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No matches found" | Check spelling, use partial names (e.g., "move" not "move plan") |
| "Too many results" | Narrow with `--memory` or `--skills` flag |
| "Bridge missing" | Re-run `graphify --update` on the memory directory |
