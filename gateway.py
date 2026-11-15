#!/usr/bin/env python3
"""Lucky.Engine 1.5.0 — gateway judgment + urgency/point protocol.

A loop is not "done" because it finished. It is done when a gateway judges its goal
and either advances it, pushes it back, redirects it to another skill, delivers to the
user, or escalates to a human.

Points: cost = max(1, power + retries). Cap is set by urgency:
  urgent 2 · normal 5 · exploratory 14   (hard ceiling 14, always)

Exit rule: under cap -> forward through the gateway to the next loop.
           at/over cap -> push back to a human unless the gateway's outcome is deliver.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chainlib import load_chains, loops_of, tier_order  # noqa: E402

TIERS = {"urgent": 2, "normal": 5, "exploratory": 14}
HARD_CAP = 14

# Whole-word cues only. Substring matching misreads "know" as "now" and
# "research report" as an exploratory signal — both were real bugs.
URGENT_WORDS = (
    "urgent", "asap", "immediately", "right now", "now", "emergency", "down",
    "broken", "deadline", "today", "critical", "outage", "blocked", "hurry",
)
EXPLORE_WORDS = (
    "someday", "eventually", "no rush", "whenever", "long term", "long-term",
    "backlog", "think about", "no urgency", "take your time", "explore later",
    "when you get a chance",
)


def _hits(words, text):
    return [w for w in words if re.search(r"\b" + re.escape(w) + r"\b", text)]


def classify_urgency(prompt: str) -> dict:
    t = (prompt or "").lower()
    u = _hits(URGENT_WORDS, t)
    e = _hits(EXPLORE_WORDS, t)
    if u:
        tier, signals = "urgent", u
    elif e:
        tier, signals = "exploratory", e
    else:
        tier, signals = "normal", []
    return {"tier": tier, "cap": min(TIERS[tier], HARD_CAP), "signals": signals}


class Ledger:
    """Append-only point accounting for gateway traversals."""

    def __init__(self, cap: int):
        self.cap = min(int(cap), HARD_CAP)
        self.total = 0
        self.events = []

    def charge(self, power: int, retries: int) -> int:
        # first pass (retries=0) costs max(1, power); each retry adds +1
        cost = max(1, int(power) + int(retries))
        self.total = min(self.cap, self.total + cost)
        return cost

    @property
    def exhausted(self) -> bool:
        return self.total >= self.cap


def compute_state_from_disk(artifact_path: str = "", workspace_dir: str = ".") -> dict:
    """Populate gateway state deterministically from real files on disk. Stdlib only."""
    state = {}
    target = ""
    if artifact_path:
        target = artifact_path if os.path.isabs(artifact_path) else os.path.join(workspace_dir, artifact_path)

    # 1. artifact_exists
    if target and os.path.isfile(target):
        if os.path.getsize(target) > 0:
            state["artifact"] = target
            state["artifact_exists"] = True

    # 2. claims_cited (e.g. report.md)
    report_file = target if (target and os.path.isfile(target) and target.endswith(".md")) else os.path.join(workspace_dir, "report.md")
    if os.path.isfile(report_file):
        try:
            with open(report_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            claim_lines = [l.strip() for l in content.splitlines() if l.strip().startswith(("- ", "* ", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))]
            if claim_lines:
                state["claims_total"] = len(claim_lines)
                link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
                cited = 0
                for cl in claim_lines:
                    m = link_re.search(cl)
                    if m:
                        dest = m.group(2).strip()
                        if dest.startswith(("http://", "https://")) or os.path.exists(dest) or os.path.exists(os.path.join(workspace_dir, dest)):
                            cited += 1
                state["claims_cited"] = cited
        except Exception:
            pass

    # 3. listings_verified (e.g. decision-brief.md)
    brief_file = target if (target and os.path.isfile(target) and "decision-brief" in target) else os.path.join(workspace_dir, "decision-brief.md")
    if os.path.isfile(brief_file):
        try:
            with open(brief_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            rows = [l.strip() for l in content.splitlines() if l.strip().startswith("|") and not l.strip().startswith("|---") and "---" not in l]
            if len(rows) > 1 and any(k in rows[0].lower() for k in ("candidate", "listing", "name", "option", "unit")):
                candidate_rows = rows[1:]
            else:
                candidate_rows = rows
            if candidate_rows:
                state["listings_candidates"] = len(candidate_rows)
                verified = 0
                url_re = re.compile(r'https?://[^\s|]+')
                price_re = re.compile(r'\$\d+')
                date_re = re.compile(r'\d{4}-\d{2}-\d{2}')
                for row in candidate_rows:
                    if url_re.search(row) and price_re.search(row) and date_re.search(row):
                        verified += 1
                state["listings_verified"] = verified
        except Exception:
            pass

    # 4. gaps_owned (e.g. posture-review.md)
    posture_file = target if (target and os.path.isfile(target) and "posture" in target) else os.path.join(workspace_dir, "posture-review.md")
    if os.path.isfile(posture_file):
        try:
            with open(posture_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            rows = [l.strip() for l in content.splitlines() if l.strip().startswith("|") and "---" not in l]
            if len(rows) > 1:
                header = [c.strip().lower() for c in rows[0].split("|")[1:-1]]
                data_rows = rows[1:]
                state["gaps_total"] = len(data_rows)
                owned = 0
                asset_idx = next((i for i, h in enumerate(header) if "asset" in h), 0)
                evidence_idx = next((i for i, h in enumerate(header) if "evidence" in h), 1)
                owner_idx = next((i for i, h in enumerate(header) if "owner" in h), 2)
                for r in data_rows:
                    cols = [c.strip() for c in r.split("|")[1:-1]]
                    if len(cols) > max(asset_idx, evidence_idx, owner_idx):
                        if cols[asset_idx] and cols[evidence_idx] and cols[owner_idx]:
                            owned += 1
                state["gaps_owned"] = owned
        except Exception:
            pass

    # 5. skill_loads (e.g. SKILL.md)
    skill_file = target if (target and os.path.isfile(target) and target.endswith("SKILL.md")) else os.path.join(workspace_dir, "SKILL.md")
    if os.path.isfile(skill_file):
        try:
            sz = os.path.getsize(skill_file)
            with open(skill_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            ok = True
            if sz > 10240:
                ok = False
            fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not fm_match:
                ok = False
            else:
                fm = fm_match.group(1)
                desc_match = re.search(r'^description:\s*(.+)$', fm, re.MULTILINE)
                if not desc_match:
                    ok = False
                else:
                    desc = desc_match.group(1).strip().strip('"').strip("'")
                    if len(desc) > 57 or not desc.startswith("Use when"):
                        ok = False
                if not re.search(r'role:\s*(root|segment|loop)', fm):
                    ok = False
                if not re.search(r'chain:\s*[\w-]+', fm):
                    ok = False
                if not re.search(r'phase:\s*(start|pre_loop|loop|end)', fm):
                    ok = False
            state["skill_load_ok"] = ok
        except Exception:
            state["skill_load_ok"] = False

    return state


def judge(kind: str, state: dict, chain: dict, workspace_dir: str = "."):
    """Deterministic judgment. Returns (verdict, reason). Never a silent pass."""
    s = dict(state) if state else {}
    st = s.get("artifact") or ""
    want = ((chain.get("end_output") or {}).get("artifact")) or ""

    # Populate missing keys deterministically from disk
    target_path = st or want
    if target_path or (workspace_dir and os.path.exists(workspace_dir)):
        disk_s = compute_state_from_disk(target_path, workspace_dir)
        for k, v in disk_s.items():
            if k not in s:
                s[k] = v
        if not st and "artifact" in disk_s:
            st = disk_s["artifact"]

    def need(*keys):
        missing = [k for k in keys if k not in s]
        return missing

    if kind == "artifact_exists":
        check_path = st or want
        if check_path and os.path.isfile(check_path) and os.path.getsize(check_path) > 0:
            return "pass", f"artifact present: {check_path}"
        if st and (st == want or want in st or st.endswith(os.path.basename(want) or "\0")):
            return "pass", f"artifact present: {st}"
        return "fail", f"artifact missing (want {want!r}, have {st!r})"

    if kind == "claims_cited":
        miss = need("claims_total", "claims_cited")
        if miss:
            return "unknown", f"state missing: {miss}"
        if s["claims_total"] <= 0:
            return "fail", "no claims extracted"
        if s["claims_cited"] == s["claims_total"]:
            return "pass", f"{s['claims_cited']}/{s['claims_total']} cited"
        return "fail", f"{s['claims_cited']}/{s['claims_total']} cited"

    if kind == "tests_green":
        miss = need("tests_run", "tests_failed")
        if miss:
            return "unknown", f"state missing: {miss}"
        if s["tests_run"] <= 0:
            return "fail", "no tests executed"
        return ("pass", f"{s['tests_run']} run, 0 failed") if s["tests_failed"] == 0 \
            else ("fail", f"{s['tests_failed']} failing")

    if kind == "listings_verified":
        miss = need("listings_candidates", "listings_verified")
        if miss:
            return "unknown", f"state missing: {miss}"
        if s["listings_candidates"] <= 0:
            return "fail", "no candidates"
        return ("pass", f"{s['listings_verified']}/{s['listings_candidates']} verified") \
            if s["listings_verified"] >= s["listings_candidates"] \
            else ("fail", f"{s['listings_verified']}/{s['listings_candidates']} verified")

    if kind == "gaps_owned":
        miss = need("gaps_total", "gaps_owned")
        if miss:
            return "unknown", f"state missing: {miss}"
        return ("pass", f"{s['gaps_owned']}/{s['gaps_total']} owned") \
            if s["gaps_owned"] >= s["gaps_total"] > 0 else ("fail", "unowned gaps remain")

    if kind == "skill_loads":
        return ("pass", "skill loaded") if s.get("skill_load_ok") is True \
            else ("fail", "skill did not load cleanly")

    if kind == "red_captured":
        return ("pass", "failing test captured") if s.get("red_test_captured") is True \
            else ("fail", "no failing test captured")

    if kind == "manual":
        return ("pass", "human approved") if s.get("human_approved") is True \
            else ("fail", "awaiting human approval")

    return "unknown", f"no predicate named {kind!r}"


def simulate(chain, prompt, state, chains=None, max_steps=24, workspace_dir="."):
    """Run the chain through its gateways. Pure function; no I/O, no model calls."""
    chains = chains or [chain]
    by_chain = {c.get("id"): c for c in chains}
    urg = classify_urgency(prompt)
    led = Ledger(urg["cap"])

    cur = chain
    order = tier_order(cur, urg["tier"])
    attempts = {}
    transcript = []
    outcome = "hitl"

    for _ in range(max_steps):
        if not order:
            outcome = "deliver"
            break
        lp = order[0]
        n = len(transcript) + 1
        gw = lp.get("gateway") or {}
        verdict, why = judge(gw.get("judge", "manual"), state, cur, workspace_dir)
        power = int(gw.get("power", n))
        a = attempts.get((cur.get("id"), lp.get("id")), 0)
        cost = led.charge(power, a)

        passed = verdict == "pass"
        move = gw.get("pass", "advance") if passed else gw.get("fail", "pushback")

        # the last loop in the plan is the delivery loop, whatever its config says
        if passed and len(order) == 1 and move == "advance":
            move = "deliver"

        # cap reached mid-chain: hand to a human instead of grinding
        if led.exhausted and move in ("advance", "pushback", "redirect"):
            move = "hitl"

        transcript.append({
            "step": n, "chain": cur.get("id"), "loop": lp.get("id"),
            "goal": lp.get("goal"), "judge": gw.get("judge"),
            "verdict": verdict, "reason": why, "cost": cost,
            "total": led.total, "cap": led.cap, "move": move,
        })

        if move == "pushback":
            attempts[(cur.get("id"), lp.get("id"))] = a + 1
            continue
        if move == "deliver":
            outcome = "deliver"
            break
        if move == "hitl":
            outcome = "hitl"
            break
        if move == "redirect":
            nxt = by_chain.get(gw.get("redirect_to"))
            if not nxt:
                outcome, move = "hitl", "hitl"
                transcript[-1]["move"] = "hitl"
                transcript[-1]["reason"] += " | redirect target missing"
                break
            cur = nxt
            order = tier_order(cur, urg["tier"])
            transcript[-1]["redirect_to"] = cur.get("id")
            continue
        # advance
        order = order[1:]

    return {
        "tier": urg["tier"], "cap": led.cap, "total": led.total,
        "signals": urg["signals"], "outcome": outcome,
        "loops_run": [t["loop"] for t in transcript],
        "transcript": transcript,
    }


def main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(description="gateway simulator")
    ap.add_argument("--chain", required=True)
    ap.add_argument("--task", default="")
    ap.add_argument("--state", default="{}", help="JSON object of judged facts")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    chains, _ = load_chains(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chains.yaml"))
    chain = next((c for c in chains if c.get("id") == a.chain), None)
    if not chain:
        print(f"no such chain: {a.chain}")
        return 2
    res = simulate(chain, a.task, json.loads(a.state), chains)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"tier={res['tier']} cap={res['cap']} points={res['total']} -> {res['outcome']}")
        for t in res["transcript"]:
            print(f"  {t['step']}. {t['loop']:<14} {t['verdict']:<7} +{t['cost']}"
                  f" ({t['total']}/{t['cap']})  {t['move']}  - {t['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
