# Lucky.Engine

**Your Agent might be smart. Now make it Lucky ;)**


> **A Note from the Creator:**
> "I'm trying to vibe my way to more effective local agents. I truly don't understand what exactly I'm building but want to share in case I'm building something of value that could help someone else. Always eager to learn and welcome any feedback :3"

## Table of Contents

- [What It Does](#what-it-does)
- [Quick Start & Installation](#quick-start--installation)
- [Query Patterns](#query-patterns)
- [Performance Benchmarks](#performance-benchmarks)
- [Examples & Templates](#examples--templates)
- [Extending](#extending)

**Location:** `<your-project>/memory/graphify-out/bridge/`

## What It Does

Lucky.Engine intelligently loads only the relevant memory and skills context for each query, reducing token usage from ~3-8k to ~300-500 per query.

## Quick Start & Installation

### Installation Script (Linux/Mac)
```bash
./install.sh
```

### Manual Setup (Windows)
1. Clone the repository
2. Copy example files:
```powershell
Copy-Item examples\example-config.yaml .\lucky-config.yaml
Copy-Item examples\example-USER.md .\USER.md
Copy-Item examples\example-MEMORY-SSOT.md .\MEMORY-SSOT.md
```

### Run Tests
```bash
python test_suite.py
```

## Purpose

Links your **memory layer** to your **skills** through pre-computed cross-reference nodes and intelligent intent-based matching.

## Structure

```
memory/graphify-out/
├── graph.json          # Original memory graph
├── GRAPH_REPORT.md
└── benchmark/ # Stress tests and results
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

>> **Note from Creator:**
> "using the example of moving because all of my agentic projects are intended to be tasks you want to delegate in your life so you can focus on what makes life fun as opposed to taking fun tasks and trying to make them perfect. i want the annoying tasks out of the way"

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


## Future Features

The following features are planned or in development:

| Feature | Status | Description |
|---------|--------|-------------|
| **Unified Query Graph** | Planned | Merge memory and skills graphs into a single queryable layer |
| **Persistent Caching** | In Progress | Disk-based cache for repeated queries |
| **Edge Traversal** | Active | Relationship-based retrieval (see `edge-traversal.md`) |
| **Intent Classification** | Planned | TF-IDF based intent detection (see `hlco` project) |

> Want to contribute? Open an issue or PR on GitHub!

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
