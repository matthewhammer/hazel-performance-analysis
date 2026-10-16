#!/usr/bin/env python3
"""^ticket(120): drag_stall.py's drag on any slider, in Hazel or in Dress Up.

Headless Firefox (deck_regress.Driver, a fresh profile per run of this
script). Each run is one long real drag of the slider named --label
(WebDriver pointer actions: down, 15 moves of 100 ms each, up) to a value
not drawn before, given as a share of the slider's range. A
requestAnimationFrame loop records every frame from just before the pointer
goes down until the largest picture differs from before the drag, polled
every 50 ms after the release (the poll's resolution bounds
release-to-redraw from above). Per run: frames, the longest gap between
frames, the time spent in gaps over 50 ms (stalled), the window, release
to redraw, and the slider's input events.

  stall_any.py --game hazel --port 8341 --slide livelit-playground-emotion-kids-choice --label "eye size"
  stall_any.py --game dress --port 8133 --tab Eyes --label "eye size" --place none
"""
import argparse, json, statistics, sys, time
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
sys.path.insert(0, "/home/matthew/.cache/hazel-diag")
from deck_regress import Driver
from slider_timing import wait, reap
import fullbody_release as F
from drag_stall import REC

SHARES = [0.25, 0.4, 0.55, 0.7, 0.85, 0.3, 0.6, 0.9, 0.45, 0.75]

def run_once(d, label, share):
    g = d.js("return __geom(arguments[0]);", [label])
    v = g["min"] + (g["max"] - g["min"]) * share
    x0, x1, y = round(F.xfor(g, g["v"])), round(F.xfor(g, v)), round(g["y"])
    d.js(REC.replace("'arm length'", json.dumps(label)))
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
    return {"share": share, "target": round(v, 1), "frames": len(fr), "window_ms": round((end or 0) - (S["down"] or 0)),
            "longest_gap_ms": round(max(gaps)) if gaps else None,
            "stalled_ms": round(sum(x for x in gaps if x > 50)),
            "release_to_redraw_ms": round(S["done"] - S["up"]) if S["done"] and S["up"] else None,
            "inputs": d.js("return window.__inCount - window.__stall.in0;"),
            "frame_ms": [round(t - (S["down"] or 0), 1) for t in fr], "up_ms": round(S["up"] - S["down"], 1) if S["up"] and S["down"] else None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", choices=["hazel", "dress"], required=True)
    ap.add_argument("--port", type=int, required=True); ap.add_argument("--wd-port", type=int, default=4814)
    ap.add_argument("--slide"); ap.add_argument("--tab"); ap.add_argument("--place", default="none")
    ap.add_argument("--label", required=True); ap.add_argument("--runs", type=int, default=8)
    ap.add_argument("--out")
    a = ap.parse_args()
    d = Driver(a.port, a.wd_port); out = {"game": a.game, "slide": a.slide, "place": a.place, "label": a.label, "port": a.port, "runs": []}
    try:
        if a.game == "hazel":
            d.goto(f"/fresh?slide={a.slide}&panel=none")
            if wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && document.querySelectorAll('svg').length > 3;", limit=300) is None:
                print("did not load"); return
            time.sleep(8)
        else:
            d.goto("/dress-up.html")
            if wait(d, "return !!document.getElementById('pic') && typeof changed === 'function';", limit=120) is None:
                print("did not load"); return
            # (the game's state is a top-level let, unseen by WebDriver's
            # scripts: the set-up runs as a script of the page's own)
            d.js("const s = document.createElement('script'); s.textContent = arguments[0]; document.head.append(s); s.remove();",
                 ["state = clone(DEFAULTS); state.music.mute = true; state.background.kind = " + json.dumps(a.place) + "; changed();"])
            d.js("[...document.querySelectorAll('button')].find(b => b.textContent.includes(arguments[0])).click();", [a.tab])
            time.sleep(2)
        out["ua"] = d.js("return navigator.userAgent;")
        d.js(F.HELPERS)
        for i, share in enumerate([0.1, 0.15] + SHARES[:a.runs]):
            time.sleep(3 if a.game == "hazel" else 1.5)
            r = run_once(d, a.label, share); r["warmup"] = i < 2
            out["runs"].append(r); print(json.dumps(r), flush=True)
        rs = [r for r in out["runs"] if not r["warmup"]]
        for k in ("longest_gap_ms", "stalled_ms", "window_ms", "release_to_redraw_ms", "inputs", "frames"):
            xs = [r[k] for r in rs if r[k] is not None]
            out[k] = {"median": statistics.median(xs), "min": min(xs), "max": max(xs)} if xs else None
        print(a.game, a.label, {k: out[k] for k in ("longest_gap_ms", "stalled_ms", "release_to_redraw_ms", "inputs")}, flush=True)
    finally:
        if a.out: json.dump(out, open(a.out, "w"), indent=1)
        d.quit(); reap(d)

if __name__ == "__main__":
    main()
