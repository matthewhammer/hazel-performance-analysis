# Self time by OCaml source file: each sample goes to the nearest frame on its stack (leaf first) compiled from a .re/.ml
# file (the dev build's source comments); jsoo runtime helpers (caml_*, no source) go to their caller. GC stays apart.
# With an out.json, also writes the time in GROUPS of files (the report's figure).
#   python3 profiles.py <hazelLib.bc.js> <file.cpuprofile> [top] [label out.json]
import json, sys, re, collections
lib, prof = sys.argv[1:3]; top = int(sys.argv[3]) if len(sys.argv) > 3 else 25
lines = open(lib, encoding="utf-8", errors="replace").read().split("\n")
p = json.load(open(prof)); nodes = {n["id"]: n for n in p["nodes"]}; parent = {}
for n in p["nodes"]:
    for c in n.get("children", []): parent[c] = n["id"]
cache = {}
def src(i):
    cf = nodes[i]["callFrame"]; ln = cf["lineNumber"]
    if cf["url"] and "hazel" not in cf["url"] and cf["url"] != "": return None
    if ln < 0: return None
    if ln in cache: return cache[ln]
    f = None
    for k in range(ln, min(ln + 30, len(lines))):
        m = re.search(r"<<((?:src|_build|ocaml|lib)[^:>]*\.(?:re|ml)):", lines[k])
        if m: f = m.group(1); break
    cache[ln] = f; return f
dt = collections.Counter()
for s, d in zip(p["samples"], p["timeDeltas"]): dt[s] += d / 1000
byf = collections.Counter()
for i, ms in dt.items():
    name = nodes[i]["callFrame"]["functionName"]
    if name in ("(garbage collector)", "(idle)", "(program)"): byf[name] += ms; continue
    j, f = i, None
    while j is not None and f is None: f = src(j); j = parent.get(j)
    byf[f or "(no source)"] += ms
total = sum(dt.values())
for f, ms in byf.most_common(top): print(f"{100*ms/total:5.1f}% {ms:8.1f} {f}")

GROUPS = [  # (group, test on the file)
 ("garbage collection", lambda f: f == "(garbage collector)"),
 ("fresh ids (Id.re: a UUID, its bytes made a JS string)", lambda f: f.endswith("util/Id.re")),
 ("pushing types through values (Ascriptions.re)", lambda f: f.endswith("Ascriptions.re")),
 ("the step's rule (Transition.re, PatternMatch.re, Unboxing.re)", lambda f: f.split("/")[-1] in ("Transition.re", "PatternMatch.re", "Unboxing.re")),
 ("the evaluator's stages (Evaluator.re, EvaluatorState.re, IncrEval.re)", lambda f: f.split("/")[-1] in ("Evaluator.re", "EvaluatorState.re", "IncrEval.re")),
 ("trampolines (Trampoline.re)", lambda f: f.endswith("Trampoline.re")),
 ("environments (Environment.re)", lambda f: f.endswith("Environment.re")),
 ("terms and their ids (IdTagged.re, DHExp.re, Exp.re, ...)", lambda f: f.split("/")[-1] in ("IdTagged.re", "DHExp.re", "Exp.re", "TermBase.re", "Grammar.re", "Pat.re", "Typ.re")),
]
if len(sys.argv) > 5:
    g = collections.Counter()
    for f, ms in byf.items():
        g[next((name for name, t in GROUPS if t(f)), "everything else")] += ms
    json.dump({"label": sys.argv[4], "total_ms": round(total, 1), "groups": [{"group": k, "ms": round(v, 1), "share": round(v / total, 4)} for k, v in g.most_common()]}, open(sys.argv[5], "w"), indent=1)
    print("groups:", ", ".join(f"{k} {100*v/total:.0f}%" for k, v in g.most_common()))
