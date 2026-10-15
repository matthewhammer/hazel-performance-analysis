"""^ticket(58): write dom.c's inputs for snapshot B (new = ids A lacks).
  python3 dom_export.py <A.heapsnapshot> <B.heapsnapshot> <outdir>"""
import json, sys, numpy as np
fa, fb, out = sys.argv[1:4]
z = np.load(fb + ".npz"); meta = json.load(open(fb + ".json"))["meta"]
nodes, edges, first = z["nodes"], z["edges"], z["first"]
NF = len(meta["node_fields"]); ID = meta["node_fields"].index("id"); SZ = meta["node_fields"].index("self_size")
WEAK = meta["edge_types"][0].index("weak")
first.astype(np.int64).tofile(f"{out}/first.bin")
(edges[:, 2] // NF).astype(np.int32).tofile(f"{out}/to.bin")
(edges[:, 0] != WEAK).astype(np.uint8).tofile(f"{out}/keep.bin")
nodes[:, SZ].astype(np.float64).tofile(f"{out}/self.bin")
(~np.isin(nodes[:, ID], np.load(fa + ".npz")["nodes"][:, ID])).astype(np.uint8).tofile(f"{out}/new.bin")
print(len(nodes), len(edges))
