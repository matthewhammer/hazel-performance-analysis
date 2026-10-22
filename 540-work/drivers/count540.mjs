// ^ticket(540): WeakMap gets and sets during one use of a held tree (let u = t in Done), to see whether ascription pushes walk it
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
const G = WeakMap.prototype.get, S = WeakMap.prototype.set; const inst = new Map(); let on = false;
const rec = w => { let r = inst.get(w); if (!r) inst.set(w, r = { get: 0, hit: 0, set: 0 }); return r; };
WeakMap.prototype.get = function (k) { const v = G.call(this, k); if (on) { const r = rec(this); r.get++; if (v !== undefined) r.hit++; } return v; };
WeakMap.prototype.set = function (k, v) { if (on) rec(this).set++; return S.call(this, k, v); };
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"),
  "(uses = (fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> let u = t in Done), ignore = (fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> Done))"].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
const n = +process.argv[3], cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
console.log("value:", typeof r.value, Object.keys(r.value || {}), JSON.stringify(r.value).slice(0, 200));
for (const k of ["ignore", "uses"]) {
  const f = r.value[k](cells, n), sm = { at_col: 1, at_row: 1, cols: n, rows: n }, ev = { tag: "Way", value: "E" };
  f(sm, ev); f(sm, ev); inst.clear(); on = true; f(sm, ev); on = false;
  console.log(k, n + "x" + n, JSON.stringify([...inst.values()]));
}
