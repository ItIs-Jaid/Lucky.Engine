# HLCO Edge Traversal Implementation

## Changes Made

### Modified: `<your-project>/memory/graphify-out/bridge/engine.py`

**New Functions:**
- `get_edges_for_node(graph, node_id)`: Finds all hyperedges connected to a given node
- `get_connected_nodes(graph, node_id, edge_limit=3)`: Follows graph edges to find related nodes, excluding the source node

**Modified Functions:**
- `load_memory_graph()`: Now returns hyperedges alongside nodes and edges
- `resolve_query(query, budget=None, edge_limit=3)`: 
  - Added `edge_limit` parameter to control how many edges to follow per matched node
  - Expands matched context by traversing hyperedges to connected nodes
  - Edge-followed nodes added with confidence=0.6 and source="edge_expansion"
  - Returns `edge_followed_count` in response

## How It Works

1. Query matching identifies primary relevant nodes (unchanged)
2. For each matched node, `get_connected_nodes()` finds related nodes via hyperedges
3. Related nodes are added to results with lower confidence (0.6)
4. Edge traversal respects `edge_limit` parameter (default 3 edges per node)

## Example Output

Query: `live_memory`
- Direct match: `live_memory`
- Edge-expanded: `memory_ssot`, `live_user`, `memory_ssot_ssot_mirror_model`
- All edge-expanded nodes have `source: "edge_expansion"`

## Edge Limit

The `edge_limit` parameter controls maximum edges followed per matched node:
- `edge_limit=1`: Follow 1 hyperedge per node (minimal expansion)
- `edge_limit=3`: Follow up to 3 hyperedges per node (default)
- Higher values = more comprehensive context expansion

## Schema

Response now includes:
```json
{
  "nodes": [...],
  "budget_used": 1550,
  "intent": "memory_structure",
  "edge_followed_count": 3
}
```
