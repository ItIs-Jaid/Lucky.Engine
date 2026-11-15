#!/usr/bin/env python3
"""baseline_solver.py — the LAZY no-plan agent (CONTROL).

Lucky.Engine has NOT been applied. The agent reads task + input and goes straight
to the answer, re-deriving its own plan. Correct implementation, but no scaffold,
no verification gate, no point budget.

This is the CONTROL for AXIS 2 (local): the ONLY difference from the framework
condition is whether the Lucky.Engine deterministic plan is injected.
"""
import json
import sys


def solve(tid, inp):
    if tid == "t001":
        return ["Fizz" if x % 15 == 0 else "Buzz" if x % 5 == 0 else "Fizz" if x % 3 == 0 else x
                for x in range(1, inp["n"] + 1)]
    if tid == "t002":
        return inp["s"][::-1]
    if tid == "t003":
        a, b = 0, 1
        for _ in range(inp["n"]):
            a, b = b, a + b
        return a
    if tid == "t004":
        n = inp["n"]
        return n > 1 and all(n % i for i in range(2, int(n ** 0.5) + 1))
    if tid == "t005":
        r = 1
        for i in range(2, inp["n"] + 1):
            r *= i
        return r
    if tid == "t006":
        return sum(c.lower() in "aeiou" for c in inp["s"])
    if tid == "t007":
        s = inp["s"]
        t = "".join(c.lower() for c in s if c.isalnum())
        return t == t[::-1]
    if tid == "t008":
        return inp["a"] if inp["a"] > inp["b"] else inp["b"]
    if tid == "t009":
        a = list(inp)
        for i in range(len(a)):
            for j in range(len(a) - 1 - i):
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
        return a
    if tid == "t010":
        return " ".join(inp["s"].split()[::-1])
    if tid == "t011":
        out = []
        for x in inp:
            if isinstance(x, list):
                out += solve(tid, {"x": x})
            else:
                out.append(x)
        return out
    if tid == "t012":
        a, b = inp["a"], inp["b"]
        while b:
            a, b = b, a % b
        return a
    raise KeyError("no baseline path for tid=%s" % tid)


if __name__ == "__main__":
    tid = sys.argv[1]
    with open("inputs/%s.json" % tid) as f:
        inp = json.load(f)
    print(json.dumps(solve(tid, inp)))
