#!/usr/bin/env python3
"""Gates for the gateway judgment + urgency/point protocol."""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import gateway  # noqa: E402
from chainlib import load_chains, loops_of, tier_order  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        FAILS.append(name)


chains, _ = load_chains(os.path.join(BASE, "chains.yaml"))
by_id = {c["id"]: c for c in chains}

# 1. urgency classification sets the depth budget
u = gateway.classify_urgency("URGENT: production is down, fix it now")
check("urgent detected", u["tier"] == "urgent", u)
check("urgent cap 2", u["cap"] == 2, u["cap"])
n = gateway.classify_urgency("fix the failing tests")
check("default normal", n["tier"] == "normal", n)
check("normal cap 5", n["cap"] == 5, n["cap"])
e = gateway.classify_urgency("someday, no rush, explore classic literature")
check("exploratory detected", e["tier"] == "exploratory", e)
check("exploratory cap 14", e["cap"] == 14, e["cap"])

# 2. urgency changes how many skills run
r = by_id["research-synthesis"]
check("urgent runs 1 loop", len(tier_order(r, "urgent")) == 1, tier_order(r, "urgent"))
check("normal runs more than urgent",
      len(tier_order(r, "normal")) > len(tier_order(r, "urgent")))
check("exploratory runs the most",
      len(tier_order(r, "exploratory")) > len(tier_order(r, "normal")))
nodes_u = sum(len(l["nodes"]) for l in tier_order(r, "urgent"))
nodes_e = sum(len(l["nodes"]) for l in tier_order(r, "exploratory"))
check("urgent plan is fewer nodes", nodes_u < nodes_e, f"{nodes_u} vs {nodes_e}")

# 3. point rule: cost = max(1, power + retries)
led = gateway.Ledger(14)
check("first pass costs 1", led.charge(1, 0) == 1)
check("second gateway costs 2", led.charge(2, 0) == 2)
check("retry costs power+retries", led.charge(3, 1) == 4)
check("power 0 floors at 1", gateway.Ledger(14).charge(0, 0) == 1)
led2 = gateway.Ledger(14)
for p in (1, 2, 3, 4):
    led2.charge(p, 0)
check("four gateways reach base 10", led2.total == 10, led2.total)
check("ledger not exhausted at base 10 (headroom=4)", led2.exhausted is False)
led2.charge(1, 3)
check("ledger reports exhausted at 14", led2.exhausted is True)

# 4. judge never silently passes
v, _ = gateway.judge("claims_cited", {}, r)
check("missing state -> unknown", v == "unknown", v)
v, _ = gateway.judge("claims_cited", {"claims_total": 3, "claims_cited": 3}, r)
check("cited state -> pass", v == "pass", v)
v, _ = gateway.judge("claims_cited", {"claims_total": 3, "claims_cited": 1}, r)
check("partial state -> fail", v == "fail", v)
v, _ = gateway.judge("no_such_predicate", {}, r)
check("unknown predicate -> unknown", v == "unknown", v)

# 5. happy path delivers at the first gateway for an urgent task
ok_state = {"artifact": "report.md", "claims_total": 2, "claims_cited": 2,
            "tests_run": 10, "tests_failed": 0, "listings_candidates": 3,
            "listings_verified": 3, "gaps_total": 2, "gaps_owned": 2,
            "red_test_captured": True, "skill_load_ok": True, "human_approved": True}
res = gateway.simulate(r, "URGENT answer this now", ok_state, chains)
check("urgent happy path delivers", res["outcome"] == "deliver", res["outcome"])
check("urgent spends 1 point", res["total"] == 1, res["total"])
check("urgent stops at loop 1", res["loops_run"] == ["LQ-answer"], res["loops_run"])

# 6. normal path runs deeper
res = gateway.simulate(r, "write a cited research report", ok_state, chains)
check("normal runs two loops", len(res["loops_run"]) == 2, res["loops_run"])
check("normal spends 3 points", res["total"] == 3, res["total"])

# 7. failure pushes back, never passes
bad = dict(ok_state, claims_cited=0, claims_total=5)
res = gateway.simulate(r, "write a cited research report", bad, chains)
check("pushback on failed gate", res["transcript"][-1]["move"] == "hitl" or
      any(t["move"] == "pushback" for t in res["transcript"]), res["transcript"])

# 8. exploratory failure escalates to a human at the cap
res = gateway.simulate(r, "someday explore this, no rush", {}, chains)
check("exploratory escalates to human", res["outcome"] == "hitl", res["outcome"])
check("never exceeds the hard cap", res["total"] <= 14, res["total"])
check("hitl carries a reason", bool(res["transcript"][-1]["reason"]))

# 8b. exploratory retry headroom: single retry on G1/G2 does not trigger premature hitl
led_test = gateway.Ledger(14)
c1 = led_test.charge(1, 0)  # G1 pass 1: 1
c2_fail = led_test.charge(2, 0)  # G2 try 1 (fails): 2
c2_retry = led_test.charge(2, 1)  # G2 try 2 (passes): 3
c3 = led_test.charge(3, 0)  # G3 pass: 3
c4 = led_test.charge(4, 0)  # G4 pass: 4
check("retry total within cap 14", led_test.total <= 14, led_test.total)
check("not exhausted before final loop delivery", led_test.total == 13 and not led_test.exhausted)

# 9. redirect starts a new loop in another chain
sf = by_id["skill-forging"]
st = dict(ok_state, skill_load_ok=False)
res = gateway.simulate(sf, "forge a new skill", st, chains)
red = [t for t in res["transcript"] if t["move"] == "redirect"]
check("failed skill test redirects", bool(red), res["transcript"])
check("redirect target recorded", bool(red) and red[0].get("redirect_to") == "delegated-build",
      red[0] if red else None)
check("redirect runs the new chain's loops",
      "LQ-slice" in res["loops_run"] or "LQ-scope" in res["loops_run"], res["loops_run"])

# 10. structural contract for every chain
for c in chains:
    cid = c["id"]
    check(f"{cid}: 3 urgency tiers", all(t in (c.get("tiers") or {})
                                         for t in ("urgent", "normal", "exploratory")))
    check(f"{cid}: has loops", len(loops_of(c)) >= 1)
    for lp in loops_of(c):
        gw = lp.get("gateway") or {}
        check(f"{cid}/{lp['id']}: goal", bool(lp.get("goal")))
        check(f"{cid}/{lp['id']}: nodes", bool(lp.get("nodes")))
        check(f"{cid}/{lp['id']}: gateway judge", bool(gw.get("judge")))
        check(f"{cid}/{lp['id']}: gateway power 0-10",
              isinstance(gw.get("power"), int) and 0 <= gw["power"] <= 10, gw.get("power"))
        check(f"{cid}/{lp['id']}: pass outcome",
              gw.get("pass") in ("advance", "deliver", "redirect"), gw.get("pass"))
        check(f"{cid}/{lp['id']}: fail outcome",
              gw.get("fail") in ("pushback", "deliver", "redirect", "hitl"), gw.get("fail"))
    last = loops_of(c)[-1]["gateway"]
    check(f"{cid}: last gateway can deliver", last.get("pass") == "deliver", last.get("pass"))

# 11. determinism
a = gateway.simulate(r, "write a cited research report", ok_state, chains)
b = gateway.simulate(r, "write a cited research report", ok_state, chains)
check("deterministic", a == b)

# 12. CLI
out = subprocess.run([sys.executable, os.path.join(BASE, "gateway.py"),
                      "--chain", "research-synthesis", "--task", "do it now",
                      "--state", json.dumps(ok_state)], capture_output=True, text=True)
check("gateway CLI exit 0", out.returncode == 0, out.stderr[-300:])
check("gateway CLI prints tier", "tier=urgent" in out.stdout, out.stdout[:200])

# 13. disk-computed determinism (compute_state_from_disk)
import tempfile
with tempfile.TemporaryDirectory() as td:
    # 13a. artifact_exists & claims_cited
    art = os.path.join(td, "report.md")
    check("disk: artifact missing before creation", gateway.compute_state_from_disk(art, td).get("artifact_exists") is None)
    with open(art, "w", encoding="utf-8") as f:
        f.write("# Report\n- [claim 1](https://example.com/1)\n- [claim 2](https://example.com/2)\n")
    d1 = gateway.compute_state_from_disk(art, td)
    check("disk: artifact_exists detected", d1.get("artifact_exists") is True)
    check("disk: claims_total counted", d1.get("claims_total") == 2, d1.get("claims_total"))
    check("disk: claims_cited counted", d1.get("claims_cited") == 2, d1.get("claims_cited"))
    v, why = gateway.judge("claims_cited", {}, {"end_output": {"artifact": "report.md"}}, td)
    check("disk: judge claims_cited passes from disk", v == "pass", (v, why))

    # 13b. listings_verified
    brief = os.path.join(td, "decision-brief.md")
    with open(brief, "w", encoding="utf-8") as f:
        f.write("| Option | Price | Date | URL |\n|---|---|---|---|\n| Unit A | $1500 | 2026-11-01 | https://rent.example/a |\n| Unit B | $1600 | 2026-11-01 | https://rent.example/b |\n")
    d2 = gateway.compute_state_from_disk(brief, td)
    check("disk: listings_candidates counted", d2.get("listings_candidates") == 2, d2.get("listings_candidates"))
    check("disk: listings_verified counted", d2.get("listings_verified") == 2, d2.get("listings_verified"))
    v, why = gateway.judge("listings_verified", {}, {"end_output": {"artifact": "decision-brief.md"}}, td)
    check("disk: judge listings_verified passes from disk", v == "pass", (v, why))

    # 13c. gaps_owned
    posture = os.path.join(td, "posture-review.md")
    with open(posture, "w", encoding="utf-8") as f:
        f.write("| Asset | Evidence | Owner |\n|---|---|---|\n| fw-01 | log-sample.json | Alice |\n| srv-02 | audit-output.txt | Bob |\n")
    d3 = gateway.compute_state_from_disk(posture, td)
    check("disk: gaps_total counted", d3.get("gaps_total") == 2, d3.get("gaps_total"))
    check("disk: gaps_owned counted", d3.get("gaps_owned") == 2, d3.get("gaps_owned"))
    v, why = gateway.judge("gaps_owned", {}, {"end_output": {"artifact": "posture-review.md"}}, td)
    check("disk: judge gaps_owned passes from disk", v == "pass", (v, why))

    # 13d. skill_loads (9 gates)
    skill_file = os.path.join(td, "SKILL.md")
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write("---\nname: S-test\ndescription: \"Use when testing skill loads cleanly.\"\nmetadata:\n  hermes:\n    boost:\n      role: segment\n      chain: research-synthesis\n      phase: loop\n---\n# Body\n")
    d4 = gateway.compute_state_from_disk(skill_file, td)
    check("disk: skill_loads passes 9-gate compliance", d4.get("skill_load_ok") is True)
    v, why = gateway.judge("skill_loads", {}, {"end_output": {"artifact": "SKILL.md"}}, td)
    check("disk: judge skill_loads passes from disk", v == "pass", (v, why))

print()
if FAILS:
    print(f"FAILED {len(FAILS)}: {FAILS}")
    sys.exit(1)
print("ALL GATEWAY GATES PASSED")
