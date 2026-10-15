"""^ticket(58): from an old node, follow the heaviest branch of new bytes
down B's BFS tree, printing each step with its top children.
  python3 snap_heavy.py <A.heapsnapshot> <B.heapsnapshot> <node> [<steps>]"""
import sys
import numpy as np
fa, fb, start = sys.argv[1], sys.argv[2], int(sys.argv[3]); steps = int(sys.argv[4]) if len(sys.argv) > 4 else 80
sys.argv = [sys.argv[0], fb, "\x00none"]
exec(open(__file__.replace("snap_heavy.py", "snap_paths.py")).read().split("sidx = ")[0])
ID = meta["node_fields"].index("id")
new = ~np.isin(nodes[:, ID], np.load(fa + ".npz")["nodes"][:, ID])
size = nodes[:, SIZE].astype(np.float64)
sub = np.where(new, size, 0.0)
order = np.argsort(dist, kind="stable"); order = order[dist[order] >= 1]
cuts = np.searchsorted(dist[order], np.arange(dist.max() + 2))
for L in range(dist.max(), 0, -1):
    idx = order[cuts[L]:cuts[L + 1]]
    if len(idx): np.add.at(sub, parent[idx], sub[idx])
# children in the BFS tree: sort by parent
kids_order = np.argsort(parent, kind="stable"); kp = parent[kids_order]
def kids(i):
    a, b = np.searchsorted(kp, i), np.searchsorted(kp, i, side="right")
    k = kids_order[a:b]; return k[k != i]
i = start
for s in range(steps):
    k = kids(i)
    if not len(k) or sub[i] < 2**20: break
    k = k[np.argsort(-sub[k])]
    alts = "; ".join(f"{elabel(pedge[c])} {sub[c] / 2**20:.1f}" for c in k[:4])
    print(f"{sub[i] / 2**20:8.1f} MB {'new' if new[i] else 'old'} {nlabel(i)}  | {len(k)} kids: {alts}")
    i = k[0]
np.save(fb + ".sub.npy", sub)
