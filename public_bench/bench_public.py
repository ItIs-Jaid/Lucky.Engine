#!/usr/bin/env python3
"""Lucky.Engine PUBLIC benchmark — framework pack vs full public catalog.

No operator identifiers, no personal memory. Corpus is public/catalog.json only.
Arm A (framework): lucky engine node pack over public_graph.json
Arm B (no framework): entire public catalog text
"""
import json, os, sys, time, urllib.request

OLLAMA = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
NUM_CTX = int(os.environ.get("NUM_CTX", "4096"))
MAX_TOK = int(os.environ.get("MAX_TOK", "80"))

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "bridge"))
import engine  # noqa: E402

QUESTIONS = [
    {"id": "review", "q": "Which skills cover code review?",
     "expect": ["code-review-and-quality", "requesting-code-review", "receiving-code-review"]},
    {"id": "planning", "q": "Which skills are for planning and writing specs?",
     "expect": ["brainstorming", "writing-plans", "spec-driven-development"]},
    {"id": "agents", "q": "Which skills orchestrate parallel agents?",
     "expect": ["dispatching-parallel-agents", "subagent-driven-development"]},
]


def corpus():
    with open(os.path.join(HERE, "public_corpus.txt"), encoding="utf-8") as f:
        return f.read()


def pack(query):
    r = engine.resolve_query(query, budget=500)
    lines = []
    for n in r.get("nodes", []):
        c = " ".join(str(n.get("content") or "").split())[:300]
        lines.append("- %s: %s" % (n.get("label"), c))
    return "\n".join(lines)


def chat(model, system, user):
    payload = {"model": model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}],
               "stream": False,
               "options": {"temperature": 0.0, "num_predict": MAX_TOK, "num_ctx": NUM_CTX}}
    req = urllib.request.Request(OLLAMA + "/api/chat",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=900) as resp:
        d = json.load(resp)
    return {"answer": (d.get("message") or {}).get("content", "").strip(),
            "total_s": round(time.time() - t, 2),
            "prompt_tok": d.get("prompt_eval_count", 0),
            "gen_tok": d.get("eval_count", 0),
            "tok_s": round(d.get("eval_count", 0) / (d.get("eval_duration", 1) / 1e9), 1)}


def grade(ans, expect):
    a = ans.lower().replace(" ", "")
    return sum(1 for e in expect if e.replace(" ", "") in a), len(expect)


def main():
    models = sys.argv[1].split(",")
    device = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    full = corpus()
    print("DEVICE %s | public corpus %d chars (~%d tok)" % (device, len(full), len(full) // 4))
    sysf = "Answer ONLY from the context. If absent say UNKNOWN. Name skills exactly.\n\nCONTEXT:\n"
    rows = []
    for model in models:
        print("\n=== MODEL %s ===" % model)
        try:
            chat(model, "ok", "warm")
        except Exception as e:
            print("  LOAD FAIL %s" % e); continue
        for item in QUESTIONS:
            for arm, ctx in (("framework", pack(item["q"])), ("no_framework", full)):
                try:
                    r = chat(model, sysf + ctx, item["q"])
                except Exception as e:
                    print("  %-9s %-12s ERROR %s" % (item["id"], arm, e)); continue
                hit, tot = grade(r["answer"], item["expect"])
                rows.append(dict(device=device, model=model, qid=item["id"], arm=arm,
                                 ctx_tok=len(ctx) // 4, hit=hit, of=tot, **r))
                print("  %-9s %-12s ctx=%-5d prompt=%-5d %6.1fs %5.1f tok/s score=%d/%d"
                      % (item["id"], arm, len(ctx) // 4, r["prompt_tok"], r["total_s"],
                         r["tok_s"], hit, tot))
                print("      A: %s" % r["answer"].replace("\n", " ")[:150])
    out = os.path.join(HERE, "public_%s.json" % device)
    with open(out, "w") as f:
        json.dump(rows, f, indent=1)
    print("\n=== SUMMARY %s ===" % device)
    for model in models:
        for arm in ("framework", "no_framework"):
            rs = [r for r in rows if r["model"] == model and r["arm"] == arm]
            if not rs:
                continue
            acc = sum(r["hit"] for r in rs) / max(1, sum(r["of"] for r in rs))
            print("%-16s %-13s acc=%.0f%%  avg_lat=%.1fs  avg_ctx_tok=%.0f  avg_prompt_tok=%.0f"
                  % (model, arm, acc * 100, sum(r["total_s"] for r in rs) / len(rs),
                     sum(r["ctx_tok"] for r in rs) / len(rs),
                     sum(r["prompt_tok"] for r in rs) / len(rs)))
    print("\nwrote %s" % out)


if __name__ == "__main__":
    main()
