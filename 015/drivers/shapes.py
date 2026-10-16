#!/usr/bin/env python3
"""^ticket(120) revision: shapes in each measured picture, Dress Up 0.0.48 and Hazel #2635 at 032fe3aca6.
One headless Firefox; counts the drawing's elements by kind (SVG shapes, groups, defs, SMIL animations)."""
import sys, time, json
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
from deck_regress import Driver
from slider_timing import wait, reap
COUNT = r"""
const root = arguments[0] === 'pic' ? document.getElementById('pic') : (() => { let best = null, area = 0;
  for (const s of document.querySelectorAll('svg')) { const r = s.getBoundingClientRect(), a = r.width * r.height; if (a > area && s.querySelectorAll('*').length > 40) { best = s; area = a; } } return best; })();
if (!root) return null;
const kinds = {}; for (const e of root.querySelectorAll('*')) kinds[e.localName] = (kinds[e.localName] || 0) + 1;
const shapeNames = ['path','rect','circle','ellipse','line','polyline','polygon','text','use','image'];
const shapes = shapeNames.reduce((a, k) => a + (kinds[k] || 0), 0);
const anims = ['animate','animateTransform','animateMotion','set'].reduce((a, k) => a + (kinds[k] || 0), 0);
return { shapes, anims, groups: kinds.g || 0, all: root.querySelectorAll('*').length, kinds };
"""
out = {}
d = Driver(8133, 4828)
page = lambda code: d.js("const s = document.createElement('script'); s.textContent = arguments[0]; document.head.append(s); s.remove();", [code])
try:
    d._req("POST", f"/session/{d.sid}/url", {"url": "http://localhost:8133/du-048.html"}); time.sleep(3.5)
    for name, setup in [("dress_none", "state.background.kind = 'none';"), ("dress_forest", "state.background.kind = 'forest';"), ("dress_witch", "state.background.kind = 'witch';")]:
        page("state = clone(DEFAULTS); state.music.mute = true; " + setup + " changed();"); time.sleep(1.2)
        out[name] = d.js(COUNT, ["pic"]); print(name, json.dumps({k: out[name][k] for k in ("shapes", "anims", "groups", "all")}), flush=True)
    for name, slide in [("hazel_kids", "livelit-playground-emotion-kids-choice"), ("hazel_fullbody", "livelit-playground-full-body")]:
        d._req("POST", f"/session/{d.sid}/url", {"url": f"http://localhost:8341/fresh?slide={slide}&panel=none"})
        wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && document.querySelectorAll('svg').length > 3;", limit=300); time.sleep(8)
        out[name] = d.js(COUNT, ["largest"]); print(name, json.dumps({k: out[name][k] for k in ("shapes", "anims", "groups", "all")}), flush=True)
finally:
    json.dump(out, open("/home/matthew/.cache/hazel-diag/r120/shapes.json", "w"), indent=1)
    d.quit(); reap(d)
