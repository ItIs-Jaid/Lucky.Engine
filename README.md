# Lucky.Engine

**Your Agent might be smart. Now make it Lucky ;)**

**Location:** `<your-project>/memory/graphify-out/bridge/`  
**Security:** Local-first (no external skill fetches)

> **A Note from the Creator:**
> "I'm trying to vibe my way to more effective local agents. I truly don't understand what exactly I'm building but want to share in case I'm building something of value that could help someone else. Always eager to learn and welcome any feedback :3"

## What It Does

This tool loads just the memory and skills you actually need for each query. Instead of dumping 3-8k tokens into context, it pulls down 300-500 tokens that are actually relevant to your question.

## Quick Start

### Linux/Mac
```bash
./install.sh
```

### Windows
```powershell
# Clone repo, then copy examples
Copy-Item examples\example-config.yaml .\lucky-config.yaml
Copy-Item examples\example-USER.md .\USER.md
Copy-Item examples\example-MEMORY-SSOT.md .\MEMORY-SSOT.md
```

### Run Tests
```bash
python test_suite.py
```

## Purpose

Connects your memory layer to your skills through bridge nodes. When you query "finances", it knows to pull from the Move Fund node and related nodes.

## How It Works

### Structure
```
memory/graphify-out/
├── graph.json          # Original memory graph
├── GRAPH_REPORT.md
└── benchmark/ # Stress tests
└── bridge/
    ├── bridge_nodes.json   # 14 skill-to-memory mappings
    └── bridge_edges.json   # 26 intra-skill edges
```

### Query Patterns

**Direct memory query:**
```bash
graphify query "What is my move plan?" --budget 500
```

**Through skill bridge:**
```bash
# Check what's mapped
cat bridge/bridge_nodes.json | grep "finances"
# Query linked node
graphify query "Move Fund" --budget 300
```

> **Note from Creator:**
> "using the example of moving because all of my agentic projects are intended to be tasks you want to delegate in your life so you can focus on what makes life fun as opposed to taking fun tasks and trying to make them perfect. i want the annoying tasks out of the way"

## Examples

Copy the template files and fill them with your actual data:
```bash
cp examples/example-config.yaml lucky-config.yaml
cp examples/example-USER.md USER.md
cp examples/example-MEMORY-SSOT.md MEMORY-SSOT.md
```

See `examples/QUICKSTART.md` for setup details.

## Alternate Uses

**Batch queries:**
Need to check finances, calendar, and tasks before you leave the house? Run a small script that hits all three and merges the results.

**Automation:**
Toss it in a shell script or cron job to pull today's priorities at 9 AM.

**Debugging:**
Agent getting lost? Run queries against your memory to see if the context was actually there.

## How to Use

1. **For memory:** `graphify query "X" --budget 500`
2. **For skills:** Check `bridge/bridge_nodes.json`
3. **Combined:** Run separate queries and merge

## Security

Local-first architecture. All skill and memory data is loaded from local files only.

| Component | Source | External access? |
|-----------|--------|-----------------|
| Skill definitions | `bridge_nodes.json` | ❌ No |
| Memory graph | `graph.json` | ❌ No |
| Intent classification | Optional local LLM | Configurable endpoint (default localhost) |

### Threat Model

- **Supply-chain attacks:** reduced risk (no runtime remote fetches for skills/memory)
- **Skill tampering:** Requires local file access
- **Data exfiltration:** No external API calls unless LLM classifier endpoint is configured

See **[SECURITY.md](SECURITY.md)** for full details.

## Dependencies

- Runtime: Python stdlib only.
- Optional: external `graphify` tool to build `graph.json` (not bundled).
- Optional LLM intent classifier uses a configurable OpenAI-compatible URL.

## Extending

Add new mappings to `bridge/bridge_nodes.json`:
```json
{
  "id": "SKILL_my-skill_0",
  "label": "my-skill → Memory Category",
  "type": "skill_reference",
  "skill": "my-skill",
  "memory_ref": "Memory Category"
}
```
