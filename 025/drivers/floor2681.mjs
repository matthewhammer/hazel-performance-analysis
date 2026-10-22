// ^ticket(535): why #2681 raises a library call's floor. Wraps WeakMap's get and set around hazel-lib.js
// (no rebuild) to count, per call, the memo's lookups and writes, and to time the calls with its writes
// switched off.
//   node --stack-size=8000 floor2681.mjs <hazel-lib.js> <mode> [sizes]
//   mode: count   per call, each WeakMap's gets, hits and sets (and the key kinds of the sets)
//         plain   time idA, noann and shipped, nothing wrapped
//         noset   time them with the busiest-writing WeakMap's set a no-op (found by a count run first)
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
const MODE = process.argv[3] || "count";
const RealGet = WeakMap.prototype.get, RealSet = WeakMap.prototype.set;
const inst = new Map(); let counting = false; let skip = null;
const rec = wm => { let r = inst.get(wm); if (!r) { r = { id: inst.size, get: 0, hit: 0, set: 0, kinds: {} }; inst.set(wm, r); } return r; };
// a key's kind: an OCaml list cell is a JS array [0, head, tail]; a term node is a block with another tag
const kind = k => Array.isArray(k) ? (k.length === 3 && k[0] === 0 && (Array.isArray(k[2]) || k[2] === 0) ? "list cell" : `block tag ${k[0]} len ${k.length}`) : typeof k;
if (MODE === "count") {
  WeakMap.prototype.get = function (k) { const v = RealGet.call(this, k); if (counting) { const r = rec(this); r.get++; if (v !== undefined) r.hit++; } return v; };
  WeakMap.prototype.set = function (k, v) { if (counting) { const r = rec(this); r.set++; const kk = kind(k); r.kinds[kk] = (r.kinds[kk] || 0) + 1; } return RealSet.call(this, k, v); };
} else if (MODE === "noset") {
  // the memo is the WeakMap that takes the most sets during a call; learn it on a warm-up call, then skip its sets
  let learn = true;
  WeakMap.prototype.set = function (k, v) { if (learn && counting) rec(this).set++; if (this === skip) return this; return RealSet.call(this, k, v); };
  globalThis.__learnDone = () => { learn = false; skip = [...inst.entries()].sort((a, b) => b[1].set - a[1].set)[0]?.[0] || null; };
}
const KCG = "/home/matthew/kcg-531/dress-up/js/";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const page = { console, Math, JSON, Array, Object, String, Number, Boolean, Map, Set, Promise, RegExp, Error, Symbol, location: { search: "?logic=hazel" },
  setTimeout: () => 0, clearTimeout() {}, performance, document: { head: { append() {} }, getElementById: () => null, body: { classList: { contains: () => false } } }, addEventListener() {},
  state: { scripts: { on: false, common: null, rooms: {} }, background: {} } };
page.window = page; page.Hazel = H; vm.createContext(page);
vm.runInContext(fs.readFileSync(KCG + "25-scripting.js", "utf8") + ";globalThis.__S={SCRIPT_PREAMBLE,SCRIPT_COMMON,SCRIPT_WORLD};", page);
const S = page.__S;
const none = vm.runInContext("scriptNoGlobals()", page);
const BODY = `
let findA = fun (cs, c, r) : ([Cell], Int, Int) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findA(rest, c, r) end in
let findU = fun (cs, c, r) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findU(rest, c, r) end in
let mk = fun look -> fun (g, e) : (Globals, Event) -> case e
  | Way(d) => let c = g.at_col + 1 in let r = g.at_row in case look(g.cells, c, r) | Some(x) => GoSquare(c, r, "W", Done) | None => Done end
  | _ => Done end in
(shipped = mk(findA), noann = mk(findU), idA = fun (g, e) : (Globals, Event) -> Done)`;
const r = H.run([S.SCRIPT_PREAMBLE, BODY].join("\n")); if (r.errors && r.errors.length) { console.error(r.errors); process.exit(1); }
const V = r.value;
const q = (a, p) => a.slice().sort((x, y) => x - y)[Math.floor(p * a.length)];
// GC time while a variant is timed, per call: is the floor's rise the collector's?
import { PerformanceObserver } from "node:perf_hooks";
const gcs = []; new PerformanceObserver(l => { for (const e of l.getEntries()) gcs.push([e.startTime, e.duration]); }).observe({ entryTypes: ["gc"] });
const windows = {};   // variant -> [start, end, calls]: GC entries are matched to it by their start time, once delivered
const T = (f, R, name) => { for (let i = 0; i < 3; i++) f(); const t = []; const t00 = performance.now(); let i = 0;
  for (; i < R; i++) { const t0 = performance.now(); f(); t.push(performance.now() - t0); if (performance.now() - t00 > 2500 && i >= 8) break; }
  if (name) windows[name] = [t00, performance.now(), i + (i < R ? 1 : 0)]; return +q(t, .5).toFixed(3); };
const globalsOf = n => { const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  return { ...none, at_col: Math.floor(n / 2) - 1, at_row: Math.floor(n / 2), cols: n, rows: n, cells }; };
const ev = { tag: "Way", value: "E" };
const out = { mode: MODE, lib: process.argv[2] };
for (const n of (process.argv[4] || "16,24").split(",").map(Number)) {
  const g = globalsOf(n); const row = {};
  if (MODE === "count") {
    for (const k of ["idA", "noann", "shipped"]) {
      V[k](g, ev); inst.clear(); counting = true; V[k](g, ev); counting = false;
      row[k] = [...inst.values()].filter(x => x.get + x.set > 0).map(x => ({ get: x.get, hit: x.hit, set: x.set, kinds: x.kinds }));
    }
  } else {
    if (MODE === "noset") { counting = true; V.idA(g, ev); counting = false; globalThis.__learnDone(); }
    const R = n >= 16 ? 30 : 60;
    for (const k of ["idA", "noann", "shipped"]) row[k] = T(() => V[k](g, ev), R, k);
    // the observer reports asynchronously: let it catch up before reading
    await new Promise(res => setTimeout(res, 50));
    row.gc_ms_per_call = Object.fromEntries(Object.entries(windows).map(([k, [a, b, n]]) => [k, +(gcs.filter(([s]) => s >= a && s <= b).reduce((x, [, d]) => x + d, 0) / n).toFixed(3)]));
  }
  out[`${n}x${n}`] = row; console.log(n, JSON.stringify(row));
}
fs.writeFileSync(`floor_${MODE}_${process.argv[5] || "run"}.json`, JSON.stringify(out, null, 1));
