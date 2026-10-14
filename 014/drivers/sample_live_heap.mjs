// ^report(14): which code allocated what a #2597 tab keeps after each edit?
// Drives a headless Chromium over the DevTools protocol: loads Full Body,
// warms up with a few edits of the shirt-width slider, then samples the
// heap (V8's sampling heap profiler, live objects only) over more edits,
// forces GCs, and writes the profile and a summary.
//   node sample_live_heap.mjs <debug-port> <app-port> <warm> <edits> <out-prefix>
import { writeFileSync } from "node:fs";
const [dport, aport, warm, edits, out] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const targets = await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json();
const page = targets.find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0; const pending = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result?.exceptionDetails) return { error: r.result.exceptionDetails.text + " " + (r.result.exceptionDetails.exception?.description || "") }; return r.result?.result?.value; };
const until = async (expr, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr) === true) return (Date.now() - t0) / 1000; await sleep(500); } return null; };
const PIC = `[...document.querySelectorAll('svg[width="320"][height="440"]')].pop()`;
const SET = v => `(() => { const inp = [...document.querySelectorAll('input[type=range]')].find(i => { const b = i.parentElement; return b && b.textContent.trim().replace(/-?\\d+$/, '').trim() === 'shirt width'; });
  if (!inp) return 'no slider'; window.__before = (${PIC} || {}).outerHTML; inp.value = '${v}';
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); return 'ok'; })()`;
const CHANGED = `(() => { const p = ${PIC}; return !!p && p.outerHTML !== window.__before; })()`;
const HEAP = `(() => { gc(); gc(); return performance.memory.usedJSHeapSize; })()`;
const MB = b => (b / 2 ** 20).toFixed(1);
let k = 0;
const edit = async () => { k++; const v = 60 + (k * 7) % 40; const r = await ev(SET(v)); const t = await until(CHANGED, 120000); await sleep(4000); const h = await ev(HEAP); console.log(`edit ${k} -> ${v}: ${r}, redraw ${t} s, live heap ${MB(h)} MB`); return h; };

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: `http://localhost:${aport}/fresh?slide=livelit-playground-full-body&panel=none` });
console.log("loaded in", await until(`!!(${PIC}) && document.querySelectorAll('input[type=range]').length > 5`, 300000), "s");
await sleep(8000);
console.log("after load:", MB(await ev(HEAP)), "MB");
for (let i = 0; i < +warm; i++) await edit();
const h0 = await ev(HEAP);
await send("HeapProfiler.enable");
await send("HeapProfiler.startSampling", { samplingInterval: 32768, includeObjectsCollectedByMajorGC: false, includeObjectsCollectedByMinorGC: false });
let h1 = h0;
for (let i = 0; i < +edits; i++) h1 = await edit();
await ev(HEAP);
const prof = (await send("HeapProfiler.stopSampling")).result.profile;
writeFileSync(out + ".heapprofile", JSON.stringify(prof));
console.log(`sampled over ${edits} edits: live heap ${MB(h0)} -> ${MB(h1)} MB (+${MB(h1 - h0)})`);

// summary: live bytes by allocating function (self), and the heaviest stacks
const self = new Map(), stacks = [];
const walk = (node, path) => {
  const f = node.callFrame, name = `${f.functionName || "(anon)"} @${f.lineNumber + 1}`;
  const here = [...path, name];
  if (node.selfSize) { self.set(name, (self.get(name) || 0) + node.selfSize); stacks.push([node.selfSize, here]); }
  for (const c of node.children || []) walk(c, here);
};
walk(prof.head, []);
const total = [...self.values()].reduce((a, b) => a + b, 0);
let txt = `live sampled bytes allocated during the edits: ${MB(total)} MB\n\nby allocating function:\n`;
for (const [name, b] of [...self].sort((a, b) => b[1] - a[1]).slice(0, 40)) txt += `${MB(b).padStart(8)} MB  ${name}\n`;
txt += `\nheaviest stacks (innermost 14 frames):\n`;
for (const [b, path] of stacks.sort((a, b) => b[0] - a[0]).slice(0, 25)) txt += `\n${MB(b)} MB\n  ` + path.slice(-14).reverse().join("\n  ") + "\n";
writeFileSync(out + ".txt", txt);
console.log(txt.split("\n").slice(0, 45).join("\n"));
ws.close();
process.exit(0);
