#!/usr/bin/env python3
"""HLCO Test Suite - run before public deployment"""

import json
import subprocess
import sys

tests = [
    {"query": "finances", "expected_intent": "financial", "max_tokens": 500},
    {"query": "move plan", "expected_intent": "relocation", "max_tokens": 1500},
    {"query": "ssh", "expected_intent": "ssh", "max_tokens": 500},
    {"query": "unknown_topic_xyz", "expected_intent": "general", "max_tokens": 2000},
    {"query": "hermes", "expected_intent": "agent_config", "max_tokens": 1000},
]

results = []
for test in tests:
    try:
        result = subprocess.run(
            ["python", "engine.py", test["query"], "--budget", str(test["max_tokens"])],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = json.loads(result.stdout)
        passed = (output.get("intent") == test["expected_intent"] and 
                  output.get("budget_used") <= test["max_tokens"])
        results.append({"query": test["query"], "passed": passed, 
                       "tokens": output.get("budget_used")})
    except Exception as e:
        results.append({"query": test["query"], "passed": False, 
                       "error": str(e)})

# Report
passed = sum(1 for r in results if r.get("passed"))
total = len(results)
print(f"Results: {passed}/{total} passed")
for r in results:
    status = "✅" if r.get("passed") else "❌"
    if "tokens" in r:
        print(f"  {status} {r['query']}: {r['tokens']} tokens")
    else:
        print(f"  ❌ {r['query']}: {r.get('error', 'failed')}")

sys.exit(0 if passed == total else 1)
