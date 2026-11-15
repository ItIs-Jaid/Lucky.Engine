"""Shared config loader for Lucky.Engine 1.5.0. Stdlib only."""
from __future__ import annotations
import os
import re


def _scalar(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v in ("true", "false"):
        return v == "true"
    return v


def load_yaml(path: str):
    """Parse the strict YAML subset used by chains.yaml (maps, lists, inline lists)."""
    lines = []
    for raw in open(path, encoding="utf-8").read().splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))

    def block(i, ind):
        if i < len(lines) and lines[i][1].startswith("- "):
            return plist(i, ind)
        return pmap(i, ind)

    def pmap(i, ind):
        out = {}
        while i < len(lines) and lines[i][0] == ind and not lines[i][1].startswith("- "):
            key, _, val = lines[i][1].partition(":")
            key, val = key.strip(), val.strip()
            if val:
                out[key] = _scalar(val)
                i += 1
            else:
                nxt = i + 1
                if nxt < len(lines) and lines[nxt][0] > ind:
                    out[key], i = block(nxt, lines[nxt][0])
                else:
                    out[key], i = None, nxt
        return out, i

    def plist(i, ind):
        out = []
        while i < len(lines) and lines[i][0] == ind and lines[i][1].startswith("- "):
            body = lines[i][1][2:]
            if ":" not in body:
                out.append(_scalar(body))
                i += 1
                continue
            key, _, val = body.partition(":")
            item = {key.strip(): _scalar(val) if val.strip() else None}
            i += 1
            if i < len(lines) and lines[i][0] > ind:
                extra, i = pmap(i, lines[i][0])
                item.update(extra)
            out.append(item)
        return out, i

    return block(0, lines[0][0])[0]


def load_chains(path: str):
    doc = load_yaml(path)
    chains, defaults = doc.get("chains", []), doc.get("defaults", {})
    base_dir = os.path.dirname(os.path.abspath(path))
    local_path = os.path.join(base_dir, "chains.local.yaml")
    if os.path.exists(local_path):
        try:
            local_doc = load_yaml(local_path)
            local_by_id = {c.get("id"): c for c in local_doc.get("chains", []) if isinstance(c, dict)}
            for c in chains:
                cid = c.get("id")
                if cid in local_by_id:
                    loc = local_by_id[cid]
                    if "keywords" in loc and isinstance(loc["keywords"], list):
                        c["keywords"] = list(dict.fromkeys((c.get("keywords") or []) + loc["keywords"]))
                    if "when" in loc and isinstance(loc["when"], dict) and "any" in loc["when"]:
                        w = c.setdefault("when", {})
                        w["any"] = list(dict.fromkeys((w.get("any") or []) + loc["when"]["any"]))
        except Exception:
            pass
    return chains, defaults


def loops_of(chain):
    """Declared loops, in declaration order."""
    return [l for l in (chain.get("loops") or []) if isinstance(l, dict)]


def tier_order(chain, tier: str):
    """Loop ids to run for this urgency tier. Falls back to all loops."""
    loops = loops_of(chain)
    tiers = chain.get("tiers") or {}
    ids = tiers.get(tier)
    if ids:
        by_id = {l.get("id"): l for l in loops}
        return [by_id[i] for i in ids if i in by_id]
    return loops


def node_ids(chain):
    """Flattened node ids in execution order (loops in order, nodes inside each)."""
    out = []
    for lp in loops_of(chain):
        out.extend(lp.get("nodes") or [])
    return out
