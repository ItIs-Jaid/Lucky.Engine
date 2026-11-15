#!/usr/bin/env python3
"""Lucky.Engine 1.5.0 — deterministic chain router (loops + gateways + urgency).

Task -> root goal -> urgency tier -> ordered loops -> node plan -> gateway contract.

Zero dependencies. Zero tokens. Target <= 100 ms.

Usage:
  python router.py --task "write a cited competitor report" --pack
  python router.py --task "URGENT fix the failing tests now"
  python router.py --task "eventually explore literature" --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chainlib import load_chains, loops_of, tier_order, load_yaml  # noqa: E402,F401
import gateway  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
CHAINS_FILE = os.path.join(BASE, "chains.yaml")
SEGMENT_DIR = os.path.join(BASE, "segments")
PHASES = ("start", "pre_loop", "loop", "end")
_PHASE_RE = re.compile(r"^#\s+\S+\s+[—-]\s+(.+)$", re.M)


def phase_of(body: str) -> str:
    """Phase comes from the card itself: '# <id> — PRE-LOOP'. No duplicated config."""
    m = _PHASE_RE.search(body or "")
    label = (m.group(1).strip().upper() if m else "LOOP")
    if label.startswith("PRE"):
        return "pre_loop"
    if label.startswith("START"):
        return "start"
    if label.startswith("END"):
        return "end"
    return "loop"


def _est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def node_plan(chain, tier="exploratory"):
    """[(node_id, phase, loop_id)] for the loops this urgency tier selects."""
    plan = []
    for lp in tier_order(chain, tier):
        for sid in lp.get("nodes") or []:
            path = os.path.join(SEGMENT_DIR, f"{sid}.md")
            body = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            plan.append((sid, phase_of(body), lp.get("id")))
    return plan


PRIMARY_DOMAIN_TERMS = {
    "research report", "cited", "citation", "report",
    "failing tests", "failing test", "refactor", "production outage",
    "threat model", "security review", "posture review", "posture report", "security gaps",
    "apartment", "relocate", "relocation", "rental", "skill",
}

STEM_MAP = {
    "cite": ["cite", "cited", "citation", "citations"],
    "citation": ["cite", "cited", "citation", "citations"],
    "test": ["test", "tests", "testing"],
    "tests": ["test", "tests", "testing"],
    "move": ["move", "moving", "moves", "moved"],
    "build": ["build", "building", "builds"],
    "report": ["report", "reports", "reporting"],
    "research": ["research", "researching", "researcher"],
    "audit": ["audit", "auditing", "audited"],
    "threat": ["threat", "threats"],
    "gap": ["gap", "gaps"],
    "vuln": ["vuln", "vulns", "vulnerability", "vulnerabilities"],
    "debug": ["debug", "debugging", "debugged"],
    "outage": ["outage", "outages"],
    "error": ["error", "errors"],
    "incident": ["incident", "incidents"],
}


def score(chain, task: str, invoked) -> int:
    if chain.get("id") == "fallback":
        return 0
    text = (task or "").lower()
    keywords = [str(k).lower() for k in (chain.get("keywords") or [])]
    s = 0
    matched_tokens = set()

    # 1. Primary domain terms & multi-word phrases (+2 each)
    for term in sorted(PRIMARY_DOMAIN_TERMS, key=len, reverse=True):
        m = re.search(r"\b" + re.escape(term) + r"\b", text)
        if m:
            term_words = term.split()
            relates = (term in keywords) or any(tw in keywords or any(tw in STEM_MAP.get(kw, []) for kw in keywords) for tw in term_words)
            if relates and not any(t in matched_tokens for t in term_words):
                s += 2
                for t in term_words:
                    matched_tokens.add(t)

    # 2. Secondary keyword hits + word-stem normalization (+1 each)
    for kw in keywords:
        if kw in matched_tokens:
            continue
        stems = STEM_MAP.get(kw, [kw])
        for stem in stems:
            if stem not in matched_tokens and re.search(r"\b" + re.escape(stem) + r"\b", text):
                s += 1
                matched_tokens.add(stem)
                break

    # 3. In-chain invoked skills (+2 each, +3 gate)
    when = chain.get("when") or {}
    hits = set(when.get("any") or []).intersection(invoked)
    s += 2 * len(hits)
    gate = when.get("count_gte")
    if gate is not None and len(invoked) >= int(gate) and hits:
        s += 3
    return s


def _conf(matched: bool, top_score: int) -> float:
    if not matched:
        return 0.0
    return 0.95 if top_score >= 6 else (0.75 if top_score >= 3 else 0.55)


def resolve(task: str, invoked=None, chains=None, defaults=None, urgency=None) -> dict:
    if chains is None:
        chains, defaults = load_chains(CHAINS_FILE)
    defaults = defaults or {}
    invoked = [i.strip() for i in (invoked or []) if i and i.strip()]
    urg = gateway.classify_urgency(task) if urgency is None else {
        "tier": urgency, "cap": min(gateway.TIERS.get(urgency, 14), 14), "signals": ["explicit"]}

    ranked = sorted(((score(c, task, invoked), c) for c in chains),
                    key=lambda pair: pair[0], reverse=True)
    top_score, chain = ranked[0] if ranked else (0, None)
    if chain is None or top_score == 0:
        chain = next((c for c in chains if c.get("id") == "fallback"), ranked[0][1])
        matched = False
    else:
        matched = True

    loops = [{"id": lp.get("id"), "goal": lp.get("goal"), "nodes": lp.get("nodes") or [],
              "gateway": lp.get("gateway") or {}} for lp in tier_order(chain, urg["tier"])]

    segments = []
    for sid, phase, loop_id in node_plan(chain, urg["tier"]):
        path = os.path.join(SEGMENT_DIR, f"{sid}.md")
        exists = os.path.exists(path)
        body = open(path, encoding="utf-8").read() if exists else ""
        segments.append({"id": sid, "phase": phase, "loop": loop_id,
                         "path": path if exists else None, "missing": not exists,
                         "est_tokens": _est_tokens(body)})

    budget = int(defaults.get("max_context_tokens", 350))
    phases = {p: [s["id"] for s in segments if s["phase"] == p] for p in PHASES}
    return {
        "chain": chain.get("id"), "root": chain.get("root"),
        "goal": chain.get("end_output", {}).get("gate"),
        "matched": matched, "confidence": _conf(matched, top_score), "score": top_score,
        "urgency": urg, "loops": loops, "phases": phases, "segments": segments,
        "point_cap": urg["cap"], "gateways": [lp["gateway"] for lp in loops],
        "end_output": chain.get("end_output"),
        "missing_segments": [s["id"] for s in segments if s["missing"]],
        "over_budget": [s["id"] for s in segments if s["est_tokens"] > budget],
        "total_est_tokens": sum(s["est_tokens"] for s in segments),
    }


SAMPLER_SCHEMA = {
    "type": "object",
    "properties": {
        "node": {"type": "string"},
        "gate_passed": {"type": "boolean"},
        "gate_reason": {"type": "string"},
        "output": {"type": "string"},
    },
    "required": ["node", "gate_passed", "gate_reason", "output"],
}


def context_pack(res: dict, zone: int = None, node_id: str = None) -> str:
    if zone == 2:
        node = node_id or ((res.get("segments") or [{}])[0].get("id") or "S-context-pack")
        seg_path = os.path.join(SEGMENT_DIR, f"{node}.md")
        seg_content = open(seg_path, encoding="utf-8").read() if os.path.exists(seg_path) else f"# {node}\nPurpose: active node\n"
        lines = [
            f"ZONE 2 (Dynamic Step Tail - Node: {node})",
            seg_content.strip(),
            "MEMORY SUBGRAPH: [engine.py --format prompt]",
            f"OUTPUT SAMPLER CONTRACT: json_schema={json.dumps(SAMPLER_SCHEMA)}",
        ]
        return "\n\n".join(lines)

    eo = res.get("end_output") or {}
    urg = res.get("urgency") or {}
    lines = [
        f"ROOT: {res['root']}  (chain {res['chain']}, confidence {res['confidence']})",
        f"URGENCY: {urg.get('tier')} -> point cap {urg.get('cap')}"
        + (f" (signals: {', '.join(urg.get('signals') or [])})" if urg.get("signals") else ""),
    ]
    for n, lp in enumerate(res.get("loops") or [], 1):
        gw = lp.get("gateway") or {}
        lines.append(f"LOOP {n} [{lp['id']}]: {lp['goal']}")
        lines.append(f"  nodes: {' -> '.join(lp.get('nodes') or [])}")
        lines.append(f"  GATEWAY {n}: judge={gw.get('judge')} power={gw.get('power')}"
                     f" pass={gw.get('pass')} fail={gw.get('fail')}"
                     + (f" redirect_to={gw['redirect_to']}" if gw.get("redirect_to") else ""))
    lines += [
        f"END OUTPUT: {eo.get('artifact')}",
        f"DONE WHEN: {eo.get('gate')}",
        f"POINTS: cost = power + attempts (min 1). Under {res.get('point_cap')} -> next loop."
        f" At/over -> human in the loop.",
        "RULE: run one loop, then STOP at its gateway. Never load a loop the plan does not name.",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Lucky.Engine 1.5.0 chain router")
    ap.add_argument("--task", required=True)
    ap.add_argument("--invoked", default="")
    ap.add_argument("--urgency", choices=["urgent", "normal", "exploratory"], default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pack", action="store_true")
    ap.add_argument("--zone", choices=[1, 2], type=int, default=None)
    ap.add_argument("--node", default=None)
    ap.add_argument("--chains", default=CHAINS_FILE)
    args = ap.parse_args(argv)

    chains, defaults = load_chains(args.chains)
    res = resolve(args.task, args.invoked.split(","), chains, defaults, args.urgency)
    if args.pack:
        print(context_pack(res, zone=args.zone, node_id=args.node))
    elif args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{res['chain']} -> {res['root']} (conf {res['confidence']}, {res['urgency']['tier']})")
        for n, lp in enumerate(res["loops"], 1):
            gw = lp["gateway"]
            print(f"  LOOP {n} {lp['id']:<12} goal={lp['goal']}")
            print(f"         nodes: {' -> '.join(lp['nodes'])}")
            print(f"         GATEWAY judge={gw.get('judge')} power={gw.get('power')}"
                  f" pass={gw.get('pass')} fail={gw.get('fail')}")
        print(f"  points cap {res['point_cap']} | done when: {res['end_output']['gate']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
