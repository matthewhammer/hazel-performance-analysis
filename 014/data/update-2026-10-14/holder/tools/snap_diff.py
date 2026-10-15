"""^ticket(58): which old objects do the new ones hang from? For two
snapshots of one session (A before, B after), the nodes of B whose ids A
lacks are new. On B's BFS tree (snap_index.py), each new node belongs to
the first new node on its path below an old one (its attachment); the
attachments' old parents, by new bytes below them, are printed with their
paths from the root.
  python3 snap_diff.py <A.heapsnapshot> <B.heapsnapshot> [<top>]"""
import json, sys
import numpy as np
fa, fb = sys.argv[1], sys.argv[2]; top = int(sys.argv[3]) if len(sys.argv) > 3 else 12
sys.argv = [sys.argv[0], fb, "\x00none"]
exec(open(__file__.replace("snap_diff.py", "snap_paths.py")).read().split("sidx = ")[0])
ID = meta["node_fields"].index("id")
ida = np.load(fa + ".npz")["nodes"][:, ID]
new = ~np.isin(nodes[:, ID], ida); del ida
size = nodes[:, SIZE]
print(f"B: {len(nodes)} nodes, {int(new.sum())} new, {size[new].sum() / 2**20:.1f} MB new self size")
order = np.argsort(dist, kind="stable"); order = order[dist[order] >= 0]
cuts = np.searchsorted(dist[order], np.arange(dist.max() + 2))
att = np.full(len(nodes), -1, np.int64)
for L in range(1, dist.max() + 1):
    idx = order[cuts[L]:cuts[L + 1]]
    if not len(idx): continue
    p = parent[idx]
    att[idx] = np.where(new[idx] & ~new[p], idx, att[p])
m = new & (att >= 0)
mass = np.bincount(att[m], weights=size[m], minlength=len(nodes))
roots = np.nonzero(mass)[0]
bnd = parent[roots]
bymass = {}
for r, b in zip(roots, bnd):
    k = (int(b), elabel(pedge[r]) if ET[edges[pedge[r], 0]] not in ("element", "hidden") else "[i]")
    e = bymass.setdefault(k, [0.0, 0, r]); e[0] += mass[r]; e[1] += 1
print(f"{len(roots)} attachments under {len(set(bnd.tolist()))} old nodes\n")
for (b, el), (mb, cnt, r) in sorted(bymass.items(), key=lambda kv: -kv[1][0])[:top]:
    print(f"=== {mb / 2**20:8.1f} MB new below old node {b} ({nlabel(b)}), via {cnt} x {el}  (first: {nlabel(r)})")
    p = path(b)
    print(show(p[-30:]) if len(p) > 30 else show(p))
    print()
