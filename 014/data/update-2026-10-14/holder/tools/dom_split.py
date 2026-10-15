"""^ticket(58): where do the paths to two nodes part? Both BFS paths from
the root, step by step, with the edge each takes, and the dominator chains.
  python3 dom_split.py <B.heapsnapshot> <domdir> <node> <node> [...]"""
import sys, numpy as np
fb, dd, vs = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
sys.argv = [sys.argv[0], fb, "\x00none"]
exec(open(__file__.replace("dom_split.py", "snap_paths.py")).read().split("sidx = ")[0])
idom = np.fromfile(f"{dd}/idom.bin", np.int32); rn = np.fromfile(f"{dd}/retnew.bin"); ret = np.fromfile(f"{dd}/ret.bin")
ps = [path(v) for v in vs]
k = 0
while all(len(p) > k for p in ps) and len({p[k][1] for p in ps}) == 1: k += 1
print(f"BFS paths share {k} steps; the shared tail:")
print(show(ps[0][max(0, k - 12):k]))
for v, p in zip(vs, ps):
    print(f"\n-- then to {v} ({len(p) - k} more steps):")
    for e, i in p[k:]:
        print(f"   --{elabel(e)}--> {nlabel(i)} [{i}] retains {ret[i] / 2**20:.1f} MB (new {rn[i] / 2**20:.1f})")
def dchain(v):
    c = [v]
    while c[-1] != 0: c.append(int(idom[c[-1]]))
    return c[::-1]
cs = [dchain(v) for v in vs]
k = 0
while all(len(c) > k for c in cs) and len({c[k] for c in cs}) == 1: k += 1
lcd = cs[0][k - 1]
print(f"\nlowest common dominator: {lcd} {nlabel(lcd)} retains {ret[lcd] / 2**20:.1f} MB (new {rn[lcd] / 2**20:.1f}), dist {dist[lcd]}")
