# Where a profile's time goes, in a few named parts: each sample goes to the first part (in PARTS order) found on its
# stack, matched on (function name, source file) from the dev build's names and source comments; the rest is "other".
#   python3 profcat.py <file.cpuprofile> <hazelLib.bc.js> <label> <out.json>
import json, sys, re, collections
prof, lib, label, out = sys.argv[1:5]
p = json.load(open(prof)); lines = open(lib, encoding="utf-8", errors="replace").read().split("\n")
nodes = {n["id"]: n for n in p["nodes"]}; parent = {}
for n in p["nodes"]:
    for c in n.get("children", []): parent[c] = n["id"]
src_cache = {}
def src(i):
    """the .re file the function at node i was compiled from (the first source comment at or below its line)"""
    ln = nodes[i]["callFrame"]["lineNumber"]
    if ln in src_cache: return src_cache[ln]
    f = ""
    for k in range(ln, min(ln + 40, len(lines))):
        m = re.search(r"<<src/([^:>]+\.re):", lines[k])
        if m: f = m.group(1); break
    src_cache[ln] = f; return f
fn = lambda i: nodes[i]["callFrame"]["functionName"]
PARTS = [  # (part, test on (function name, source file))
 ("garbage collection", lambda f, s: f == "(garbage collector)"),
 ("fresh ids (Id.mk: a UUID, bytes to a JS string)", lambda f, s: s.endswith("util/Id.re") and f.startswith("mk")),
 ("pushing types through values (Ascriptions)", lambda f, s: s.endswith("Ascriptions.re")),
 ("the step's rule (Transition)", lambda f, s: s.endswith("Transition.re")),
 ("the evaluator's stages (Evaluator: reuse, probes, state)", lambda f, s: s.endswith("Evaluator.re") or s.endswith("EvaluatorState.re") or s.endswith("IncrEval.re")),
 ("the library's boundary (of_js, to_js, function_of)", lambda f, s: "HazelLib" in s),
]
dt = collections.Counter()
for s, d in zip(p["samples"], p["timeDeltas"]): dt[s] += d / 1000
parts = collections.Counter()
for i, ms in dt.items():
    stack = []; j = i
    while j is not None: stack.append(j); j = parent.get(j)
    got = "other"
    for name, test in PARTS:
        if any(test(fn(k), src(k)) for k in stack): got = name; break
    parts[got] += ms
idle = sum(ms for i, ms in dt.items() if fn(i) in ("(idle)", "(program)"))
total = sum(dt.values())
res = {"label": label, "total_ms": round(total, 1), "parts": [{"part": k, "ms": round(v, 1), "share": round(v / total, 4)} for k, v in parts.most_common()]}
json.dump(res, open(out, "w"), indent=1)
for x in res["parts"]: print(f'{x["share"]*100:5.1f}%  {x["ms"]:8.1f} ms  {x["part"]}')
