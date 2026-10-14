// ^report(14): the sizes of the page's long-lived tables after load and after
// each edit, read from a probe build (patches/count_id_keyed_tables.patch).
//   node count_tables.mjs <debug-port> <app-port> <edits>
const [dport, aport, plan] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const page = (await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json()).find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0; const pending = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); return r.result?.result?.value; };
const until = async (expr, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr) === true) return (Date.now() - t0) / 1000; await sleep(500); } return null; };
const PIC = `[...document.querySelectorAll('svg[width="320"][height="440"]')].pop()`;
const SET = v => `(() => { const inp = [...document.querySelectorAll('input[type=range]')].find(i => { const b = i.parentElement; return b && b.textContent.trim().replace(/-?\\d+$/, '').trim() === ${JSON.stringify(process.env.LABEL || 'shirt width')}; });
  if (!inp) return 'no slider'; window.__before = (${PIC} || {}).outerHTML; inp.value = '${v}';
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); return 'ok'; })()`;
const CHANGED = `(() => { const p = ${PIC}; return !!p && p.outerHTML !== window.__before; })()`;
const HEAP = `(() => { gc(); gc(); return performance.memory.usedJSHeapSize; })()`;
const MB = b => (b / 2 ** 20).toFixed(1);
let k = 0;
const edit = async () => { k++; const v = 60 + (k * 7) % 40; await ev(SET(v)); const t = process.env.SETTLE ? (await sleep(+process.env.SETTLE * 1000), 'fixed ' + process.env.SETTLE) : await until(CHANGED, 120000); await sleep(4000); console.log(`edit ${k} -> ${v}: redraw ${t} s`); };
const sizes = async label => {
  const h = await ev(HEAP), t = await ev("JSON.stringify(window.__hazel45 ? __hazel45() : null)");
  console.log(JSON.stringify({ label, heapMB: +(h / 2 ** 20).toFixed(1), sizes: JSON.parse(t) }));
};
const census = async label => {
  const h = await ev(HEAP), out = [];
  for (const proto of ["Map", "Set", "WeakMap"]) {
    const p = (await send("Runtime.evaluate", { expression: `${proto}.prototype` })).result.result.objectId;
    const arr = (await send("Runtime.queryObjects", { prototypeObjectId: p })).result.objects.objectId;
    const r = await send("Runtime.callFunctionOn", { objectId: arr, returnByValue: true, functionDeclaration: `function () {
      if (${JSON.stringify(proto)} === "WeakMap") return [this.length];
      return this.map(m => [m.size, [...m.keys()].slice(0, 3).map(x => typeof x === "string" ? x.slice(0, 40) : Array.isArray(x) ? "[array " + x.length + "]" : typeof x)])
        .sort((a, b) => b[0] - a[0]).slice(0, 6); }` });
    out.push([proto, r.result.result.value]);
  }
  console.log(`\n== ${label}: live heap ${MB(h)} MB`);
  for (const [proto, v] of out) console.log(proto, JSON.stringify(v));
};
await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: `http://localhost:${aport}/fresh?slide=${process.env.SLIDE || "livelit-playground-full-body"}&panel=none` });
console.log("loaded in", await until(`document.querySelectorAll('input[type=range]').length > ${process.env.MINSLIDERS || 5}`, 300000), "s");
await sleep(8000);
await sizes("load"); for (let i = 0; i < +plan; i++) { await edit(); await sizes(`edit ${k}`); }
ws.close(); process.exit(0);
