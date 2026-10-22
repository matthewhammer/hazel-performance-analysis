# Sum a .cpuprofile: self ms and inclusive ms per function name (inclusive counted once per stack). python3 profsum.py <file> [top]
import json, sys, collections
p = json.load(open(sys.argv[1])); top = int(sys.argv[2]) if len(sys.argv) > 2 else 30
nodes = {n["id"]: n for n in p["nodes"]}; parent = {}
for n in p["nodes"]:
    for c in n.get("children", []): parent[c] = n["id"]
dt = collections.Counter()
for s, d in zip(p["samples"], p["timeDeltas"]): dt[s] += d / 1000
selfms, incl = collections.Counter(), collections.Counter()
name = lambda i: (nodes[i]["callFrame"]["functionName"] or "(anon)") + ":" + str(nodes[i]["callFrame"]["lineNumber"])
for i, ms in dt.items():
    selfms[name(i)] += ms; seen = set(); j = i
    while j is not None:
        nm = name(j)
        if nm not in seen: incl[nm] += ms; seen.add(nm)
        j = parent.get(j)
total = sum(dt.values()); print(f"total {total:.0f} ms")
print("-- self"); [print(f"{ms:8.1f} {100*ms/total:5.1f}% {nm}") for nm, ms in selfms.most_common(top)]
print("-- inclusive"); [print(f"{ms:8.1f} {100*ms/total:5.1f}% {nm}") for nm, ms in incl.most_common(top)]
