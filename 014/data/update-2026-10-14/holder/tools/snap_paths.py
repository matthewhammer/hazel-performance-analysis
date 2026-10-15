"""^ticket(58): retaining paths in an indexed heap snapshot (snap_index.py).
  python3 snap_paths.py <file.heapsnapshot> <string value> [<max paths>]
For every string node with that value: its retainers, and for each the
shortest path from the root (BFS over non-weak edges), with long runs of
the same step collapsed."""
import json, sys
import numpy as np
f, want = sys.argv[1], sys.argv[2]; maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 6
z = np.load(f + ".npz"); j = json.load(open(f + ".json"))
meta, S = j["meta"], j["strings"]
nodes, edges, first, parent, pedge, dist = (z[k] for k in ("nodes", "edges", "first", "parent", "pedge", "dist"))
NT, ET = meta["node_types"][0], meta["edge_types"][0]
NF = len(meta["node_fields"])
SIZE = meta["node_fields"].index("self_size")
def nlabel(i):
    t = NT[nodes[i, 0]]; nm = S[nodes[i, 1]]
    if t in ("string", "concatenated string", "sliced string"): return f'"{nm[:30]}"'
    return f"{t}:{nm[:50]}" if nm else t
def elabel(e):
    t = ET[edges[e, 0]]; x = edges[e, 1]
    return f"[{x}]" if t in ("element", "hidden") else f"{t}:{S[x][:40]}"
def path(i):
    out = []
    while i != 0:
        out.append((pedge[i], i)); i = parent[i]
    out.reverse()
    return out
def show(p):
    steps = [f"--{elabel(e)}--> {nlabel(i)}" for e, i in p]
    # collapse runs of a repeating 1-, 2- or 3-step pattern
    out, k = [], 0
    while k < len(steps):
        for w in (1, 2, 3):
            pat = steps[k:k + w]; r = 1
            while steps[k + r * w: k + (r + 1) * w] == pat: r += 1
            if r >= 4:
                out.append(f"  ( {'  '.join(pat)} ) x {r}"); k += r * w; break
        else:
            out.append("  " + steps[k]); k += 1
    return "\n".join(out)
sidx = [i for i, s in enumerate(S) if s == want]
targets = np.nonzero(np.isin(nodes[:, 1], sidx) & np.isin(nodes[:, 0], [NT.index("string")]))[0]
print(f"{len(targets)} string node(s) with value {want!r}")
to = edges[:, 2] // NF
for t in targets[:3]:
    ret = np.nonzero(to == t)[0]
    src = np.searchsorted(first, ret, side="right") - 1
    print(f"\nnode {t}: dist {dist[t]}, {len(ret)} retainers")
    kinds = {}
    for e, s in zip(ret, src):
        kinds.setdefault(nlabel(s) + " " + elabel(e), []).append(s)
    for k, v in sorted(kinds.items(), key=lambda kv: -len(kv[1]))[:10]:
        print(f"  {len(v):6d} x {k}  (dist {min(dist[v])}..{max(dist[v])})")
    seen = 0
    for e, s in sorted(zip(ret, src), key=lambda es: dist[es[1]])[:maxp]:
        print(f"\n path to retainer {s} (dist {dist[s]}):\n" + show(path(s)))
