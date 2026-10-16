#!/usr/bin/env python3
"""^ticket(90): how long does the page stall during a real drag?

Headless Firefox (deck_regress.Driver), Full Body, the "arm length" slider:
each run is one long real drag (WebDriver pointer actions: down, 15 moves
of 100 ms each, up), to a length not drawn before. A requestAnimationFrame
loop in the page records every frame from just before the pointer goes
down until the picture has redrawn after the release (or 60 s). A frame
gap is the time between two frames; a page that keeps up draws every
~17 ms. Reports, per run: the longest gap, the time spent in gaps over
50 ms (stalled), the window's length, and release to redraw.

  drag_stall.py --port 8341 --setup C --runs 6 --out c.json
  drag_stall.py --port 8341 --setup B ...   # UX mode, as fullbody_release.py
"""
import argparse, json, statistics, sys, time
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
sys.path.insert(0, "/home/matthew/.cache/hazel-diag")
from deck_regress import Driver
from slider_timing import wait, reap
import fullbody_release as F

REC = r"""
if (window.__inCount === undefined) { window.__inCount = 0; const inp = __slider('arm length'); if (inp) inp.addEventListener('input', () => { window.__inCount++; }, { capture: true }); }
window.__stall = { frames: [], on: true, up: null, done: null, down: null, in0: window.__inCount, rp0: window.__ll_repaints || 0, co0: window.__ll_coalesced || 0 };
document.addEventListener('pointerdown', () => { window.__stall.down = performance.now(); }, { capture: true, once: true });
document.addEventListener('pointerup', () => {
  const S = window.__stall; S.up = performance.now();
  const poll = setInterval(() => { const q = __pic();
    if (q && q.outerHTML !== window.__before) { S.done = performance.now(); clearInterval(poll); setTimeout(() => { S.on = false; }, 300); }
    else if (performance.now() - S.up > 60000) { clearInterval(poll); S.on = false; } }, 50);
}, { capture: true, once: true });
window.__before = (__pic() || {}).outerHTML || '';
(function tick(t) { const S = window.__stall; S.frames.push(t); if (S.on) requestAnimationFrame(tick); })(performance.now());
"""

def run_once(d, v):
    g = d.js("return __geom(arguments[0]);", [F.LABEL])
    x0, x1, y = round(F.xfor(g, g["v"])), round(F.xfor(g, v)), round(g["y"])
    d.js(REC)
    time.sleep(0.3)
    d.pointer([{"type": "pointerMove", "duration": 0, "x": x0, "y": y, "origin": "viewport"}, {"type": "pointerDown", "button": 0}]
              + [{"type": "pointerMove", "duration": 100, "x": round(x0 + (x1 - x0) * j / 15), "y": y, "origin": "viewport"} for j in range(1, 16)]
              + [{"type": "pointerUp", "button": 0}])
    wait(d, "return window.__stall.on === false;", limit=90)
    S = d.js("return window.__stall;")
    fr = [t for t in S["frames"] if S["down"] is None or t >= S["down"] - 20]
    end = S["done"] or S["up"]
    fr = [t for t in fr if end is None or t <= end + 50]
    gaps = [b - a for a, b in zip(fr, fr[1:])]
    return {"target": v, "frames": len(fr), "window_ms": round((end or 0) - (S["down"] or 0)),
            "longest_gap_ms": round(max(gaps)) if gaps else None,
            "stalled_ms": round(sum(g for g in gaps if g > 50)),
            "release_to_redraw_ms": round(S["done"] - S["up"]) if S["done"] and S["up"] else None,
            "inputs": d.js("return window.__inCount - window.__stall.in0;"),
            "repaints_sent": d.js("return (window.__ll_repaints || 0) - window.__stall.rp0;"),
            "repaints_coalesced": d.js("return (window.__ll_coalesced || 0) - window.__stall.co0;")}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8341); ap.add_argument("--wd-port", type=int, default=4812)
    ap.add_argument("--setup", choices=["B", "C"], required=True); ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = Driver(a.port, a.wd_port); out = {"setup": a.setup, "port": a.port, "runs": []}
    try:
        d.goto(f"/fresh?slide={F.SLIDE}&panel=none")
        if wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && document.querySelectorAll('svg').length > 3;", limit=300) is None:
            print("did not load"); return
        time.sleep(8); d.js(F.HELPERS)
        if a.setup == "B":
            out["ux"] = F.ux_mode(d); print("UX mode:", json.dumps(out["ux"]), flush=True); d.js(F.HELPERS)
        for i, v in enumerate([110, 130] + [150, 200, 250, 300, 350, 400, 425, 175][:a.runs]):
            time.sleep(3)
            r = run_once(d, v); r["warmup"] = i < 2
            out["runs"].append(r); print(json.dumps(r), flush=True)
        rs = [r for r in out["runs"] if not r["warmup"]]
        for k in ("longest_gap_ms", "stalled_ms", "window_ms", "release_to_redraw_ms", "inputs", "repaints_sent", "repaints_coalesced"):
            xs = [r[k] for r in rs if r[k] is not None]
            out[k] = {"median": statistics.median(xs), "min": min(xs), "max": max(xs)} if xs else None
        print(a.setup, {k: out[k] for k in ("longest_gap_ms", "stalled_ms", "window_ms", "release_to_redraw_ms", "inputs", "repaints_sent", "repaints_coalesced")}, flush=True)
    finally:
        if a.out: json.dump(out, open(a.out, "w"), indent=1)
        d.quit(); reap(d)

if __name__ == "__main__":
    main()
