#!/usr/bin/env python3
"""
Lucky.Engine Core
Resolves queries to relevant memory/skills nodes with budget constraints.
"""

import json
from pathlib import Path
from datetime import datetime
import re
import os

# Paths
BASE = Path("C:/Users/<your-name>/<your-project>")
BRIDGE = BASE / "memory" / "graphify-out" / "bridge"
MEMORY_GRAPH = BASE / "memory" / "graphify-out" / "graph.json"
AUDIT_LOG = BRIDGE / "lucky-audit.md"
CONFIG_FILE = BRIDGE / "lucky-config.yaml"


def load_config():
    """Load HLCO configuration (simple key-value parser)."""
    if CONFIG_FILE.exists():
        config = {}
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        config[key.strip()] = val.strip()
        # Convert to proper types
        result = {
            "max_tokens": int(config.get("max_tokens", 2000)),
            "confidence_threshold": float(config.get("confidence_threshold", 0.8)),
            "audit_max_lines": int(config.get("audit_max_lines", 5000)),
            "default_budget": int(config.get("default_budget", 500)),
        }
        return result
    
    return {
        "max_tokens": 2000,
        "confidence_threshold": 0.8,
        "audit_max_lines": 5000,
        "default_budget": 500,
    }


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
    """Extract primary intent from query using LLM when available, fallback to keyword matching."""
    
    # Check for LLM API key
    api_key = os.environ.get("HLCO_LLM_API_KEY")
    
    if api_key:
        # Use LLM-based classification
        return classify_intent_llm(query)
    
    # Fallback to keyword matching
    query_lower = query.lower()
    
    # Intent mapping
    intents = [
        ("finances", "financial"),
        ("move", "relocation"),
        ("hermes", "agent_config"),
        ("memory", "memory_structure"),
        ("graph", "graph"),
        ("config", "configuration"),
        ("skill", "skills"),
        ("ssh", "ssh"),
        ("tailscale", "network"),
        ("todo", "tasks"),
    ]
    
    for keyword, intent in intents:
        if keyword in query_lower:
            return intent
    
    return "general"


def classify_intent_llm(query: str) -> str:
    """Classify intent using LLM API when key is available."""
    import urllib.request
    import urllib.error
    
    # Try OpenAI-compatible endpoint (default to localhost)
    api_url = os.environ.get("HLCO_LLM_API_URL", "http://localhost:8080/v1/chat/completions")
    
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
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 20
    }
    
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return content if content else "general"
    
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, TimeoutError):
        return "general"


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
    
    # 2. Match by memory node content
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
        intent_priorities = {
            "financial": ["Move Fund", "Income Bridge", "Finances"],
            "relocation": ["Move Plan", "Move Target"],
            "agent_config": ["Hermes Agent", "Profile"],
            "general": ["User Mirror", "Memory SSOT"],
        }
        
        priorities = intent_priorities.get(intent, intent_priorities["general"])
        for node in graph.get("nodes", []):
            for priority in priorities:
                if priority.lower() in node.get("label", "").lower():
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
    
    return {
        "nodes": matched,
        "budget_used": estimated,
        "intent": intent,
        "edge_followed_count": edges_followed,
    }


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "finances"
    result = resolve_query(query)
    print(json.dumps(result, indent=2))
