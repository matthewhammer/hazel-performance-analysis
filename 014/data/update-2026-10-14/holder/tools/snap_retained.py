"""^ticket(58): what a node holds exclusively: the bytes no longer reachable
from the root (over non-weak edges) when that node is cut out, split into
new (B's ids that A lacks) and old.
  python3 snap_retained.py <A.heapsnapshot> <B.heapsnapshot> <node> [<node> ...]"""
import sys
import numpy as np
fa, fb, cuts_ = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
sys.argv = [sys.argv[0], fb, "\x00none"]
exec(open(__file__.replace("snap_retained.py", "snap_paths.py")).read().split("sidx = ")[0])
ID = meta["node_fields"].index("id")
new = ~np.isin(nodes[:, ID], np.load(fa + ".npz")["nodes"][:, ID])
size = nodes[:, SIZE].astype(np.float64)
ec = np.diff(first); to = edges[:, 2] // NF
WEAK = ET.index("weak"); notweak = edges[:, 0] != WEAK
def reach(cut):
    seen = np.zeros(len(nodes), bool); seen[0] = True
    if cut is not None: seen[cut] = True   # never entered
    frontier = np.array([0])
    while len(frontier):
        counts = ec[frontier]; tot = int(counts.sum())
        if not tot: break
        eidx = np.repeat(first[frontier], counts) + (np.arange(tot) - np.repeat(np.cumsum(counts) - counts, counts))
        dst = to[eidx[notweak[eidx]]]
        dst = np.unique(dst[~seen[dst]])
        seen[dst] = True; frontier = dst
    if cut is not None: seen[cut] = False
    return seen
full = reach(None)
print(f"reachable: {full.sum()} nodes; new {size[full & new].sum() / 2**20:.1f} MB, old {size[full & ~new].sum() / 2**20:.1f} MB")
for c in cuts_:
    r = reach(c)
    lost = full & ~r
    print(f"cut {c} ({nlabel(c)}): holds alone {lost.sum()} nodes, new {size[lost & new].sum() / 2**20:.1f} MB, old {size[lost & ~new].sum() / 2**20:.1f} MB", flush=True)
