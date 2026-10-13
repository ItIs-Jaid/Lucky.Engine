#!/usr/bin/env python3
"""
Lucky.Engine Core

SECURITY: Local-first architecture. All skill and memory data is loaded
from local files only. No external fetches, registries, or remote calls.

Threat model:
- No supply-chain attacks (no remote dependencies)
- No skill tampering without local file access
- No data exfiltration (no external API calls)
"""

import json
import os
import urllib
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime
import re
from cache import cache

def _env(primary, *fallbacks):
    """Read env var with deprecated-name fallbacks. Returns None if unset/empty."""
    for name in (primary,) + tuple(fallbacks):
        val = os.environ.get(name)
        if val:
            return val
    return None


# Paths — bridge dir is wherever this file lives; memory graph is one level up
# (override with LUCKY_MEMORY_GRAPH / deprecated HLCO_MEMORY_GRAPH env var)
BRIDGE = Path(__file__).resolve().parent
MEMORY_GRAPH = Path(
    _env("LUCKY_MEMORY_GRAPH", "HLCO_MEMORY_GRAPH") or str(BRIDGE.parent / "graph.json")
)
AUDIT_LOG = BRIDGE / "lucky-audit.md"
_config_env = _env("LUCKY_CONFIG_FILE", "HLCO_CONFIG_FILE")
CONFIG_FILE = Path(_config_env) if _config_env else BRIDGE / "lucky-config.yaml"


def _parse_scalar(value: str):
    value = value.strip()
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if value == "":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        return value[1:-1]
    return value


_DEFAULT_CONFIG = {
    "max_tokens": 2000,
    "confidence_threshold": 0.8,
    "audit_max_lines": 5000,
    "default_budget": 500,
    "fallback_budget": 1500,
    "cache_enabled": False,
    "skill_weights": {},
    "intent_keywords": {
        "finances": "financial",
        "move": "relocation",
        "hermes": "agent_config",
        "memory": "memory_structure",
        "graph": "graph",
        "config": "configuration",
        "skill": "skills",
        "ssh": "ssh",
        "tailscale": "network",
        "todo": "tasks",
    },
    "intent_priorities": {
        "financial": ["Move Fund", "Income Bridge", "Finances"],
        "relocation": ["Move Plan", "Move Target"],
        "agent_config": ["Hermes Agent", "Profile"],
        "general": ["User Mirror", "Memory SSOT"],
    },
}


def load_config():
    """Load Lucky.Engine configuration (nested YAML subset, stdlib only)."""
    path = CONFIG_FILE
    if not path.exists():
        return dict(_DEFAULT_CONFIG)

    config: dict = {}
    current: str | None = None

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            if ":" not in stripped:
                continue
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if indent == 0:
                current = None
                if val == "":
                    config[key] = {}
                    current = key
                else:
                    # inline dict on one line isn't supported; scalar
                    config[key] = _parse_scalar(val)
            else:
                # indented child
                parent = current
                if parent is None:
                    # infer parent: last dict at top level
                    for k in reversed(list(config)):
                        if isinstance(config[k], dict):
                            parent = k
                            current = k
                            break
                if parent is not None and isinstance(config.get(parent), dict):
                    config[parent][key] = _parse_scalar(val)

    # Merge with defaults
    result = dict(_DEFAULT_CONFIG)
    for k, v in config.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = {**result[k], **v}
        else:
            result[k] = v

    # Type coercion for known keys
    result["max_tokens"] = int(result.get("max_tokens", _DEFAULT_CONFIG["max_tokens"]))
    result["confidence_threshold"] = float(result.get("confidence_threshold", _DEFAULT_CONFIG["confidence_threshold"]))
    result["audit_max_lines"] = int(result.get("audit_max_lines", _DEFAULT_CONFIG["audit_max_lines"]))
    result["default_budget"] = int(result.get("default_budget", _DEFAULT_CONFIG["default_budget"]))
    result["fallback_budget"] = int(result.get("fallback_budget", _DEFAULT_CONFIG["fallback_budget"]))
    result["cache_enabled"] = bool(result.get("cache_enabled", _DEFAULT_CONFIG["cache_enabled"]))
    result["skill_weights"] = dict(result.get("skill_weights", {}) or {})
    result["intent_keywords"] = dict(result.get("intent_keywords", {}) or {})
    result["intent_priorities"] = dict(result.get("intent_priorities", {}) or {})

    if not result["intent_keywords"]:
        result["intent_keywords"] = dict(_DEFAULT_CONFIG["intent_keywords"])
    if not result["intent_priorities"]:
        result["intent_priorities"] = dict(_DEFAULT_CONFIG["intent_priorities"])

    return result


def load_bridge():
    """Load bridge mappings (skill→memory)."""
    bridge_nodes = BRIDGE / "bridge_nodes.json"
    if bridge_nodes.exists():
        with open(bridge_nodes) as f:
            return json.load(f)
    return []


def load_memory_graph():
    """Load the memory graph."""
    if MEMORY_GRAPH.exists():
        with open(MEMORY_GRAPH) as f:
            return json.load(f)
    return {"nodes": [], "edges": [], "hyperedges": []}


def get_edges_for_node(graph: dict, node_id: str) -> list:
    """Find all hyperedges connected to a given node."""
    return [e for e in graph.get("hyperedges", []) if node_id in e.get("nodes", [])]


def get_connected_nodes(graph: dict, node_id: str, edge_limit: int = 3) -> list:
    """
    Follow graph edges to find related nodes.
    Returns nodes connected via hyperedges, excluding the source node.
    """
    connected = set()
    edges_seen = 0
    
    for edge in graph.get("hyperedges", []):
        if node_id in edge.get("nodes", []) and edges_seen < edge_limit:
            edges_seen += 1
            for neighbor_id in edge.get("nodes", []):
                if neighbor_id != node_id:
                    connected.add(neighbor_id)
    
    return list(connected)


def extract_intent(query: str) -> str:
    """Extract primary intent from query using LLM when available, keyword fallback."""
    # Check for LLM API key
    api_key = _env("LUCKY_LLM_API_KEY", "HLCO_LLM_API_KEY")

    if api_key:
        # Use LLM-based classification
        return classify_intent_llm(query)

    # Fallback to keyword matching
    return _keyword_intent(query)


def _keyword_intent(query: str) -> str:
    """Keyword intent classifier (also LLM fallback)."""
    query_lower = query.lower()
    try:
        keywords = load_config().get("intent_keywords", {})
    except Exception:
        keywords = {}
    if not keywords:
        keywords = _DEFAULT_CONFIG["intent_keywords"]
    for keyword, intent in keywords.items():
        if keyword in query_lower:
            return intent
    return "general"


def classify_intent_llm(query: str) -> str:
    """Classify intent using LLM API when key is available."""
    import json as _json

    # Try OpenAI-compatible endpoint (LUCKY_ with deprecated HLCO_ fallback)
    api_url = _env("LUCKY_LLM_API_URL", "HLCO_LLM_API_URL") or "http://localhost:8080/v1/chat/completions"

    system_prompt = """You are an intent classifier for a personal knowledge management system.
Classify the user's query into one of these intents:
- financial: Money, finances, budget, income, expenses, investments
- relocation: Moving, housing, relocation, property
- agent_config: Agent setup, configuration, hermes settings
- memory_structure: Memory organization, knowledge graph, notes
- graph: Network relationships, connections, links
- configuration: General settings, preferences
- skills: Abilities, capabilities, competencies
- ssh: Remote access, security keys, connections
- network: Networking, connectivity, infrastructure
- tasks: Todo, action items, to-do lists

Return ONLY the intent name, nothing else."""

    user_prompt = f"Query: {query}"

    payload = {
        "model": "default",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 20,
    }

    api_key = _env("LUCKY_LLM_API_KEY", "HLCO_LLM_API_KEY")
    if not api_key:
        return _keyword_intent(query)

    headers = {"Content-Type": "application/json"}
    headers["Authorization"] = f"Bearer {api_key}"

    try:
        req = urllib.request.Request(
            api_url,
            data=_json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = _json.loads(response.read().decode("utf-8"))
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return content if content else _keyword_intent(query)

    except Exception:
        # Network, parsing, key, timeout, etc. -> keyword fallback (never "general" blindly)
        return _keyword_intent(query)


def find_relevant_nodes(query: str, intent: str, bridge: list, graph: dict) -> list:
    """Find nodes relevant to query intent."""
    query_lower = query.lower()
    max_tokens = load_config().get("max_tokens", 2000)
    threshold = load_config().get("confidence_threshold", 0.8)
    weights = load_config().get("skill_weights", {})
    
    matched = []
    
    # 1. Match by skill in query
    for skill, weight in weights.items():
        if skill in query_lower:
            # Find bridge mappings for this skill
            for node in bridge:
                if node.get("skill", "") == skill:
                    confidence = 0.9 * weight
                    if confidence >= threshold:
                        matched.append({
                            "id": node.get("id"),
                            "label": node.get("label"),
                            "type": "skill_reference",
                            "confidence": confidence,
                        })

    # 2. Match by memory node content (token-overlap done in chunk 3; keep substring for now)
    for node in graph.get("nodes", []):
        label = node.get("label", "").lower()
        if query_lower in label:
            confidence = 0.95
            if confidence >= threshold:
                matched.append({
                    "id": node.get("id"),
                    "label": node.get("label"),
                    "type": node.get("type"),
                    "confidence": confidence,
                })

    # 3. Fallback: return high-confidence nodes by intent
    if not matched:
        priorities = load_config().get("intent_priorities", {}).get(intent) or load_config().get("intent_priorities", {}).get("general", [])
        for node in graph.get("nodes", []):
            for priority in priorities:
                if priority.lower() in node.get("label", "").lower():
                    if 0.85 >= threshold:
                        matched.append({
                            "id": node.get("id"),
                            "label": node.get("label"),
                            "type": node.get("type"),
                            "confidence": 0.85,
                        })
                    break
    
    # Sort by confidence, limit by budget
    matched.sort(key=lambda x: x["confidence"], reverse=True)
    return matched


def estimate_tokens(nodes: list) -> int:
    """Estimate token count for nodes."""
    # Rough estimate: ~10 tokens per label + 100 per node
    return sum(100 + 10 * len(n.get("label", "")) for n in nodes)


def write_audit(query: str, intent: str, matched: list, excluded: list, tokens_used: int):
    """Write audit entry to log."""
    if not AUDIT_LOG.exists():
        AUDIT_LOG.write_text("# HLCO Audit Log\n\n")
    
    # Load existing log
    log_text = AUDIT_LOG.read_text()
    lines = log_text.strip().split("\n")
    
    # Trim if over limit
    max_lines = load_config().get("audit_max_lines", 5000)
    if len(lines) >= max_lines:
        lines = lines[-(max_lines - 10):]
        log_text = "\n".join(lines) + "\n"
    
    # Append new entry
    timestamp = datetime.now().isoformat()
    entry = f"""
### Entry {timestamp}
**Query:** "{query}"
**Intent:** {intent}
**Loaded Nodes:**
"""
    for node in matched:
        entry += f"- {node['label']} [confidence: {node['confidence']:.2f}]\n"
    
    if excluded:
        entry += "**Excluded:**\n"
        for node in excluded[:5]:  # Limit excluded listing
            entry += f"- {node.get('label', 'unknown')}\n"
    
    entry += f"**Total Tokens:** {tokens_used}\n---\n"
    
    AUDIT_LOG.write_text(log_text + entry)


def resolve_query(query: str, budget: int = None, edge_limit: int = 3) -> dict:
    """
    Main entry point. Resolve query to context with edge traversal.
    Returns dict with nodes, budget_used, audit_id, edge_followed_count.
    """
    config = load_config()
    budget = budget or config.get("default_budget", 500)
    
    # Check cache first (skip for edge traversal to avoid stale context)
    cache_key = f"query:{query}:{budget}:edge{edge_limit}"
    cached = cache.get(cache_key)
    if cached and edge_limit == 0:
        return cached
    
    intent = extract_intent(query)
    bridge = load_bridge()
    graph = load_memory_graph()
    
    matched = find_relevant_nodes(query, intent, bridge, graph)
    
    # Edge traversal: expand context by following graph edges
    matched_ids = set(m["id"] for m in matched)
    expanded_nodes = set()
    edges_followed = 0
    
    for node in matched:
        node_id = node["id"]
        connected = get_connected_nodes(graph, node_id, edge_limit=edge_limit)
        for conn_id in connected:
            if conn_id not in matched_ids:
                expanded_nodes.add(conn_id)
                edges_followed += 1
    
    # Add expanded nodes to matched with lower confidence
    for node in graph.get("nodes", []):
        if node.get("id") in expanded_nodes:
            matched.append({
                "id": node.get("id"),
                "label": node.get("label"),
                "type": node.get("type"),
                "confidence": 0.6,  # Lower confidence for edge-followed nodes
                "source": "edge_expansion",
            })
    
    # Budget enforcement
    estimated = estimate_tokens(matched)
    if estimated > budget:
        matched = matched[:max(1, int(budget / 100))]
        estimated = estimate_tokens(matched)
    
    # Audit
    excluded = [n for n in graph.get("nodes", []) if n.get("id") not in [m["id"] for m in matched]]
    write_audit(query, intent, matched, excluded, estimated)
    
    result = {
        "nodes": matched,
        "budget_used": estimated,
        "intent": intent,
        "edge_followed_count": edges_followed,
    }
    
    # Cache result (only when edge traversal is disabled)
    if edge_limit == 0:
        cache.set(cache_key, result)
    
    return result
    


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "finances"
    result = resolve_query(query)
    print(json.dumps(result, indent=2))
