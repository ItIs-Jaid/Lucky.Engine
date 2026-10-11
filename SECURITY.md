# Security Model

## Local-First Architecture

Lucky.Engine is designed to be **local-first** to prevent supply-chain attacks or external manipulation.

### What This Means

| Component | Source | Mutable from outside? |
|-----------|--------|----------------------|
| Skill definitions | Local `bridge_nodes.json` | ❌ No (file-based) |
| Memory graph | Local `graph.json` | ❌ No (file-based) |
| Query resolution | Local `engine.py` | ❌ No (compiled) |
| Cache | Local in-memory cache | ❌ No (runtime) |

### What We DON'T Use

- ❌ Remote skill fetching
- ❌ Public skill registries
- ❌ Web-based skill updates
- ❌ External skill loading

### How To Verify

All skill references in `bridge_nodes.json` point to local memory nodes:

```json
{
  "id": "SKILL_finance_0",
  "skill": "finances",
  "memory_ref": "Move Fund",  ← Local node, not URL
  "type": "skill_reference"
}
```

### Threat Model

- **Supply-chain attack:** Cannot happen; no remote dependencies
- **Skill tampering:** Requires local file access (same as system compromise)
- **Data exfiltration:** No external API calls by default

---
*Local-First Security Model v1.0*
