#!/usr/bin/env python3
"""^ticket(120): drag_stall.py's drag, on Messed Up Dress Up (the plain-JS game).

The same measurement as drag_stall.py, so the two can stand side by side:
headless Firefox (deck_regress.Driver, a fresh profile), the "arm length"
slider in the game's "Neck, arms & legs" tab, each run one long real drag
(WebDriver pointer actions: down, 15 moves of 100 ms each, up) to a length
not drawn before; a requestAnimationFrame loop records every frame from just
before the pointer goes down until the picture differs from before the drag,
polled every 50 ms after the release (the poll's resolution bounds
release-to-redraw from above). Music muted before the first press.

  dressup_stall.py --port 8133 --place none --runs 8 --out dress_none.json
  dressup_stall.py --port 8133 --place forest --runs 8 --out dress_forest.json
"""
import argparse, json, statistics, sys, time
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
sys.path.insert(0, "/home/matthew/.cache/hazel-diag")
from deck_regress import Driver
from slider_timing import wait, reap
import fullbody_release as F
from drag_stall import run_once

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8133); ap.add_argument("--wd-port", type=int, default=4813)
    ap.add_argument("--place", default="none"); ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = Driver(a.port, a.wd_port); out = {"game": "dress-up", "place": a.place, "port": a.port, "runs": []}
    try:
        d.goto("/dress-up.html")
        if wait(d, "return !!document.getElementById('pic') && typeof changed === 'function';", limit=120) is None:
            print("did not load"); return
        out["ua"] = d.js("return navigator.userAgent;")
        # (the game's state is a top-level let, which WebDriver's scripts can't
        # see: run the set-up as a script of the page's own)
        page = lambda code: d.js("const s = document.createElement('script'); s.textContent = arguments[0]; document.head.append(s); s.remove();", [code])
        page("state = clone(DEFAULTS); state.music.mute = true; state.background.kind = " + json.dumps(a.place) + "; changed();"
             "window.__armLen = () => state.body.armLen;")
        d.js("[...document.querySelectorAll('button')].find(b => b.textContent.includes('Neck, arms')).click();")
        time.sleep(2); d.js(F.HELPERS)
        for i, v in enumerate([110, 130] + [150, 200, 250, 300, 350, 400, 425, 175][:a.runs]):
            time.sleep(1.5)
            r = run_once(d, v); r["warmup"] = i < 2
            r["value_after"] = d.js("return window.__armLen();")
            out["runs"].append(r); print(json.dumps(r), flush=True)
        rs = [r for r in out["runs"] if not r["warmup"]]
        for k in ("longest_gap_ms", "stalled_ms", "window_ms", "release_to_redraw_ms", "inputs", "frames"):
            xs = [r[k] for r in rs if r[k] is not None]
            out[k] = {"median": statistics.median(xs), "min": min(xs), "max": max(xs)} if xs else None
        print(a.place, {k: out[k] for k in ("longest_gap_ms", "stalled_ms", "window_ms", "release_to_redraw_ms", "inputs", "frames")}, flush=True)
    finally:
        if a.out: json.dump(out, open(a.out, "w"), indent=1)
        d.quit(); reap(d)

if __name__ == "__main__":
    main()
