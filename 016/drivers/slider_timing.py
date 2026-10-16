#!/usr/bin/env python3
"""Where does a slider release go, on Emotion (Kids' Choice), in Firefox?

Headless Firefox over WebDriver (deck_regress.Driver), a fresh profile, the
slide opened at /fresh with the debug panel, its Frame Timing, Statics,
Worker Messaging and Evaluation sections expanded. Then, per run, the eye
size slider is set and released (an `input` event, then `change`, which is
the commit), and we wait for the face's eyes to be redrawn at the new size.

Reports per run: the input and change handlers' own time, the total until
the face changed, and every stretch over 50 ms when the main thread could
not run a 10 ms timer. Then the debug panel's text, for the per-frame
breakdown (statics / syntax / ...) and the worker's timings.

  scripts/slider_timing.py --port 8341 --runs 4
"""
import argparse, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deck_regress import Driver

SLIDE = "livelit-playground-emotion-kids-choice"
SECTIONS = ["Frame Timing", "Statics", "Worker Messaging", "Evaluation"]

HELPERS = r"""
window.__face = () => [...document.querySelectorAll('svg')]
  .find(s => (s.getAttribute('viewBox') || '').startsWith('0 -80 200'));
window.__eyeR = () => {
  const f = __face();
  const c = f && [...f.querySelectorAll('circle')].find(c => c.getAttribute('cy') === '100');
  return c ? c.getAttribute('r') : null;
};
window.__slider = label => {
  for (const inp of document.querySelectorAll('input[type=range]')) {
    const box = inp.parentElement;
    if (box && box.textContent.trim().startsWith(label)) return inp;
  }
  return null;
};
window.__start = (label, value) => {
  window.__r = null;
  const inp = __slider(label);
  if (!inp) { window.__r = 'no slider ' + label; return; }
  const before = __eyeR();
  const gaps = []; let last = performance.now(), running = true;
  const tick = () => {
    const now = performance.now();
    if (now - last > 50) gaps.push(Math.round(now - last));
    last = now;
    if (running) setTimeout(tick, 10);
  };
  setTimeout(tick, 10);
  const t0 = performance.now();
  inp.value = String(value);
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  const tInput = performance.now() - t0;
  inp.dispatchEvent(new Event('change', {bubbles: true}));
  const tChange = performance.now() - t0 - tInput;
  const poll = () => {
    const after = __eyeR(), el = performance.now() - t0;
    if (after !== before || el > 120000) {
      running = false;
      window.__r = {value, before, after, inputMs: Math.round(tInput),
        changeMs: Math.round(tChange), totalMs: Math.round(el), gapsMs: gaps};
    } else setTimeout(poll, 20);
  };
  setTimeout(poll, 20);
};
"""


def wait(d, js, limit=180.0):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if d.js(js) is True:
                return time.time() - t0
        except Exception:
            pass
        time.sleep(0.2)
    return None


def reap(d):
    """geckodriver is a snap here: terminate() is refused, so signal it
    from inside the snap (see playground_timing.py)."""
    try:
        subprocess.run(["snap", "run", "--shell", "firefox.geckodriver", "-c",
                        f"kill {d.proc.pid}"], timeout=20,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8341)
    ap.add_argument("--wd-port", type=int, default=4762)
    ap.add_argument("--runs", type=int, default=4)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    d = Driver(args.port, args.wd_port)
    report = {}
    try:
        d.goto(f"/fresh?slide={SLIDE}&panel=debug")
        load = wait(d, "return document.querySelectorAll('input[type=range]').length > 3 && "
                       "!!([...document.querySelectorAll('svg')].find(s => "
                       "(s.getAttribute('viewBox') || '').startsWith('0 -80 200')));")
        report["load_s"] = load
        print(f"load {load}", flush=True)
        if load is None:
            return
        # metrics record only with the Debug Sidebar setting on: the menu's toggle
        flipped = d.js("""
          const el = [...document.querySelectorAll('*')]
            .filter(e => e.children.length <= 3 && e.textContent.trim() === 'Debug Sidebar');
          if (!el.length) return 'no toggle';
          el[el.length - 1].click();
          return el.length;""")
        report["debug_toggle"] = flipped
        print("debug toggle", flipped, flush=True)
        time.sleep(2)
        # expand the debug panel's timing sections: click each title
        opened = d.js("""
          const want = arguments[0], got = [];
          const root = document.getElementById('debug-sidebar') || document;
          for (const t of want) {
            const el = [...root.querySelectorAll('.debug-section-title')]
              .find(e => e.textContent.replace(/[▸▾]/g, '').trim() === t);
            if (el) { el.click(); got.push(t); }
          }
          return got;""", [SECTIONS])
        report["sections_opened"] = opened
        print("sections", opened, flush=True)
        time.sleep(3)
        d.js(HELPERS)
        runs = []
        for i, v in enumerate([80, 20, 70, 30][:args.runs]):
            time.sleep(4)  # let the page settle between runs
            d.js("__start(arguments[0], arguments[1]);", ["eye size", v])
            wait(d, "return window.__r !== null && window.__r !== undefined;", limit=150)
            r = d.js("return window.__r;")
            runs.append(r)
            print(json.dumps(r), flush=True)
        report["runs"] = runs
        time.sleep(2)
        report["panel"] = d.js("const e = document.getElementById('debug-sidebar'); "
                               "return e ? e.innerText : null;")
    finally:
        d.quit()
        reap(d)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(report, f, indent=1)
    print((report.get("panel") or "(no panel)")[:6000])


if __name__ == "__main__":
    main()
