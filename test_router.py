#!/usr/bin/env python3
"""Gates for the router: routing, tiers, phases, budgets, determinism, CLI."""
import os
import py_compile
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import router  # noqa: E402
from chainlib import load_chains, loops_of, tier_order  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print(f"PASS  {name}")
    else:
        print(f"FAIL  {name}  {detail}")
        FAILS.append(name)


for mod in ("router.py", "gateway.py", "chainlib.py"):
    try:
        py_compile.compile(os.path.join(BASE, mod), doraise=True)
        check(f"{mod} compiles", True)
    except Exception as exc:  # noqa: BLE001
        check(f"{mod} compiles", False, str(exc)[:300])

chains, defaults = load_chains(os.path.join(BASE, "chains.yaml"))
budget = int(defaults.get("max_context_tokens", 350))
check("chain count >= 6", len(chains) >= 6, len(chains))

# 1. phase structure on the deepest plan
for c in chains:
    cid = c["id"]
    plan = router.node_plan(c, "exploratory")
    phases = {p: [s for s, ph, _ in plan if ph == p] for p in router.PHASES}
    check(f"{cid}: start 1-2", 1 <= len(phases["start"]) <= 2, len(phases["start"]))
    check(f"{cid}: end 1-2", 1 <= len(phases["end"]) <= 2, len(phases["end"]))
    if cid == "fallback":
        check("fallback: minimal shape", len(plan) == 3, len(plan))
    else:
        check(f"{cid}: pre_loop >= 2", len(phases["pre_loop"]) >= 2, len(phases["pre_loop"]))
    # phases are ordered inside each loop, not across the whole chain
    for lp in loops_of(c):
        seq = [router.PHASES.index(ph) for sid, ph, lid in plan if lid == lp["id"]]
        check(f"{cid}/{lp['id']}: phases ordered within loop", seq == sorted(seq), seq)
        check(f"{cid}/{lp['id']}: loop body <= 3",
              sum(1 for ph in seq if ph == router.PHASES.index("loop")) <= 3, seq)

# 2. every node exists and fits the per-node budget
seen = set()
for c in chains:
    for sid, _, _ in router.node_plan(c, "exploratory"):
        if sid in seen:
            continue
        seen.add(sid)
        path = os.path.join(BASE, "segments", f"{sid}.md")
        check(f"{sid}: exists", os.path.exists(path), path)
        if os.path.exists(path):
            est = max(1, len(open(path, encoding="utf-8").read()) // 4)
            check(f"{sid}: <= {budget} tok (est {est})", est <= budget, est)

# 3. routing
r = router.resolve("write a cited research report on competitors", [], chains, defaults)
check("research -> research-synthesis", r["chain"] == "research-synthesis", r["chain"])
check("research matched", r["matched"] is True)
check("research nodes complete", r["missing_segments"] == [], r["missing_segments"])
check("research normal = 2 loops", len(r["loops"]) == 2, [l["id"] for l in r["loops"]])

r2 = router.resolve("fix the failing tests and refactor the handler",
                    ["subagent-delegation", "agentic-teams", "subagent-driven-development"],
                    chains, defaults)
check("build -> delegated-build", r2["chain"] == "delegated-build", r2["chain"])
check("build pre_loop 3 nodes", len(r2["phases"]["pre_loop"]) == 3, r2["phases"])
check("build ends at the gate node", r2["phases"]["end"] == ["S-gate-verify"], r2["phases"])

r3 = router.resolve("find a rental apartment relocation under 1500", [], chains, defaults)
check("move -> move-and-relocate", r3["chain"] == "move-and-relocate", r3["chain"])

r4 = router.resolve("what is 2 plus 2", [], chains, defaults)
check("unknown -> fallback", r4["chain"] == "fallback", r4["chain"])
check("unknown unmatched", r4["matched"] is False)

# 4. urgency shapes the plan
ru = router.resolve("URGENT: fix the failing tests now", [], chains, defaults)
rn = router.resolve("fix the failing tests, no rush, eventually", [], chains, defaults)
check("urgent tier detected", ru["urgency"]["tier"] == "urgent", ru["urgency"])
check("urgent plan is shorter", len(ru["segments"]) < len(rn["segments"]),
      f"{len(ru['segments'])} vs {len(rn['segments'])}")
check("explicit urgency override", router.resolve("x", [], chains, defaults,
      "exploratory")["urgency"]["tier"] == "exploratory")

# 5. count_gte semantics: +2 per in-chain skill, +3 gate
r5 = router.resolve("fix tests", ["subagent-delegation", "agentic-teams"], chains, defaults)
r6 = router.resolve("fix tests",
                    ["subagent-delegation", "agentic-teams", "subagent-driven-development"],
                    chains, defaults)
check("count_gte below threshold", r5["score"] == 6, r5["score"])
check("count_gte fires: +2 hit +3 gate", r6["score"] == r5["score"] + 5, r6["score"])

# 6. determinism
a = router.resolve("harden the homelab security posture", [], chains, defaults)
b = router.resolve("harden the homelab security posture", [], chains, defaults)
check("deterministic", a == b)
check("security -> security-review", a["chain"] == "security-review", a["chain"])

# 7. context pack
pack = router.context_pack(a)
check(f"pack <= {budget} tok (est {len(pack)//4})", len(pack) // 4 <= budget)
check("pack names loops and gateways", "LOOP 1" in pack and "GATEWAY 1" in pack, pack[:200])
check("pack states the point rule", "POINTS:" in pack)
check("pack states done-when", "DONE WHEN:" in pack)

# 8. hygiene
src = open(os.path.join(BASE, "router.py"), encoding="utf-8").read()
for bad in ("yaml", "requests", "numpy", "subprocess"):
    check(f"no import {bad}", f"import {bad}" not in src)

# 9. CLI
out = subprocess.run([sys.executable, os.path.join(BASE, "router.py"),
                      "--task", "write a cited report", "--pack"],
                     capture_output=True, text=True)
check("CLI exit 0", out.returncode == 0, out.stderr[-300:])
check("CLI prints ROOT", "ROOT:" in out.stdout, out.stdout[:200])
check("CLI prints URGENCY", "URGENCY:" in out.stdout, out.stdout[:200])

# 10. two-zone prefix-safe packing & sampler schema
check("SAMPLER_SCHEMA valid", "gate_passed" in router.SAMPLER_SCHEMA.get("properties", {}))
pack_z2 = router.context_pack(a, zone=2)
check("pack zone 2 outputs dynamic tail", "ZONE 2" in pack_z2 and "OUTPUT SAMPLER CONTRACT" in pack_z2)
out_z2 = subprocess.run([sys.executable, os.path.join(BASE, "router.py"),
                         "--task", "write a cited report", "--pack", "--zone", "2"],
                        capture_output=True, text=True)
check("CLI zone 2 exit 0", out_z2.returncode == 0, out_z2.stderr[-300:])
check("CLI zone 2 prints dynamic tail", "ZONE 2" in out_z2.stdout, out_z2.stdout[:200])

print()
if FAILS:
    print(f"FAILED {len(FAILS)}: {FAILS}")
    sys.exit(1)
print("ALL ROUTER GATES PASSED")
