#!/usr/bin/env python3
"""^ticket(29): ^report(8)'s measurement again, on #2635's current head.

The Full Body slide, the "arm length" slider: two warm-up changes, then
twelve, each a real pointer drag (WebDriver actions) to a length not drawn
before, the same lengths in every set-up. Release to redraw: from the
slider's pointerup to the first poll (every 200 ms, in the page, as in
^report(8)) at which the largest picture's markup differs from before the
drag. Headless Firefox, a fresh profile per set-up (deck_regress.Driver).

  fullbody_release.py --port 8341 --setup C   # the whole program (dev mode)
  fullbody_release.py --port 8341 --setup B   # UX mode, only arm_length and drawn
"""
import argparse, json, statistics, sys, time
sys.path.insert(0, "/home/matthew/hazel-livelits-modular/scripts")
from deck_regress import Driver
from slider_timing import wait, reap

SLIDE = "livelit-playground-full-body"
LABEL = "arm length"
WARMUP = [110, 130]
VALUES = [150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425]

HELPERS = r"""
window.__pic = () => {
  let best = null, area = 0;
  for (const s of document.querySelectorAll('svg')) {
    const r = s.getBoundingClientRect(), a = r.width * r.height;
    if (a > area && s.querySelectorAll('*').length > 40) { best = s; area = a; }
  }
  return best;
};
window.__slider = label => {
  for (const inp of document.querySelectorAll('input[type=range]')) {
    const box = inp.parentElement;
    if (box && box.textContent.trim().startsWith(label)) return inp;
  }
  for (const inp of document.querySelectorAll('input[type=range]')) {
    const box = inp.closest('div');
    if (box && box.textContent.includes(label)) return inp;
  }
  return null;
};
window.__arm = () => {
  const p = __pic();
  window.__before = p ? p.outerHTML : '';
  window.__up = null; window.__done = null; window.__polls = 0;
  document.addEventListener('pointerup', () => {
    window.__up = performance.now();
    const poll = setInterval(() => {
      window.__polls++;
      const q = __pic();
      if (q && q.outerHTML !== window.__before) { window.__done = performance.now(); clearInterval(poll); }
      else if (performance.now() - window.__up > 60000) { clearInterval(poll); }
    }, 200);
  }, { capture: true, once: true });
};
window.__geom = label => {
  const s = __slider(label);
  if (!s) return null;
  s.scrollIntoView({ block: 'center' });
  const r = s.getBoundingClientRect();
  return { x: r.x, y: r.y + r.height / 2, w: r.width, min: +s.min, max: +s.max, v: +s.value };
};
"""

def xfor(g, v, pad=8):
    return g["x"] + pad + (v - g["min"]) / (g["max"] - g["min"]) * (g["w"] - 2 * pad)

def drag_to(d, v):
    g = d.js("return __geom(arguments[0]);", [LABEL])
    if not g:
        raise SystemExit("no slider")
    x0, x1, y = round(xfor(g, g["v"])), round(xfor(g, v)), round(g["y"])
    d.js("__arm();")
    d.pointer([{"type": "pointerMove", "duration": 0, "x": x0, "y": y, "origin": "viewport"},
               {"type": "pointerDown", "button": 0}]
              + [{"type": "pointerMove", "duration": 40, "x": round(x0 + (x1 - x0) * j / 5), "y": y, "origin": "viewport"} for j in range(1, 6)]
              + [{"type": "pointerUp", "button": 0}])
    ok = wait(d, "return window.__done !== null || (window.__up !== null && performance.now() - window.__up > 60000);", limit=90)
    r = d.js("return [window.__up, window.__done, window.__polls, __slider(arguments[0]).value];", [LABEL])
    up, done, polls, val = r
    return (done - up) / 1000 if (up is not None and done is not None) else None, val, polls

def ux_mode(d):
    """UX mode, then every GUI row's chip off but arm_length's and drawn's."""
    box = d.js("const e = document.querySelectorAll('.outline-mode-btn')[1]; e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2];")
    d.pointer([{"type": "pointerMove", "duration": 0, "x": int(box[0]), "y": int(box[1]), "origin": "viewport"},
               {"type": "pointerDown", "button": 0}, {"type": "pointerUp", "button": 0}])
    time.sleep(6)
    # (setup, not measured: the chips are toggled by element clicks, one at a
    # time, the outline settling between, until exactly the two are on)
    for _ in range(200):
        left = d.js("""const keep = ['arm_length', 'drawn'], name = c => (c.parentElement.innerText || '').replace(/[^A-Za-z0-9_]/g, '');
          const chips = [...document.querySelectorAll('.outline-ux-chip')];
          // (the picture's row reads probe(drawn) while shown, drawn while hidden)
          const kept = c => keep.includes(name(c)) || name(c) === 'probedrawn';
          const wrong = chips.filter(c => c.classList.contains('outline-ux-on') !== kept(c));
          if (!wrong.length) return 0; wrong[0].click(); return wrong.length;""")
        if not left:
            break
        time.sleep(0.8)
    time.sleep(6)
    return d.js("""return { on: [...document.querySelectorAll('.outline-ux-chip.outline-ux-on')].map(c => (c.parentElement.innerText || '').replace(/[^A-Za-z0-9_]/g, '')),
                            chips: document.querySelectorAll('.outline-ux-chip').length,
                            sliders: [...document.querySelectorAll('input[type=range]')].filter(i => i.getClientRects().length).length,
                            pictures: [...document.querySelectorAll('svg')].filter(s => s.getClientRects().length && s.querySelectorAll('*').length > 40).length };""")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8341)
    ap.add_argument("--wd-port", type=int, default=4811)
    ap.add_argument("--setup", choices=["B", "C"], required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    d = Driver(args.port, args.wd_port)
    out = {"setup": args.setup, "port": args.port, "runs": []}
    try:
        d.goto(f"/fresh?slide={SLIDE}&panel=none")
        t = wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && document.querySelectorAll('svg').length > 3;", limit=300)
        if t is None:
            print("did not load"); return
        time.sleep(8)
        d.js(HELPERS)
        if args.setup == "B":
            out["ux"] = ux_mode(d)
            print("UX mode:", json.dumps(out["ux"]), flush=True)
            d.js(HELPERS)
        for i, v in enumerate(WARMUP + VALUES):
            time.sleep(3)
            secs, val, polls = drag_to(d, v)
            row = {"i": i, "warmup": i < len(WARMUP), "target": v, "value": val, "s": secs, "polls": polls}
            out["runs"].append(row)
            print(json.dumps(row), flush=True)
        ss = [r["s"] for r in out["runs"] if not r["warmup"] and r["s"] is not None]
        out["median"], out["min"], out["max"] = statistics.median(ss), min(ss), max(ss)
        print(f"{args.setup}: median {out['median']:.2f} s, range {out['min']:.2f}-{out['max']:.2f} s, n={len(ss)}", flush=True)
        d.shot(f"fullbody_{args.setup}.png")
    finally:
        if args.out:
            json.dump(out, open(args.out, "w"), indent=1)
        d.quit(); reap(d)

if __name__ == "__main__":
    main()
