import json, os, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) > 1:
    tid = sys.argv[1]
else:
    tid = "t001"
# support being called as `python verifier tid` where the solver wrote solutions/<tid>.json
got = json.load(open(os.path.join(BASE, "solutions", tid + ".json")))
exp = json.load(open(os.path.join(BASE, "expected", tid + ".json")))
if got == exp:
    print("PASS"); sys.exit(0)
print("FAIL expected=%r got=%r" % (exp, got)); sys.exit(1)
