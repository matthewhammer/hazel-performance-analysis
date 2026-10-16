#!/usr/bin/env python3
"""^ticket(91): an interleaved A/B of a drag fix against #2635's head, drag by drag.

One headless Firefox (deck_regress.Driver), one tab per build, all loaded at
once: the head twice (as http://localhost:8341 and http://127.0.0.1:8341, two
origins with their own saved state: an A/A pair whose difference is the noise
floor) and the prototype (its own port). Then rounds: in each round every tab
makes one real drag of Full Body's "arm length" slider (drag_stall.py's drag:
down, 15 moves of 100 ms, up, to a value not drawn before in that tab), the
order of the tabs turned round from round to round, so no build always goes
first or last and the session's drift falls on all of them alike.

Per drag, as drag_stall.py: frames, longest gap, frozen time (gaps over 50 ms),
release to redraw, the slider's inputs, and (the coalescing build's counters)
repaints sent and coalesced. Per build: medians and ranges; per pair of builds,
the paired differences round by round (median, and how many rounds each way).

  ab_drag.py --proto http://localhost:8351 --label coalesce --setup C --rounds 10 --out ab_coal_C.json
"""
import argparse, json, statistics, sys, time
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
sys.path.insert(0, "/home/matthew/.cache/hazel-diag")
from deck_regress import Driver
from slider_timing import wait, reap
import fullbody_release as F
from drag_stall import REC

SLIDE = "livelit-playground-full-body"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proto", required=True); ap.add_argument("--label", required=True)
    ap.add_argument("--setup", choices=["B", "C"], default="C"); ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--wd-port", type=int, default=4831); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tabs = [("head", "http://localhost:8341"), ("head-again", "http://127.0.0.1:8341"), (a.label, a.proto)]
    d = Driver(8341, a.wd_port)
    out = {"setup": a.setup, "rounds": a.rounds, "builds": {n: u for n, u in tabs}, "drags": []}
    req = d._req
    def switch(h): req("POST", f"/session/{d.sid}/window", {"handle": h})
    try:
        handles = {}
        first = req("GET", f"/session/{d.sid}/window")["value"]
        for i, (name, url) in enumerate(tabs):
            h = first if i == 0 else req("POST", f"/session/{d.sid}/window/new", {"type": "tab"})["value"]["handle"]
            handles[name] = h; switch(h)
            req("POST", f"/session/{d.sid}/url", {"url": f"{url}/fresh?slide={SLIDE}&panel=none"})
            if wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && document.querySelectorAll('svg').length > 3;", limit=300) is None:
                raise SystemExit(f"{name} did not load")
            time.sleep(8); d.js(F.HELPERS)
            if a.setup == "B":
                out.setdefault("ux", {})[name] = F.ux_mode(d); d.js(F.HELPERS)
            st = d.js("return fetch('/status.json').then(r => r.json()).catch(() => null);")
            out.setdefault("status", {})[name] = st
            print("loaded", name, url, (st or {}).get("head", "?")[:40], flush=True)
        # (each tab's own sequence of targets, the same in every tab: a long
        # drag each time, down and up in turn, each value new to the tab)
        targets = [400 - 3 * k if k % 2 == 0 else 150 + 3 * k for k in range(a.rounds + 2)]
        names = [n for n, _ in tabs]
        for r in range(-1, a.rounds):          # (round -1: a warm-up drag in each tab)
            order = names[(r % 3):] + names[:(r % 3)] if r >= 0 else names
            if r % 2 == 1: order = order[::-1]
            for name in order:
                switch(handles[name]); time.sleep(2.5)
                vis = d.js("return document.visibilityState;")
                v = targets[r + 1]
                g = d.js("return __geom(arguments[0]);", [F.LABEL])
                x0, x1, y = round(F.xfor(g, g["v"])), round(F.xfor(g, v)), round(g["y"])
                d.js(REC); time.sleep(0.3)
                d.pointer([{"type": "pointerMove", "duration": 0, "x": x0, "y": y, "origin": "viewport"}, {"type": "pointerDown", "button": 0}]
                          + [{"type": "pointerMove", "duration": 100, "x": round(x0 + (x1 - x0) * j / 15), "y": y, "origin": "viewport"} for j in range(1, 16)]
                          + [{"type": "pointerUp", "button": 0}])
                wait(d, "return window.__stall.on === false;", limit=90)
                S = d.js("return window.__stall;")
                fr = [t for t in S["frames"] if S["down"] is None or t >= S["down"] - 20]
                end = S["done"] or S["up"]; fr = [t for t in fr if end is None or t <= end + 50]
                gaps = [b - c for c, b in zip(fr, fr[1:])]
                rec = {"round": r, "build": name, "target": v, "visible": vis, "frames": len(fr),
                       "longest_gap_ms": round(max(gaps)) if gaps else None, "stalled_ms": round(sum(x for x in gaps if x > 50)),
                       "window_ms": round((end or 0) - (S["down"] or 0)),
                       "release_to_redraw_ms": round(S["done"] - S["up"]) if S["done"] and S["up"] else None,
                       "inputs": d.js("return window.__inCount - window.__stall.in0;"),
                       "repaints_sent": d.js("return (window.__ll_repaints || 0) - window.__stall.rp0;"),
                       "repaints_coalesced": d.js("return (window.__ll_coalesced || 0) - window.__stall.co0;")}
                out["drags"].append(rec); print(json.dumps(rec), flush=True)
        # summary
        meas = [x for x in out["drags"] if x["round"] >= 0]
        out["summary"] = {}
        for name in names:
            xs = [x for x in meas if x["build"] == name]
            out["summary"][name] = {k: {"median": statistics.median([x[k] for x in xs if x[k] is not None]),
                                        "min": min(x[k] for x in xs if x[k] is not None), "max": max(x[k] for x in xs if x[k] is not None)}
                                    for k in ("stalled_ms", "longest_gap_ms", "release_to_redraw_ms", "inputs")}
        out["paired"] = {}
        for other in names[1:]:
            for k in ("stalled_ms", "release_to_redraw_ms"):
                diffs = []
                for r in range(a.rounds):
                    h = [x for x in meas if x["round"] == r and x["build"] == "head"]; o = [x for x in meas if x["round"] == r and x["build"] == other]
                    if h and o and h[0][k] is not None and o[0][k] is not None: diffs.append(o[0][k] - h[0][k])
                if diffs:
                    out["paired"][f"{other} - head: {k}"] = {"median": statistics.median(diffs), "rounds": len(diffs),
                                                              "lower": sum(1 for x in diffs if x < 0), "higher": sum(1 for x in diffs if x > 0), "diffs": diffs}
        print(json.dumps(out["summary"]), flush=True); print(json.dumps({k: {kk: v[kk] for kk in ("median", "lower", "higher", "rounds")} for k, v in out["paired"].items()}), flush=True)
    finally:
        json.dump(out, open(a.out, "w"), indent=1)
        d.quit(); reap(d)

if __name__ == "__main__":
    main()
