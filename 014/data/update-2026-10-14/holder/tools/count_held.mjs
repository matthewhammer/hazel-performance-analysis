// ^ticket(58): does a tab hold more browser-side closures with each edit?
// After load and after each edit of Full Body's shirt width (set as
// ^report(14)'s drivers set it), two forced GCs, then: Chrome's DOM counters
// (documents, nodes incl. detached, JS event listeners), the live JS heap,
// and, from wrappers installed before the page's own scripts, the listeners
// added minus removed per target kind, observers observing, intervals
// running, timeouts and animation frames pending.
//   node count_held.mjs <debug-port> <app-port> <edits> <out.json>
import { writeFileSync } from "node:fs";
const [dport, aport, edits, out] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const page = (await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json()).find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0; const pending = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); return r.result?.result?.value; };
const until = async (expr, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr) === true) return (Date.now() - t0) / 1000; await sleep(500); } return null; };
const WRAP = `(() => {
  const c = self.__held = { listeners: {}, observing: 0, observers: 0, intervals: 0, timeouts: 0, frames: 0 };
  const kind = t => t === self ? 'window' : t === self.document ? 'document' : (t && t.nodeType === 1) ? 'element' : (t && t.constructor && t.constructor.name) || 'other';
  const seen = new WeakMap();
  const key = (t, type, f, o) => type + '|' + (typeof o === 'boolean' ? o : !!(o && o.capture));
  const add = EventTarget.prototype.addEventListener, rem = EventTarget.prototype.removeEventListener;
  EventTarget.prototype.addEventListener = function (type, f, o) {
    if (f) { let m = seen.get(this); if (!m) seen.set(this, m = new Map()); let s = m.get(key(this, type, f, o)); if (!s) m.set(key(this, type, f, o), s = new Set());
      if (!s.has(f)) { s.add(f); const k = kind(this); c.listeners[k] = (c.listeners[k] || 0) + 1; } }
    return add.call(this, type, f, o); };
  EventTarget.prototype.removeEventListener = function (type, f, o) {
    const m = seen.get(this), s = m && m.get(key(this, type, f, o));
    if (s && s.delete(f)) { const k = kind(this); c.listeners[k]--; }
    return rem.call(this, type, f, o); };
  for (const O of ['ResizeObserver', 'MutationObserver', 'IntersectionObserver']) {
    const B = self[O]; if (!B) continue;
    self[O] = class extends B { constructor(...a) { super(...a); c.observers++; this.__n = 0; }
      observe(...a) { if (!this.__n++) c.observing++; return super.observe(...a); }
      disconnect() { if (this.__n) { this.__n = 0; c.observing--; } return super.disconnect(); } };
  }
  const si = self.setInterval, ci = self.clearInterval, live = new Set();
  self.setInterval = (...a) => { const id = si(...a); live.add(id); c.intervals = live.size; return id; };
  self.clearInterval = id => { live.delete(id); c.intervals = live.size; return ci(id); };
  const st = self.setTimeout, ct = self.clearTimeout, tl = new Set();
  self.setTimeout = (f, ...a) => { let id; id = st((...b) => { tl.delete(id); c.timeouts = tl.size; return typeof f === 'function' ? f(...b) : undefined; }, ...a); tl.add(id); c.timeouts = tl.size; return id; };
  self.clearTimeout = id => { tl.delete(id); c.timeouts = tl.size; return ct(id); };
  const ra = self.requestAnimationFrame, ca = self.cancelAnimationFrame, fl = new Set();
  self.requestAnimationFrame = f => { let id; id = ra(t => { fl.delete(id); c.frames = fl.size; return f(t); }); fl.add(id); c.frames = fl.size; return id; };
  self.cancelAnimationFrame = id => { fl.delete(id); c.frames = fl.size; return ca(id); };
})();`;
const PIC = `[...document.querySelectorAll('svg[width="320"][height="440"]')].pop()`;
const SET = v => `(() => { const inp = [...document.querySelectorAll('input[type=range]')].find(i => { const b = i.parentElement; return b && b.textContent.trim().replace(/-?\\d+$/, '').trim() === 'shirt width'; });
  if (!inp) return 'no slider'; window.__before = (${PIC} || {}).outerHTML; inp.value = '${v}';
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); return 'ok'; })()`;
const CHANGED = `(() => { const p = ${PIC}; return !!p && p.outerHTML !== window.__before; })()`;
const rows = [];
const sample = async label => {
  await ev(`(() => { gc(); gc(); })()`);
  const dom = (await send("Memory.getDOMCounters")).result;
  const s = await ev(`({ heapMB: +(performance.memory.usedJSHeapSize / 2 ** 20).toFixed(1), shown: document.getElementsByTagName('*').length, held: self.__held })`);
  const row = { label, ...dom, ...s };
  rows.push(row); console.log(JSON.stringify(row));
};
await send("Page.enable"); await send("Runtime.enable");
await send("Page.addScriptToEvaluateOnNewDocument", { source: WRAP });
await send("Page.navigate", { url: `http://localhost:${aport}/fresh?slide=livelit-playground-full-body&panel=none` });
console.log("loaded in", await until(`!!(${PIC}) && document.querySelectorAll('input[type=range]').length > 5`, 300000), "s");
await sleep(8000);
await sample("load");
for (let k = 1; k <= +edits; k++) {
  const v = 60 + (k * 7) % 40;
  const r = await ev(SET(v)); const t = await until(CHANGED, 120000); await sleep(4000);
  console.log(`edit ${k} -> ${v}: ${r}, redraw ${t} s`);
  await sample(`edit ${k}`);
}
writeFileSync(out, JSON.stringify(rows, null, 1));
ws.close(); process.exit(0);
