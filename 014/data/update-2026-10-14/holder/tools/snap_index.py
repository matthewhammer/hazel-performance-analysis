"""^ticket(58): parse a V8 .heapsnapshot into numpy arrays once (nodes,
edges, first-edge offsets, strings, closure locations) and a BFS from the
root over non-weak edges (parent node and edge per node), saved as .npz +
.json beside the snapshot for snap_paths.py.
  python3 snap_index.py <file.heapsnapshot>"""
import json, sys, time
import numpy as np
f = sys.argv[1]; t0 = time.time()
raw = open(f, "rb").read()
def section(name, nxt):
    a = raw.index(b'"' + name + b'":[') + len(name) + 4
    b = raw.index(b'"' + nxt + b'":', a)
    b = raw.rindex(b']', a, b)
    return a, b
head = json.loads(raw[raw.index(b'{"snapshot":') + 12: raw.index(b'\n"nodes":')].rstrip(b',\n'))
meta = head["meta"]
a, b = section(b"nodes", b"edges"); nodes = np.array(raw[a:b].split(b","), dtype=np.int64) if False else np.fromstring(raw[a:b].decode(), dtype=np.int64, sep=",")
print("nodes parsed", time.time() - t0, flush=True)
a, b = section(b"edges", b"trace_function_infos"); edges = np.fromstring(raw[a:b].decode(), dtype=np.int64, sep=",")
print("edges parsed", time.time() - t0, flush=True)
a, b = section(b"locations", b"strings"); locs = np.fromstring(raw[a:b].decode() or "0", dtype=np.int64, sep=",") if b > a else np.zeros(0, np.int64)
a = raw.index(b'"strings":[') + 10; strings = json.loads(raw[a: raw.rindex(b"]") + 1])
print("strings", len(strings), time.time() - t0, flush=True)
del raw
NF, EF = len(meta["node_fields"]), len(meta["edge_fields"])
nodes = nodes.reshape(-1, NF); edges = edges.reshape(-1, EF)
N = len(nodes); ec = nodes[:, meta["node_fields"].index("edge_count")]
first = np.zeros(N + 1, np.int64); np.cumsum(ec, out=first[1:])
to = edges[:, 2] // NF
WEAK = meta["edge_types"][0].index("weak")
etype = edges[:, 0]
# BFS, level by level
parent = np.full(N, -1, np.int64); pedge = np.full(N, -1, np.int64); dist = np.full(N, -1, np.int32)
parent[0] = 0; dist[0] = 0; frontier = np.array([0]); d = 0
while len(frontier):
    starts, counts = first[frontier], ec[frontier]
    tot = int(counts.sum())
    if not tot: break
    src = np.repeat(frontier, counts)
    off = np.arange(tot) - np.repeat(np.cumsum(counts) - counts, counts)
    eidx = np.repeat(starts, counts) + off
    keep = etype[eidx] != WEAK
    eidx, src = eidx[keep], src[keep]
    dst = to[eidx]
    new = dist[dst] < 0
    eidx, src, dst = eidx[new], src[new], dst[new]
    dst, i = np.unique(dst, return_index=True)
    d += 1
    parent[dst] = src[i]; pedge[dst] = eidx[i]; dist[dst] = d
    frontier = dst
print("bfs levels", d, "reached", int((dist >= 0).sum()), "of", N, time.time() - t0, flush=True)
np.savez(f + ".npz", nodes=nodes, edges=edges, first=first, parent=parent, pedge=pedge, dist=dist, locs=locs)
json.dump({"meta": meta, "strings": strings}, open(f + ".json", "w"))
print("saved", time.time() - t0)
