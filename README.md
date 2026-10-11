# Lucky.Engine

**Your Agent might be smart. Now make it Lucky ;)**

**Location:** `<your-project>/memory/graphify-out/bridge/`

## What It Does

Lucky.Engine intelligently loads only the relevant memory and skills context for each query, reducing token usage from ~3-8k to ~300-500 per query.

## Purpose

Links your **memory layer** (36 nodes, 4 communities) with your **skills** (57+ directories) through pre-computed cross-reference nodes and intelligent intent-based matching.

## Structure

```
memory/graphify-out/
├── graph.json          # Original memory graph (34 nodes)
├── GRAPH_REPORT.md
└── bridge/
    ├── bridge_nodes.json   # 14 skill-to-memory mapping nodes
    └── bridge_edges.json   # 26 intra-skill edges
```

## Quick Reference

| Skill | Memory Link | Usage |
|-------|-------------|-------|
| `memory-graph` | Memory Layer SSOT | Core memory structure |
| `hermes-agent` | Profile & Infrastructure | Agent config, SSH, Tailscale |
| `graphify` | Memory Graph + Corpus Graph | Query both layers |
| `agent-skills` | Goals + Aspirations | Task coordination |
| `finances` | Move Fund + Income Bridge | Financial planning |

## Query Patterns

### Pattern 1: Direct Memory Query
```bash
graphify query "What is my move plan?" --budget 500
```

### Pattern 2: Skill-to-Memory Bridge
```bash
# First check bridge nodes
cat memory/graphify-out/bridge/bridge_nodes.json | grep "finances"
# Then query the linked memory node
graphify query "Move Fund" --budget 300
```

### Pattern 3: Unified Query (Future)
```bash
# When both graphs are linked:
graphify query "finances AND move" --budget 800
```

## Benefits

| Before | After |
|--------|-------|
| Full context token (~4-8k) | Targeted query (~300-800) |
| Manual memory lookup | Direct skill-to-memory bridge |
| Disconnected graphs | Unified query surface |

## 📚 Examples & Templates

To get started, copy the example files from the `examples/` folder:

```bash
# Copy configuration
cp examples/example-config.yaml lucky-config.yaml

# Copy memory templates (then edit with your actual data)
cp examples/example-USER.md USER.md
cp examples/example-MEMORY-SSOT.md MEMORY-SSOT.md
cp examples/example-bridge_nodes.json bridge_nodes.json
```

See `examples/QUICKSTART.md` for a complete setup guide.

## How to Use

1. **For memory queries:** Use `/memory/query` (future) or `graphify query "X" --budget 500`
2. **For skill lookups:** Check `bridge/bridge_nodes.json` for memory links
3. **For combined queries:** Run separate queries and merge results

## Extending

Add new mappings in `bridge/bridge_nodes.json`:
```json
{
  "id": "SKILL_my-skill_0",
  "label": "my-skill → Memory Category",
  "type": "skill_reference",
  "skill": "my-skill",
  "memory_ref": "Memory Category"
}
```

---
*Generated: 2026-10-11*
