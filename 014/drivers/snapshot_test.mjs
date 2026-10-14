// does a heap snapshot work at all here? on the page that is open
const [dport, url] = process.argv.slice(2);
const page = (await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json()).find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0, bytes = 0; const pending = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } else if (m.method === "HeapProfiler.addHeapSnapshotChunk") bytes += m.params.chunk.length; });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
await send("Page.enable"); await send("Page.navigate", { url }); await new Promise(r => setTimeout(r, +(process.env.WAIT || 3) * 1000));
await send("HeapProfiler.enable");
const t = setTimeout(() => { console.log("no answer in 900 s (renderer gone?)"); process.exit(1); }, 900000);
const r = await send("HeapProfiler.takeHeapSnapshot", { reportProgress: false });
clearTimeout(t); console.log("snapshot ok:", (bytes / 2 ** 20).toFixed(1), "MB of JSON", r.error ? JSON.stringify(r.error) : ""); process.exit(0);
