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
import argparse
import urllib
import urllib.error
import urllib.request
from pathlib import Path
from datetime import datetime
import re
from cache import cache

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "what", "is", "my", "your", "our", "to", "of", "in", "on", "for", "and",
    "or", "how", "do", "i", "me", "we", "it", "this", "that", "these",
    "those", "with", "as", "at", "by", "from", "into",
}


def _short_content(node):
    if not isinstance(node, dict):
        return None
    for key in ("content", "rationale", "description", "facts", "value", "summary"):
        v = node.get(key)
        if v is None:
            continue
        if isinstance(v, (list, dict)):
            v = " ".join(str(x) for x in (v if isinstance(v, list) else v.values()))
        r = str(v).strip()
        if not r:
            continue
        if len(r) <= 400:
            return r
        cut = r[:400]
        for sep in (". ", "! ", "? ", "\n", "; "):
            idx = cut.rfind(sep)
            if idx > 80:
                return cut[: idx + len(sep)].strip()
        sp = cut.rfind(" ")
        if sp > 80:
            return cut[:sp].strip()
        return cut.strip()


def load_bridge_edges():
    if BRIDGE_EDGES_FILE.exists():
        try:
            with open(BRIDGE_EDGES_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def _resolve_memory_ref(ref, graph):
    if not ref:
        return None
    needle = str(ref).strip().lower()
    for node in graph.get("nodes", []):
        label = (node.get("label") or "").lower()
        norm = (node.get("norm_label") or "").lower()
        if not label:
            continue
        if needle == label or needle == norm:
            return node
        if label in needle or needle in label:
            return node
    return None


def _tokenize(text: str) -> set:
    if not text:
        return set()
    toks = set(re.findall(r"[a-z0-9]+", str(text).lower()))
    return {t for t in toks if t not in STOPWORDS}


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
BRIDGE_EDGES_FILE = BRIDGE / "bridge_edges.json"
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
"skill_weights": {
        "memory-graph": 1.0, "hermes-agent": 0.9, "graphify": 0.95, "finances": 1.0,
        "agent-skills": 0.9, "security": 0.85, "research": 0.85, "productivity": 0.85,
        "devops": 0.85, "software-development": 0.85, "creative": 0.85, "mlops": 0.85,
        "github": 0.85, "learning": 0.85, "note-taking": 0.85, "autonomous-ai-agents": 0.85,
        "mcp": 0.85, "project": 0.85,
    },
    "intent_keywords": {
        "finances": "financial",
        "finance": "financial",
        "move": "relocation",
        "relocation": "relocation",
        "hermes": "agent_config",
        "memory": "memory_structure",
        "graph": "graph",
        "config": "configuration",
        "skill": "skills",
        "ssh": "ssh",
        "tailscale": "network",
        "tailnet": "network",
        "network": "network",
        "todo": "tasks",
    },
    "intent_priorities": {
        "financial": ["Move Fund", "Income Bridge", "Finances"],
        "relocation": ["Move Plan", "Move Target"],
        "network": ["Tailnet"],
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
        with open(bridge_nodes, encoding="utf-8") as f:
            return json.load(f)
    return []

def _slugify(text):
    return re.sub(r"[^a-z0-9_]+", "_", str(text).strip().lower()).strip("_") or "node"


def build_graph_from_markdown(user_md_path, ssot_md_path, output_graph_path):
    user_md_path = Path(user_md_path)
    ssot_md_path = Path(ssot_md_path)
    output_graph_path = Path(output_graph_path)
    nodes = []
    seen = set()
    current = None

    def add_node(label, source_file):
        nonlocal current
        label = str(label).strip()
        if not label:
            return None
        nid = _slugify(label)
        if nid in seen:
            for n in nodes:
                if n["id"] == nid:
                    current = n
                    return n
        node = {"id": nid, "label": label, "type": "memory_node", "source_file": str(source_file), "rationale": None}
        nodes.append(node)
        seen.add(nid)
        current = node
        return node

    for path in (user_md_path, ssot_md_path):
        if not path.exists():
            continue
        cur = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip()
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                label = stripped.lstrip("#").strip()
                if level <= 2:
                    node = add_node(label, path.name)
                    cur = node
            elif stripped.startswith("-") or stripped.startswith("*"):
                text = stripped.lstrip("-*").strip()
                if cur is not None:
                    if cur.get("rationale"):
                        cur["rationale"] = cur["rationale"] + " " + text
                    else:
                        cur["rationale"] = text
                else:
                    add_node(text, path.name)

    edges = []
    for i in range(len(nodes) - 1):
        edges.append({"source": nodes[i]["id"], "target": nodes[i + 1]["id"]})
    hyperedges = []
    if nodes:
        hyperedges.append({"id": "all_nodes", "label": "All memory nodes", "nodes": [n["id"] for n in nodes], "relation": "related"})
    chunk = []
    for n in nodes:
        chunk.append(n["id"])
        if len(chunk) >= 5:
            hyperedges.append({"id": "group_" + chunk[0], "nodes": list(chunk), "relation": "related"})
            chunk = []
    if chunk:
        hyperedges.append({"id": "group_" + chunk[0], "nodes": list(chunk), "relation": "related"})

    data = {"directed": False, "multigraph": False, "graph": {"hyperedges": hyperedges}, "nodes": nodes, "links": edges, "edges": edges, "hyperedges": hyperedges}
    output_graph_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def load_memory_graph():
    global MEMORY_GRAPH
    if not MEMORY_GRAPH.exists():
        try:
            user_candidate = None
            ssot_candidate = None
            for u in (BRIDGE / "USER.md", BRIDGE.parent / "USER.md", BRIDGE / "examples" / "example-USER.md"):
                if u.exists():
                    user_candidate = u
                    break
            for s in (BRIDGE / "MEMORY-SSOT.md", BRIDGE.parent / "MEMORY-SSOT.md", BRIDGE / "examples" / "example-MEMORY-SSOT.md"):
                if s.exists():
                    ssot_candidate = s
                    break
            if user_candidate and ssot_candidate:
                build_graph_from_markdown(user_candidate, ssot_candidate, MEMORY_GRAPH)
        except Exception:
            pass
    if MEMORY_GRAPH.exists():
        with open(MEMORY_GRAPH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            data = {"nodes": [], "edges": [], "hyperedges": []}
        nodes = data.get("nodes", [])
        edges = data.get("edges", data.get("links", []))
        if edges is None:
            edges = []
        hypers = data.get("hyperedges")
        if hypers is None:
            g = data.get("graph")
            if isinstance(g, dict):
                hypers = g.get("hyperedges", [])
            else:
                hypers = []
        if hypers is None:
            hypers = []
        data["nodes"] = nodes
        data["edges"] = edges
        data["links"] = edges
        data["hyperedges"] = hypers
        if not isinstance(data.get("graph"), dict):
            data["graph"] = {}
        data["graph"]["hyperedges"] = hypers
        return data
    return {"nodes": [], "edges": [], "links": [], "hyperedges": [], "graph": {"hyperedges": []}}


def get_edges_for_node(graph: dict, node_id: str) -> list:
    """Find all hyperedges connected to a given node."""
    return [e for e in graph.get("hyperedges", []) if node_id in e.get("nodes", [])]


def get_connected_nodes(graph: dict, node_id: str, edge_limit: int = 3) -> list:
    bridge_edges = load_bridge_edges()
    connected = []
    seen = set()
    # binary edges
    for e in (graph.get("edges", []) or graph.get("links", []) or []):
        s = e.get("source")
        t = e.get("target")
        if s == node_id and t is not None and t not in seen:
            connected.append(t); seen.add(t)
        elif t == node_id and s is not None and s not in seen:
            connected.append(s); seen.add(s)
    # hyperedges
    hypers = graph.get("hyperedges") or (graph.get("graph", {}) or {}).get("hyperedges", []) or []
    for edge in hypers:
        if node_id in (edge.get("nodes") or []):
            for nid in edge.get("nodes", []):
                if nid != node_id and nid not in seen:
                    connected.append(nid); seen.add(nid)
    # bridge edges
    for e in bridge_edges:
        s = e.get("source")
        t = e.get("target")
        if s == node_id and t is not None and t not in seen:
            connected.append(t); seen.add(t)
        elif t == node_id and s is not None and s not in seen:
            connected.append(s); seen.add(s)
    if edge_limit and edge_limit > 0:
        return connected[:edge_limit]
    return connected


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
        "model": _env("LUCKY_LLM_MODEL", "HLCO_LLM_MODEL") or "default",
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


def find_relevant_nodes(query, intent, bridge, graph):
    config = load_config()
    threshold = config.get("confidence_threshold", 0.8)
    weights = dict(config.get("skill_weights", {}) or {})
    for node in (bridge or []):
        sk = node.get("skill")
        if sk is not None and sk not in weights:
            weights[sk] = 0.85

    query_lower = query.lower()
    query_tokens = _tokenize(query)
    matched = []
    seen_ids = set()

    def add_entry(entry):
        eid = entry.get("id")
        if eid is None or eid in seen_ids:
            return False
        matched.append(entry)
        seen_ids.add(eid)
        return True

    norm_skill = lambda s: str(s).replace("-", " ").replace("_", " ").lower()

    # Step 1: skill matching with tokenized overlap + aliases
    all_skills = set(weights.keys()) | {n.get("skill") for n in (bridge or []) if n.get("skill") is not None}
    for skill in all_skills:
        if skill is None:
            continue
        w = weights.get(skill, 0.85)
        if w is None:
            w = 0.85
        sn = norm_skill(skill)
        skill_tokens = _tokenize(sn)
        is_match = False
        if sn and sn in query_lower:
            is_match = True
        if skill_tokens and skill_tokens.issubset(query_tokens):
            is_match = True
        if (not is_match) and skill_tokens and (skill_tokens & query_tokens):
            is_match = True
        if not is_match:
            continue
        confidence = round(min(1.0, 0.80 + 0.20 * float(w)), 3)
        if confidence < threshold:
            continue
        for node in (bridge or []):
            if node.get("skill") != skill:
                continue
            add_entry({
                "id": node.get("id"),
                "label": node.get("label"),
                "type": "skill_reference",
                "confidence": confidence,
                "content": _short_content(node),
            })
            mem = _resolve_memory_ref(node.get("memory_ref"), graph)
            if mem is not None:
                mem_conf = round(min(1.0, confidence + 0.05), 3)
                if mem_conf >= threshold:
                    add_entry({
                        "id": mem.get("id"),
                        "label": mem.get("label"),
                        "type": mem.get("type"),
                        "confidence": mem_conf,
                        "content": _short_content(mem),
                    })

    # Step 2: memory node token overlap + reverse bridging
    for node in graph.get("nodes", []):
        nid = node.get("id")
        if nid in seen_ids:
            continue
        label_tokens = _tokenize(node.get("label", ""))
        if not label_tokens:
            continue
        overlap = query_tokens & label_tokens
        if not overlap:
            continue
        score = len(overlap) / len(label_tokens)
        confidence = round(0.8 + 0.15 * score, 3)
        if confidence < threshold:
            continue
        add_entry({
            "id": nid,
            "label": node.get("label"),
            "type": node.get("type"),
            "confidence": confidence,
            "content": _short_content(node),
        })
        # reverse bridge: skills whose memory_ref resolves to this node
        for bnode in (bridge or []):
            mem = _resolve_memory_ref(bnode.get("memory_ref"), graph)
            if mem is not None and mem.get("id") == nid:
                skill = bnode.get("skill")
                w = weights.get(skill, 0.85)
                if w is None:
                    w = 0.85
                sconf = round(min(confidence, 0.80 + 0.20 * float(w)), 3)
                if sconf < threshold:
                    continue
                add_entry({
                    "id": bnode.get("id"),
                    "label": bnode.get("label"),
                    "type": "skill_reference",
                    "confidence": sconf,
                    "content": _short_content(bnode),
                })
                m2 = _resolve_memory_ref(bnode.get("memory_ref"), graph)
                if m2 is not None and m2.get("id") not in seen_ids:
                    mc = round(min(1.0, sconf + 0.05), 3)
                    if mc >= threshold:
                        add_entry({
                            "id": m2.get("id"),
                            "label": m2.get("label"),
                            "type": m2.get("type"),
                            "confidence": mc,
                            "content": _short_content(m2),
                        })

    # Step 3: intent priorities always evaluated
    priorities = config.get("intent_priorities", {}).get(intent)
    if not priorities:
        priorities = config.get("intent_priorities", {}).get("general", [])
    for p in (priorities or []):
        for node in graph.get("nodes", []):
            if str(p).lower() in str(node.get("label", "")).lower():
                nid = node.get("id")
                if nid in seen_ids:
                    continue
                conf = 0.85
                if conf < threshold:
                    continue
                add_entry({
                    "id": nid,
                    "label": node.get("label"),
                    "type": node.get("type"),
                    "confidence": conf,
                    "content": _short_content(node),
                })
                for bnode in (bridge or []):
                    mem = _resolve_memory_ref(bnode.get("memory_ref"), graph)
                    if mem is not None and mem.get("id") == nid:
                        skill = bnode.get("skill")
                        w = weights.get(skill, 0.85)
                        if w is None:
                            w = 0.85
                        sconf = round(min(conf, 0.80 + 0.20 * float(w)), 3)
                        if sconf < threshold:
                            continue
                        add_entry({
                            "id": bnode.get("id"),
                            "label": bnode.get("label"),
                            "type": "skill_reference",
                            "confidence": sconf,
                            "content": _short_content(bnode),
                        })

    matched.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    return matched


def estimate_tokens(nodes: list) -> int:
    """Estimate token count from returned label + content (chars/4, labelled estimate)."""
    total = 0
    for node in nodes or []:
        text = node.get("label") or ""
        content = node.get("content")
        if content:
            text = f"{text} {content}"
        # chars/4 estimate plus small per-node overhead (JSON/fields)
        total += max(1, len(text) // 4 + 2)
    return total


def write_audit(query: str, intent: str, matched: list, excluded: list, tokens_used: int):
    """Append an audit entry (never rewrite the whole file)."""
    max_lines = load_config().get("audit_max_lines", 5000)

    # Trim if over limit: rewrite with utf-8 (only when needed).
    if AUDIT_LOG.exists():
        try:
            lines = AUDIT_LOG.read_text(encoding="utf-8").splitlines()
        except Exception:
            lines = []
        if len(lines) >= max_lines:
            trimmed = lines[-(max_lines - 10):]
            AUDIT_LOG.write_text("\n".join(trimmed) + "\n", encoding="utf-8")

    # Header for a fresh log.
    if not AUDIT_LOG.exists() or AUDIT_LOG.stat().st_size == 0:
        with open(AUDIT_LOG, "w", encoding="utf-8") as f:
            f.write("# LUCKY Audit Log\n\n")

    # Excluded-nodes check via set.
    matched_ids = {m.get("id") for m in (matched or [])}
    excluded_ids = {n.get("id") for n in (excluded or []) if n.get("id") not in matched_ids}

    timestamp = datetime.now().isoformat()
    entry_lines = [
        f"### Entry {timestamp}",
        f'**Query:** "{query}"',
        f"**Intent:** {intent}",
        "**Loaded Nodes:**",
    ]
    for node in matched or []:
        entry_lines.append(f"- {node['label']} [confidence: {node['confidence']:.2f}]")
    if excluded_ids:
        entry_lines.append("**Excluded (count):** " + str(len(excluded_ids)))
    entry_lines.append(f"**Total Tokens:** {tokens_used}")
    entry_lines.append("---")
    entry = "\n".join(entry_lines) + "\n"

    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def resolve_query(query, budget=None, edge_limit=3):
    config = load_config()
    budget = budget or config.get("default_budget", 500)

    cache_key = f"query:{query}:{budget}:edge{edge_limit}"
    cached = cache.get(cache_key)
    if cached:
        val = cached.get("value")
        if val is not None:
            return val

    intent = extract_intent(query)
    bridge = load_bridge()
    graph = load_memory_graph()

    matched = find_relevant_nodes(query, intent, bridge, graph)

    matched_ids = set(m["id"] for m in matched)
    expanded_nodes = set()
    edges_followed = 0

    for node in list(matched):
        node_id = node["id"]
        connected = get_connected_nodes(graph, node_id, edge_limit=edge_limit)
        for conn_id in connected:
            if conn_id not in matched_ids:
                expanded_nodes.add(conn_id)
                edges_followed += 1

    for node in graph.get("nodes", []):
        if node.get("id") in expanded_nodes:
            nid = node.get("id")
            if nid not in matched_ids:
                matched.append({
                    "id": nid,
                    "label": node.get("label"),
                    "type": node.get("type"),
                    "confidence": 0.6,
                    "source": "edge_expansion",
                    "content": _short_content(node),
                })
                matched_ids.add(nid)

    matched.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    selected = []
    used = 0
    for node in matched:
        cost = estimate_tokens([node])
        if not selected or used + cost <= budget:
            selected.append(node)
            used += cost
        else:
            if not selected:
                selected.append(node)
                used += cost
    matched = selected
    estimated = estimate_tokens(matched)

    excluded = [n for n in graph.get("nodes", []) if n.get("id") not in [m["id"] for m in matched]]
    write_audit(query, intent, matched, excluded, estimated)

    active_tools = _make_active_tools(matched, limit=3)

    result = {
        "nodes": matched,
        "budget_used": estimated,
        "intent": intent,
        "edge_followed_count": edges_followed,
        "active_tools": active_tools,
    }

    cache.set(cache_key, result)
    return result


def _make_active_tools(matched, limit=3):
    tools = []
    seen = set()
    count = 0
    for node in matched:
        if node.get("type") != "skill_reference":
            continue
        skill_name = None
        for b in load_bridge():
            if b.get("id") == node.get("id"):
                skill_name = b.get("skill")
                break
        if not skill_name:
            nid = node.get("id", "")
            if isinstance(nid, str) and nid.startswith("SKILL-"):
                skill_name = nid.split("_")[0].replace("SKILL-", "")
        if not skill_name or skill_name in seen:
            continue
        seen.add(skill_name)
        tools.append({
            "type": "function",
            "function": {
                "name": str(skill_name).replace("-", "_"),
                "description": f"Use the {skill_name} skill for this context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Sub-query for this skill."}
                    },
                    "required": [],
                },
            },
        })
        count += 1
        if count >= limit:
            break
    tools.append({
        "type": "function",
        "function": {
            "name": "lucky_memory_update",
            "description": "Update a memory node in the Lucky.Engine graph with new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node": {"type": "string", "description": "Node id or label to update."},
                    "content": {"type": "string", "description": "New content to store."},
                },
                "required": ["node", "content"],
            },
        },
    })
    return tools


def update_memory_node(node_id_or_label, new_content):
    graph = load_memory_graph()
    target = None
    needle = str(node_id_or_label).strip().lower()
    for node in graph.get("nodes", []):
        nid = str(node.get("id", "")).lower()
        label = str(node.get("label", "")).lower()
        if nid == needle or label == needle or needle in label or label in needle:
            target = node
            break
    if target is None:
        return {"status": "not_found", "node": node_id_or_label}
    target["rationale"] = new_content
    target["content"] = new_content
    target["description"] = new_content
    out = MEMORY_GRAPH
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    cache.clear()
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"### Memory Update {datetime.now().isoformat()}\n- node: {target.get('id')}\n- content: {new_content}\n---\n")
    except Exception:
        pass
    return {"status": "updated", "node": target.get("id"), "label": target.get("label")}


def _format_prompt(result):
    nodes = sorted(result.get("nodes", []), key=lambda n: str(n.get("id", "")))
    lines = ["<lucky_context>"]
    for n in nodes:
        nid = n.get("id")
        label = n.get("label")
        conf = n.get("confidence")
        content = n.get("content")
        attrs = f'id="{nid}" label="{label}" confidence="{conf}"'
        lines.append(f'  <node {attrs}>{content if content is not None else ""}</node>')
    lines.append("</lucky_context>")
    return "\n".join(lines)
    


def main():
    parser = argparse.ArgumentParser(description="Lucky.Engine")
    parser.add_argument("query", nargs="?", default="finances")
    parser.add_argument("--query", dest="query_opt", default=None)
    parser.add_argument("--budget", type=int, default=None)
    parser.add_argument("--edge-limit", type=int, default=3)
    parser.add_argument("--format", choices=["json", "prompt", "compact"], default="json")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--update-node", dest="update_node", default=None)
    parser.add_argument("--content", default=None)
    args = parser.parse_args()

    if args.query_opt:
        args.query = args.query_opt

    if args.build:
        user_candidate = None
        ssot_candidate = None
        for u in (BRIDGE / "USER.md", BRIDGE.parent / "USER.md", BRIDGE / "examples" / "example-USER.md"):
            if u.exists():
                user_candidate = u
                break
        for s in (BRIDGE / "MEMORY-SSOT.md", BRIDGE.parent / "MEMORY-SSOT.md", BRIDGE / "examples" / "example-MEMORY-SSOT.md"):
            if s.exists():
                ssot_candidate = s
                break
        if not user_candidate or not ssot_candidate:
            print(json.dumps({"status": "error", "message": "missing USER.md / MEMORY-SSOT.md"}))
            return
        graph = build_graph_from_markdown(user_candidate, ssot_candidate, MEMORY_GRAPH)
        print(json.dumps({"status": "built", "output": str(MEMORY_GRAPH), "nodes": len(graph.get("nodes", []))}))
        return

    if args.update_node:
        res = update_memory_node(args.update_node, args.content if args.content is not None else "")
        print(json.dumps(res))
        return

    result = resolve_query(args.query, budget=args.budget, edge_limit=args.edge_limit)

    if args.format == "prompt":
        print(_format_prompt(result))
    elif args.format == "compact":
        print(json.dumps(result, separators=(",", ":")))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
