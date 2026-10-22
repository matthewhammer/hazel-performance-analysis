import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const V = {
  h_ref: "fun k -> let u = held in k",
  h_ign: "fun k -> k",
  h_tup: "fun k -> let (u, v) = (held, k) in v",
  h_case: "fun k -> case held | _ => k end",
  h_hd: "fun k -> case held | _ :: _ => k | [] => k end",
  h_ap: "fun k -> (fun x -> k)(held)",
  h_if: "fun k -> if true then k else (let u = held in k)",
};
const prog = `let build = fun (n, acc) -> if n == 0 then acc else build(n - 1, n :: acc) in
let hold = fun n -> let held = build(n, []) in (${Object.entries(V).map(([k, v]) => `${k} = (${v})`).join(", ")}) in
let hold_lit = fun held -> (${Object.entries(V).map(([k, v]) => `${k} = (${v})`).join(", ")}) in
let hold_ann = fun (held : [Int]) -> (${Object.entries(V).map(([k, v]) => `${k} = (${v})`).join(", ")}) in
(hold = hold, hold_lit = hold_lit, hold_ann = hold_ann)`;
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
const q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
const counts = typeof H.stepCounts === "function";
for (const how of ["hold", "hold_lit", "hold_ann"]) for (const n of [300, 3000]) {
  const h = how === "hold" ? r.value.hold(n) : r.value[how](Array.from({ length: n }, (_, i) => i + 1));
  const row = [];
  for (const k of Object.keys(V)) {
    for (let i = 0; i < 3; i++) h[k](7);
    const ts = []; for (let i = 0; i < 15; i++) { const t = performance.now(); h[k](7); ts.push(performance.now() - t); }
    let st = ""; if (counts) { H.stepCounts(); h[k](7); const c = H.stepCounts(); st = "/" + (c.evaluate || 0); }
    row.push(`${k} ${q(ts).toFixed(3)}${st}`);
  }
  console.log(how.padEnd(9), String(n).padStart(5), row.join("  "));
}
