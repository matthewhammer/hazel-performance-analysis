"""^ticket(58): the lowest dominators of the new bytes: nodes retaining at
least <min MB> of new bytes where no one dominator-child keeps 60% of it;
for each, its dominator chain from the root and its BFS path.
  python3 dom_report.py <B.heapsnapshot> <domdir> [<min MB>]"""
import sys, numpy as np
fb, dd = sys.argv[1], sys.argv[2]; minmb = float(sys.argv[3]) if len(sys.argv) > 3 else 8
sys.argv = [sys.argv[0], fb, "\x00none"]
exec(open(__file__.replace("dom_report.py", "snap_paths.py")).read().split("sidx = ")[0])
idom = np.fromfile(f"{dd}/idom.bin", np.int32); ret = np.fromfile(f"{dd}/ret.bin"); rn = np.fromfile(f"{dd}/retnew.bin")
N = len(idom); ok = idom >= 0; ok[0] = False
maxkid = np.zeros(N); np.maximum.at(maxkid, idom[ok], rn[ok])
cand = np.nonzero((rn >= minmb * 2**20) & (maxkid < 0.6 * rn))[0]
cand = cand[np.argsort(-rn[cand])]
def domchain(v):
    c = [v]
    while c[-1] != 0: c.append(int(idom[c[-1]]))
    return c[::-1]
for v in cand[:12]:
    print(f"=== node {v} {nlabel(v)}: retains {ret[v] / 2**20:.1f} MB, new {rn[v] / 2**20:.1f} MB; biggest dominated child {maxkid[v] / 2**20:.1f} MB")
    ch = domchain(v)
    print("  dominators:", " > ".join(f"{nlabel(x)}({rn[x] / 2**20:.0f})" for x in ch[-12:]))
    p = path(v); print(show(p[-24:]) if len(p) > 24 else show(p))
    kids = np.nonzero(idom == v)[0]; kids = kids[np.argsort(-rn[kids])][:6]
    print("  top dominated:", "; ".join(f"{nlabel(k)} {rn[k] / 2**20:.1f}" for k in kids))
    print()
