"""^ticket(86): undo and redo times, as built against the compaction port,
from undo_check.mjs logs (undo5/<build>_<i>.log)."""
import glob, json, re, statistics, sys
d = sys.argv[1] if len(sys.argv) > 1 else "undo5"
out = {}
for b in ("asbuilt", "port"):
    steps = {"edit": [], "undo": [], "redo": [], "edit2": [], "undo2": []}; ok = []; errs = []
    for f in sorted(glob.glob(f"{d}/{b}_*.log")):
        L = open(f).read().strip().splitlines()
        try: last = json.loads(L[-1])
        except Exception: print("bad", f, L[-1:]); continue
        for l in L:
            m = re.match(r"(\w+)\s+redraw ([\d.]+|null)", l)
            if m and m.group(1) in steps: steps[m.group(1)].append(None if m.group(2) == "null" else float(m.group(2)))
        ok.append(all(last[k] for k in ("undo_restores_start", "redo_restores_edit", "undo2_restores_redo"))); errs.append(len(last["errors"]))
    ur = [x for k in ("undo", "redo", "undo2") for x in steps[k] if x is not None]
    ed = [x for k in ("edit", "edit2") for x in steps[k] if x is not None]
    out[b] = dict(runs=len(ok), all_restore=all(ok), steps=steps, undo_redo_median=statistics.median(ur), undo_redo=sorted(ur),
                  edit_median=statistics.median(ed), edits=sorted(ed), console_errors=errs,
                  undo_redo_over_4s=sum(x > 4 for x in ur), edits_over_4s=sum(x > 4 for x in ed))
    print(b, {k: v for k, v in out[b].items() if k != "steps"})
json.dump(out, open(f"{d}/summary.json", "w"), indent=1)
