# GATEWAY — judged loops, urgency, and the point budget

A loop is not finished because it ran out of nodes. It is finished when a **gateway judges its
goal** and decides what happens next. Gateways are the only place a chain is allowed to change
direction, and the only place a human is asked for anything.

## 1. Anatomy

```
loop:  goal + nodes + exit predicate
   |
   v
GATEWAY n ── judge(goal) ──┬── pass  -> advance | deliver | redirect
                           └── fail  -> pushback | redirect | hitl
   |
   +-- charge: cost = max(1, power + attempts)
```

| Field | Meaning |
|---|---|
| `goal` | one sentence the gateway can actually judge |
| `judge` | deterministic predicate id (see §2) |
| `power` | 0-10 base-ten weight; defaults to the gateway's position |
| `pass` | `advance` / `deliver` / `redirect` |
| `fail` | `pushback` / `redirect` / `hitl` |
| `redirect_to` | chain id that starts a fresh loop when `pass`/`fail` is `redirect` |

## 2. Predicates (deterministic, computed from disk or state)

| id | pass condition | disk computation |
|---|---|---|
| `artifact_exists` | declared end artifact is on disk | `os.path.isfile(path) and os.path.getsize(path) > 0` |
| `claims_cited` | `claims_cited == claims_total > 0` | Parses Markdown links `[...](...)` in `report.md` |
| `tests_green` | `tests_failed == 0 and tests_run > 0` | Captured test runner output |
| `listings_verified` | `listings_verified >= listings_candidates > 0` | Parses candidate rows with price, live URL, date in `decision-brief.md` |
| `gaps_owned` | `gaps_owned >= gaps_total > 0` | Parses posture table rows for asset, evidence, owner in `posture-review.md` |
| `red_captured` | a failing test was captured this session | Captured test runner output |
| `skill_loads` | the skill loaded cleanly in a live session | Validates frontmatter & 9 /boost 1.5 gates in `SKILL.md` |
| `manual` | explicit approval flag is set | Human approval flag |

`gateway.py` computes these predicates directly from the artifact on disk via `compute_state_from_disk()`, while continuing to support synthetic state dicts in `gateway.simulate()` for hermetic unit tests.
Missing state returns `unknown`, and `unknown` is treated as fail. **There is no silent pass.**

## 3. Urgency sets the depth

| Tier | Cues | Cap | Shape |
|---|---|---|---|
| `urgent` | urgent, asap, now, down, broken, deadline, outage | **2** | 1 loop, deliver fast |
| `normal` | none detected (default) | **5** | 2 loops, then deliver |
| `exploratory` | someday, eventually, no rush, backlog, no urgency | **14** | every loop, gateway to gateway |

Cues are matched on **word boundaries**. Substring matching produced two real bugs in this
project: "know" matched "now" (false urgent), and "research report" matched an exploratory
keyword (false slow).

More urgency -> fewer skills -> faster output. No urgency -> more skills -> more loops ->
more gateways -> eventually a human.

## 4. The point budget

```
cost  = max(1, power + retries)      # first pass (retries=0) costs max(1, power); each retry adds +1
total = sum(cost)                     # cumulative across gateways
cap   = 2 | 5 | 14                    # by urgency tier
hard  = 14                            # never exceeded
```

- Under cap: **forward through the gateway to the next loop.**
- At or over cap: **back to a human** (`hitl`), unless the gateway's outcome is `deliver`.
- Retries cost more: retries=1 on a power-3 gateway is 4 points, so thrash escalates itself.

Worked example (exploratory, four gateways, powers 1/2/3/4):
`1 + 2 + 3 + 4 = 10` -> base sum = 10 against cap 14, leaving 4 points of retry headroom before hitl.

## 5. Terminal rule

The **last loop in the selected tier always delivers** when its gate passes, even if its
declared `pass` is `advance`. This is what lets one chain serve all three urgency tiers without
duplicating config: urgent runs one loop and it delivers; exploratory runs four and the fourth
delivers.

## 6. What a gateway is not

- Not a scoring model. No LLM votes on its own output.
- Not a retry loop. Retries are charged; the cap ends them.
- Not a place to add scope. A gateway advances the declared goal or hands off, nothing else.

## 7. Observability

`gateway.simulate()` returns a transcript you can log to `.lucky/ledger-<chain>.jsonl`:

```json
{"step":2,"chain":"research-synthesis","loop":"L-EVIDENCE-LOOP","judge":"claims_cited",
 "verdict":"pass","reason":"12/12 claims cited in report.md","cost":2,"total":3,"cap":5,
 "move":"deliver"}
```

That transcript is the audit trail: every point spent, every judgment, every hand-off.
