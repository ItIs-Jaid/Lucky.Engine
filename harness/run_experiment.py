#!/usr/bin/env python3
"""harness/run_experiment.py — Lucky.Engine 1.5.0 eval orchestrator.

Runs two axes:

  AXIS 1 (router): deterministic routing accuracy. No LLM.
      python harness/run_experiment.py --axis1

  AXIS 2 (agent ablation): same agent solves the tasks WITH the Lucky.Engine
      chain pre-pass vs WITHOUT. Measures correctness, tokens, rework, gate.
      python harness/run_experiment.py --axis2 local       # deterministic stand-in
      python harness/run_experiment.py --axis2 ollama      # real local ollama model

Modes:
  local : baseline_solver.py (no plan) vs lucky_solver.py (follows Lucky.Engine plan)
  ollama: ollama_solver.py --framework runs the model on the Lucky.Engine plan;
          --framework off runs the model on task only.

Outputs raw measurements to results/<axis>.jsonl.
"""

import argparse
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = BASE
sys.path.insert(0, PROJECT)
import router  # noqa: E402
from chainlib import load_chains  # noqa: E402
from evals.routing import EVAL as ROUTING_EVAL  # noqa: E402

BENCHMARK = os.path.join(BASE, "benchmark")
RESULTS = os.path.join(BASE, "results")
os.makedirs(RESULTS, exist_ok=True)

META = json.load(open(os.path.join(BENCHMARK, "meta.json")))
TASK_DIR = os.path.join(BENCHMARK, "inputs")


def task_paths(tid: str):
    return os.path.join(TASK_DIR, tid + ".json"), os.path.join(BENCHMARK, "expected", tid + ".json"), \
        os.path.join(BENCHMARK, "verifiers", tid + ".py")


# ---------------------------------------------------------------- AXIS 1

def run_axis1():
    """Routing accuracy: task -> chain. Deterministic."""
    chains, _ = load_chains(os.path.join(PROJECT, "chains.yaml"))
    by_id = {c["id"]: c for c in chains}
    results = []
    print("AXIS 1 — Lucky.Engine routing accuracy (task -> chain)")
    print("=" * 70)
    gt = {}
    for tid, task, exp in ROUTING_EVAL:
        gt[tid] = exp
        res = router.resolve(task)
        ok = res["chain"] == exp
        results.append({"tid": tid, "task": task, "expected": exp, "predicted": res["chain"],
                        "confidence": res["confidence"], "score": res["score"], "matched": res["matched"],
                        "ok": ok})
        print(f"  {tid:<6} expected={exp:<20} predicted={res['chain']:<20} "
              f"{'OK' if ok else 'X'} conf={res['confidence']:.2f}")
    n = len(results)
    correct = sum(1 for r in results if r["ok"])
    acc = correct / n
    from collections import Counter
    print("-" * 70)
    print(f"accuracy = {acc:.2f}  ({correct}/{n})")
    for c in ["research-synthesis", "delegated-build", "move-and-relocate",
              "skill-forging", "security-review"]:
        gt_c = sum(1 for r in results if r["expected"] == c)
        pred_c = sum(1 for r in results if r["predicted"] == c)
        good = sum(1 for r in results if r["predicted"] == c and r["expected"] == c)
        p = good / pred_c if pred_c else 0
        r_ = good / gt_c if gt_c else 0
        f1 = 2 * p * r_ / (p + r_) if (p + r_) else 0
        print(f"  {c:<20} P={p:.2f} R={r_:.2f} F1={f1:.2f} (gt={gt_c}, pred={pred_c})")
    out = {"axis": 1, "metric": "routing_accuracy", "accuracy": round(acc, 4),
           "n_tasks": n, "correct": correct, "per_chain": []}
    with open(os.path.join(RESULTS, "axis1_routing.json"), "w") as f:
        json.dump(out, f, indent=2)
    return results


# ---------------------------------------------------------------- AXIS 2 (local)

def solve_task(solver, tid):
    inp, _, _ = task_paths(tid)
    cmd = [sys.executable, os.path.join(BASE, solver), tid]
    try:
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=BENCHMARK, capture_output=True, text=True, timeout=60)
        dt = time.time() - t0
        out = proc.stdout.strip()
        return {"tid": tid, "exit": proc.returncode, "stdout": out, "stderr": proc.stderr[-300:],
                "time": round(dt, 3), "raw": True}
    except Exception as exc:
        return {"tid": tid, "exit": -1, "stdout": "", "stderr": str(exc)[:300], "time": 0, "raw": False}


def score_solution(tid, stdout, expected_file, verifier):
    import os
    sol_path = os.path.join(BENCHMARK, "solutions", tid + ".json")
    os.makedirs(os.path.dirname(sol_path), exist_ok=True)
    payload = stdout.strip()
    for line in payload.splitlines():
        if line.startswith("SOLUTION="):
            payload = line[len("SOLUTION="):].strip()
            break
    with open(sol_path, "w") as fh:
        try:
            json.loads(payload)
            fh.write(payload)
        except Exception:
            fh.write(json.dumps(payload))
    cmd = [sys.executable, verifier, tid]
    try:
        proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, timeout=30)
        verdict = proc.returncode == 0
        detail = proc.stdout.strip() or proc.stderr.strip()
        return {"verdict": "PASS" if verdict else "FAIL", "detail": detail}
    finally:
        if os.path.exists(sol_path):
            os.unlink(sol_path)


def run_axis2_local(agent="lucky"):
    """Baseline (no plan) vs Framework (Lucky.Engine plan). Deterministic stand-in."""
    print("\nAXIS 2 (local) — agent without plan vs agent with Lucky.Engine plan")
    print("=" * 70)
    baseline, framework = "scripts/baseline_solver.py", "scripts/lucky_solver.py"
    rows = []
    for t in META["tasks"]:
        tid, task, exp = t["id"], t["prompt"], t.get("category", "")
        # baseline
        b = solve_task(baseline, tid)
        b["expected"] = exp
        # framework: agent given the Lucky.Engine plan
        f = solve_task(framework, tid)
        f["expected"] = exp
        # score
        _, exp_file, _ = task_paths(tid)
        b_sc = score_solution(tid, b["stdout"], exp_file, os.path.join(BENCHMARK, "verifiers", tid + ".py"))
        f_sc = score_solution(tid, f["stdout"], exp_file, os.path.join(BENCHMARK, "verifiers", tid + ".py"))
        rows.append({"tid": tid, "task": task, "expected": exp,
                     "baseline_exit": b["exit"], "baseline_pass": b_sc["verdict"],
                     "framework_exit": f["exit"], "framework_pass": f_sc["verdict"],
                     "baseline_tokens": len(b["stdout"]), "framework_tokens": len(f["stdout"]),
                     "baseline_time": b["time"], "framework_time": f["time"]})
        print(f"  {tid:<6} baseline={b_sc['verdict']:<5} framework={f_sc['verdict']:<5} "
              f"conf={f['stdout'][:40]}")
    out = {"axis": 2, "mode": "local", "agent": "deterministic", "rows": rows}
    acc_b = sum(1 for r in rows if r["baseline_pass"] == "PASS") / len(rows)
    acc_f = sum(1 for r in rows if r["framework_pass"] == "PASS") / len(rows)
    out["summary"] = {"baseline_accuracy": round(acc_b, 4), "framework_accuracy": round(acc_f, 4),
                      "n_tasks": len(rows)}
    with open(os.path.join(RESULTS, "axis2_local.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("=" * 70)
    print(f"baseline_acc={acc_b:.2f}  framework_acc={acc_f:.2f}")
    return rows


# ---------------------------------------------------------------- AXIS 2 (ollama)

OLLAMA_DEFAULT = os.path.join(BASE, "ollama")

def ollama_solve(tid, framework, model="tinyllama"):
    inp, _, _ = task_paths(tid)
    system = ""
    if framework:
        tasks_by_id = {t["id"]: t for t in META["tasks"]}
        pack = router.context_pack(router.resolve(tasks_by_id[tid]["prompt"]))
        system = pack + "\n\nTASK:\n"
    else:
        system = "Solve the task directly.\n\nTASK:\n"
    payload = {
        "model": model,
        "prompt": system + json.dumps(json.load(open(inp))),
        "stream": False,
    }
    proc = subprocess.run(
        ["curl", "-s", "--max-time", "120", "-X", "POST",
         "http://localhost:11434/api/generate",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=150)
    return proc.stdout or proc.stderr


def run_axis2_ollama(model="tinyllama"):
    print("\nAXIS 2 (ollama) — real model with vs without Lucky.Engine plan")
    print("=" * 70)
    rows = []
    for t in META["tasks"]:
        tid, task, exp = t["id"], t["prompt"], t.get("category", "")
        t0 = time.time()
        b_out = ollama_solve(tid, framework=False, model=model)
        b_t = time.time() - t0
        t0 = time.time()
        f_out = ollama_solve(tid, framework=True, model=model)
        f_t = time.time() - t0
        # placeholder scoring: true-live scoring needs a local verifier; mark as pending
        rows.append({"tid": tid, "task": task, "expected": exp,
                     "baseline_stdout_len": len(b_out), "framework_stdout_len": len(f_out),
                     "baseline_time": round(b_t, 3), "framework_time": round(f_t, 3),
                     "scored": False, "note": "scoring pending local verifier"})
        print(f"  {tid:<6} baseline={len(b_out)}f ({b_t:.1f}s) framework={len(f_out)}f ({f_t:.1f}s) scored={False}")
    out = {"axis": 2, "mode": "ollama", "model": model, "rows": rows}
    with open(os.path.join(RESULTS, "axis2_ollama.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print("=" * 70)
    return rows


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--axis1", action="store_true", help="run routing-accuracy eval")
    ap.add_argument("--axis2", choices=["local", "ollama"], help="run agent ablation")
    ap.add_argument("--model", default="tinyllama", help="ollama model name")
    args = ap.parse_args()

    if args.axis1:
        run_axis1()
    if args.axis2:
        if args.axis2 == "local":
            run_axis2_local()
        else:
            # ollama: require server up; report if not reachable
            try:
                ping = subprocess.run(["curl", "-s", "--max-time", "5", "http://localhost:11434/api/version"],
                                      capture_output=True, text=True, timeout=10)
                if ping.returncode != 0:
                    print("NOTE: no ollama server at localhost:11434 — running local deterministic mode only.")
                    run_axis2_local()
                else:
                    run_axis2_ollama(args.model)
            except Exception as exc:
                print("NOTE: ollama unavailable:", exc)
                run_axis2_local()
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
