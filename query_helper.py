#!/usr/bin/env python3
"""
Unified Memory + Skills Query Helper

Usage:
    python query_helper.py "my question" [--budget 500] [--memory] [--skills]

Examples:
    python query_helper.py "move plan"
    python query_helper.py "finances" --budget 300
    python query_helper.py "hermes config" --skills
"""

import sys
import json
from pathlib import Path

# Paths
BASE = Path("C:/Users/<your-name>/<your-project>")
MEMORY_GRAPH = BASE / "memory" / "graphify-out" / "graph.json"
BRIDGE = BASE / "memory" / "graphify-out" / "bridge"

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {"nodes": [], "edges": []}

def search_memory(query, budget=500):
    """Search memory graph for matching nodes"""
    graph = load_json(MEMORY_GRAPH)
    nodes = graph.get("nodes", [])
    
    # Simple text search
    matches = []
    for node in nodes:
        label = node.get("label", "").lower()
        node_type = node.get("type", "").lower()
        if query.lower() in label or query.lower() in node_type:
            matches.append({
                "id": node.get("id"),
                "label": node.get("label"),
                "type": node.get("type"),
                "community": node.get("community")
            })
    
    return matches[:10]  # Limit results

def search_brige(query):
    """Search bridge for skill-to-memory mappings"""
    try:
        with open(BRIDGE / "bridge_nodes.json") as f:
            nodes = json.load(f)
        
        matches = []
        for node in nodes:
            label = node.get("label", "").lower()
            skill = node.get("skill", "").lower()
            if query.lower() in label or query.lower() in skill:
                matches.append({
                    "skill": node.get("skill"),
                    "memory_ref": node.get("memory_ref"),
                    "label": node.get("label")
                })
        return matches
    except:
        return []

def print_results(query, memory_matches, skill_matches, budget):
    print(f"\n📊 Query: '{query}' (budget: {budget} tokens)")
    print("=" * 50)
    
    if memory_matches:
        print(f"\n📝 MEMORY MATCHES ({len(memory_matches)} found):")
        for m in memory_matches[:5]:
            print(f"   • {m['label']} [{m.get('type', 'node')}]")
            if m.get('community'):
                print(f"     → Community: {m['community']}")
    
    if skill_matches:
        print(f"\n🔗 SKILL-BRIDGE MATCHES ({len(skill_matches)} found):")
        for m in skill_matches[:5]:
            print(f"   • {m['skill']} → {m['memory_ref']}")
    
    if not memory_matches and not skill_matches:
        print("\n⚠️  No direct matches found. Try:")
        print(f"   • Search graph directly: graphify query '{query}'")
        print(f"   • Check memory graph: graphify-out/GRAPH_REPORT.md")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    
    query = args[0]
    budget = 500
    search_both = True
    
    for i, arg in enumerate(args):
        if arg == "--budget" and i + 1 < len(args):
            budget = int(args[i + 1])
        elif arg == "--memory":
            search_both = False
            memory_only = True
        elif arg == "--skills":
            search_both = False
            skills_only = True
    
    print("🔍 Unified Memory + Skills Query Helper")
    
    if search_both or (not memory_only):
        memory_matches = search_memory(query, budget)
    else:
        memory_matches = []
    
    if search_both or (not skills_only):
        skill_matches = search_brige(query)
    else:
        skill_matches = []
    
    print_results(query, memory_matches, skill_matches, budget)
    
    print(f"\n📁 Data sources:")
    print(f"   Memory: {MEMORY_GRAPH}")
    print(f"   Bridge: {BRIDGE}/")
    print(f"   Graph report: {BASE / 'memory' / 'graphify-out' / 'GRAPH_REPORT.md'}")

if __name__ == "__main__":
    main()
