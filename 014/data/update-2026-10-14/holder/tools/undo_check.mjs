// ^ticket(58): does undo still restore Full Body? Load the slide, set the
// shirt width (as ^report(14)'s drivers do), undo (Ctrl+Z), redo
// (Ctrl+Shift+Z), then edit again; after each step, the slider's value, a
// hash of the picture, the program text's hash, and any page exceptions.
//   node undo_check.mjs <debug-port> <app-port>
const [dport, aport] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const page = (await (await fetch(`http://127.0.0.1:${dport}/json/list`)).json()).find(t => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r, { once: true }));
let n = 0; const pending = new Map(), errors = [];
ws.addEventListener("message", e => { const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description?.slice(0, 200) || m.params.exceptionDetails.text);
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push("console: " + m.params.args.map(a => a.value ?? a.description ?? "").join(" ").slice(0, 200));
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++n; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); return r.result?.result?.value; };
const until = async (expr, ms) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr) === true) return (Date.now() - t0) / 1000; await sleep(300); } return null; };
const PIC = `[...document.querySelectorAll('svg[width="320"][height="440"]')].pop()`;
const SLIDER = `[...document.querySelectorAll('input[type=range]')].find(i => { const b = i.parentElement; return b && b.textContent.trim().replace(/-?\\d+$/, '').trim() === 'shirt width'; })`;
const SET = v => `(() => { const inp = ${SLIDER}; if (!inp) return 'no slider'; window.__before = (${PIC} || {}).outerHTML; inp.value = '${v}';
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true })); return 'ok'; })()`;
const ARM = `(() => { window.__before = (${PIC} || {}).outerHTML; return true; })()`;
const CHANGED = `(() => { const p = ${PIC}; return !!p && p.outerHTML !== window.__before; })()`;
const STATE = `(() => { const h = s => { let a = 0; for (let i = 0; i < s.length; i++) a = (Math.imul(a, 31) + s.charCodeAt(i)) | 0; return (a >>> 0).toString(16); };
  const p = ${PIC}, inp = ${SLIDER}, code = document.querySelector('.code-container, .code') ;
  return { slider: inp && inp.value, picture: p ? h(p.outerHTML) : null, text: code ? h(code.innerText) : null,
           holes: document.querySelectorAll('.empty-hole').length, errs: document.querySelectorAll('.error, .err, .type-error').length }; })()`;
const key = async (k, code, mods) => {
  for (const type of ["keyDown", "keyUp"])
    await send("Input.dispatchKeyEvent", { type, key: k, code, modifiers: mods, windowsVirtualKeyCode: k.toUpperCase().charCodeAt(0) });
};
await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: `http://localhost:${aport}/fresh?slide=livelit-playground-full-body&panel=none` });
console.log("loaded in", await until(`!!(${PIC}) && document.querySelectorAll('input[type=range]').length > 5`, 300000), "s");
await sleep(8000);
const s0 = await ev(STATE); console.log("start ", JSON.stringify(s0));
await ev(SET(67)); console.log("edit  redraw", await until(CHANGED, 120000)); await sleep(3000);
const s1 = await ev(STATE); console.log("edited", JSON.stringify(s1));
await ev(ARM); await key("z", "KeyZ", 2); console.log("undo  redraw", await until(CHANGED, 120000)); await sleep(3000);
const s2 = await ev(STATE); console.log("undone", JSON.stringify(s2));
await ev(ARM); await key("z", "KeyZ", 2 | 8); console.log("redo  redraw", await until(CHANGED, 120000)); await sleep(3000);
const s3 = await ev(STATE); console.log("redone", JSON.stringify(s3));
await ev(SET(81)); console.log("edit2 redraw", await until(CHANGED, 120000)); await sleep(3000);
const s4 = await ev(STATE); console.log("edit2 ", JSON.stringify(s4));
await ev(ARM); await key("z", "KeyZ", 2); console.log("undo2 redraw", await until(CHANGED, 120000)); await sleep(3000);
const s5 = await ev(STATE); console.log("undo2 ", JSON.stringify(s5));
const same = (a, b) => a.slider === b.slider && a.picture === b.picture && a.text === b.text;
console.log(JSON.stringify({ undo_restores_start: same(s0, s2), redo_restores_edit: same(s1, s3), undo2_restores_redo: same(s3, s5), errors }));
ws.close(); process.exit(0);
