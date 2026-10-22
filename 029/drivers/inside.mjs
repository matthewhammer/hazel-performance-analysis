import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const r = H.run(`let build = fun (n, acc) -> if n == 0 then acc else build(n - 1, n :: acc) in
let rep = fun (f, m) -> if m == 0 then 0 else (let z = f(1) in rep(f, m - 1)) in
let inside = fun (n, m) -> let held = build(n, []) in let f = (fun k -> let u = held in k) in rep(f, m) in
let outside = fun n -> let held = build(n, []) in (fun k -> let u = held in k) in
(inside = inside, outside = outside)`);
if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 400)); process.exit(1); }
const q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
const T = f => { for (let i = 0; i < 2; i++) f(); const t = []; for (let i = 0; i < 7; i++) { const t0 = performance.now(); f(); t.push(performance.now() - t0); } return q(t); };
for (const n of [100, 1000, 3000]) {
  const p = m => { r.value.inside(n, m); H.stepCounts(); r.value.inside(n, m); return H.stepCounts().evaluate; };
  const per_inside = (p(100) - p(0)) / 100;
  const ms_inside = (T(() => r.value.inside(n, 100)) - T(() => r.value.inside(n, 0))) / 100;
  const g = r.value.outside(n); g(1); H.stepCounts(); g(1); const per_out = H.stepCounts().evaluate;
  console.log(JSON.stringify({ n, passes_per_call_inside_hazel: per_inside, ms_per_call_inside: +ms_inside.toFixed(4), passes_per_call_from_js: per_out, ms_per_call_from_js: +T(() => g(1)).toFixed(4) }));
}
