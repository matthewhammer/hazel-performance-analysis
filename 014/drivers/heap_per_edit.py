"""^report(14): does a tab's memory grow with each edit of a big slide? Headless
Chromium (precise memory info, gc exposed), Full Body, a slider set again and
again (input + change, as the earlier drivers do); after each edit, once the
picture has redrawn and the page has settled, two forced GCs and the live JS
heap.

  python3 heap_per_edit.py <port> <edits> <out.json>"""
import json, subprocess, sys, time, urllib.request, urllib.error

port, edits, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
WD = 9555


class Chrome:
    def __init__(self):
        self.base = f"http://127.0.0.1:{WD}"
        self.proc = subprocess.Popen(["chromium.chromedriver", f"--port={WD}"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(self.base + "/status", timeout=2); break
            except Exception:
                pass
        else:
            raise SystemExit("chromedriver did not start")
        caps = {"capabilities": {"alwaysMatch": {"browserName": "chrome", "goog:chromeOptions": {"args": [
            "--headless=new", "--enable-precise-memory-info", "--js-flags=--expose-gc",
            "--window-size=1600,1100", "--no-first-run", "--no-default-browser-check"]}}}}
        r = self._req("POST", "/session", caps)
        if "sessionId" not in r.get("value", {}):
            raise SystemExit("session failed: " + json.dumps(r)[:400])
        self.sid = r["value"]["sessionId"]

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as f:
                return json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode())

    def js(self, script, args=None):
        return self._req("POST", f"/session/{self.sid}/execute/sync", {"script": script, "args": args or []}).get("value")

    def goto(self, url):
        self._req("POST", f"/session/{self.sid}/url", {"url": url})

    def quit(self):
        try:
            self._req("DELETE", f"/session/{self.sid}")
        finally:
            try:
                self.proc.terminate()
            except PermissionError:
                pass


def wait(d, js, limit=240.0):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            if d.js(js) is True:
                return time.time() - t0
        except Exception:
            pass
        time.sleep(0.5)
    return None


HEAP = """window.gc(); window.gc();
  return performance.memory ? [performance.memory.usedJSHeapSize, performance.memory.totalJSHeapSize] : null;"""
PIC = "[...document.querySelectorAll('svg[width=\"320\"][height=\"440\"]')].pop()"
SET = r"""
const [label, value] = arguments;
const inp = [...document.querySelectorAll('input[type=range]')].find(i => {
  const box = i.parentElement; return box && box.textContent.trim().replace(/-?\d+$/, '').trim() === label; });
if (!inp) return 'no slider ' + label;
window.__before = (""" + PIC + r""" || {}).outerHTML;
inp.value = String(value);
inp.dispatchEvent(new Event('input', {bubbles: true}));
inp.dispatchEvent(new Event('change', {bubbles: true}));
return 'ok';
"""
CHANGED = "const p = " + PIC + "; return !!p && p.outerHTML !== window.__before;"

d = Chrome()
rows = []
try:
    d.goto(f"http://localhost:{port}/fresh?slide=livelit-playground-full-body&panel=none")
    t = wait(d, "return !!(" + PIC + ") && [...document.querySelectorAll('input[type=range]')].length > 5;")
    print("loaded in", None if t is None else round(t, 1), "s", flush=True)
    time.sleep(8)
    base = d.js(HEAP)
    print("after load:", base, flush=True)
    rows.append({"edit": 0, "used": base[0], "total": base[1]})
    for i in range(1, edits + 1):
        value = 60 + (i * 7) % 40
        r = d.js(SET, ["shirt width", value])
        t0 = time.time()
        drew = wait(d, CHANGED, limit=120)
        time.sleep(4)
        h = d.js(HEAP)
        rows.append({"edit": i, "value": value, "set": r, "redraw_s": None if drew is None else round(drew, 2),
                     "used": h[0], "total": h[1]})
        print(f"edit {i:2} -> {value}: redraw {rows[-1]['redraw_s']} s, live heap {h[0] / 2**20:7.1f} MB "
              f"(+{(h[0] - base[0]) / 2**20:6.1f})", flush=True)
finally:
    json.dump(rows, open(out, "w"), indent=1)
    d.quit()
