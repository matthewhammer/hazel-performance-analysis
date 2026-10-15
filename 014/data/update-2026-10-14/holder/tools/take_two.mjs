// ^ticket(58): a heap snapshot of Full Body after some edits of the shirt
// width (set as ^report(14)'s drivers set it), streamed to a file.
//   node take_two.mjs <debug-port> <app-port> <edits,edits,...> <out-prefix>
// (a snapshot after each run of edits, in the same session: ids are stable)
import { createWriteStream } from "node:fs";
const [dport, aport, plan, out] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const page = (await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json()).find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0; const pending = new Map();
let file = null, bytes = 0;
ws.addEventListener("message", e => { const m = JSON.parse(e.data);
  if (m.method === "HeapProfiler.addHeapSnapshotChunk") { file.write(m.params.chunk); bytes += m.params.chunk.length; return; }
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); return r.result?.result?.value; };
const until = async (expr, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr) === true) return (Date.now() - t0) / 1000; await sleep(500); } return null; };
const PIC = `[...document.querySelectorAll('svg[width="320"][height="440"]')].pop()`;
const SET = v => `(() => { const inp = [...document.querySelectorAll('input[type=range]')].find(i => { const b = i.parentElement; return b && b.textContent.trim().replace(/-?\\d+$/, '').trim() === 'shirt width'; });
  if (!inp) return 'no slider'; window.__before = (${PIC} || {}).outerHTML; inp.value = '${v}';
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); return 'ok'; })()`;
const CHANGED = `(() => { const p = ${PIC}; return !!p && p.outerHTML !== window.__before; })()`;
await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: `http://localhost:${aport}/fresh?slide=livelit-playground-full-body&panel=none` });
console.log("loaded in", await until(`!!(${PIC}) && document.querySelectorAll('input[type=range]').length > 5`, 300000), "s");
await sleep(8000);
let k = 0;
for (const [run, m] of plan.split(",").map((x, r) => [r, +x])) {
  for (let q = 0; q < m; q++) {
    k++; const v = 60 + (k * 7) % 40;
    const r = await ev(SET(v)); const t = await until(CHANGED, 120000); await sleep(4000);
    console.log(`edit ${k} -> ${v}: ${r}, redraw ${t} s`);
  }
  await ev(`(() => { gc(); gc(); })()`);
  console.log("heap", await ev(`(performance.memory.usedJSHeapSize / 2 ** 20).toFixed(1)`), "MB; snapshot after edit", k);
  file = createWriteStream(`${out}-${k}.heapsnapshot`); bytes = 0; const t0 = Date.now();
  await send("HeapProfiler.enable");
  const r = await send("HeapProfiler.takeHeapSnapshot", { reportProgress: false, captureNumericValue: false });
  await new Promise(res => file.end(res));
  console.log("snapshot", r.error ? JSON.stringify(r.error) : "ok", (bytes / 2 ** 20).toFixed(1), "MB in", ((Date.now() - t0) / 1000).toFixed(1), "s");
}
ws.close(); process.exit(0);
