// ^ticket(540): narrowing what makes using a held value O(N): each probe holds a value of n*n parts in a closure and does one thing
// with it per call. node --stack-size=8000 probe540b.mjs <hazel-lib.js> <sizes>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const probes = `
let mk = fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in t in
let ints = fun k -> if k == 0 then [] else k :: ints(k - 1) in
let tree_let = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> let u = t in Done in
let tree_pass = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> if (fun u -> 0)(t) == 0 then Done else Done in
let tree_pass_ann = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> if (fun (u : Tree) -> 0)(t) == 0 then Done else Done in
let list_pass = fun (cells, w) -> let xs = ints(length(cells)) in fun (n, e) -> if (fun u -> 0)(xs) == 0 then Done else Done in
let list_case = fun (cells, w) -> let xs = ints(length(cells)) in fun (n, e) -> case xs | [] => Done | _ :: _ => Done end in
let pair_pass = fun (cells, w) -> let xs = ints(length(cells)) in let p = (xs, 1) in fun (n, e) -> if (fun u -> 0)(p) == 0 then Done else Done in
(tree_let = tree_let, tree_pass = tree_pass, tree_pass_ann = tree_pass_ann, list_pass = list_pass, list_case = list_case, pair_pass = pair_pass)`;
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"), probes].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 800)); process.exit(1); }
const V = r.value, q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
for (const n of process.argv[3].split(",").map(Number)) {
  const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  const sm = { at_col: 1, at_row: 1, cols: n, rows: n }, ev = { tag: "Way", value: "E" }, row = { n };
  for (const k of ["tree_let", "tree_pass", "tree_pass_ann", "list_pass", "list_case", "pair_pass"]) {
    const f = V[k](cells, n); for (let i = 0; i < 3; i++) f(sm, ev);
    const ts = []; for (let i = 0; i < 25; i++) { const a = performance.now(); f(sm, ev); ts.push(performance.now() - a); }
    row[k] = +q(ts).toFixed(3);
  }
  console.log(JSON.stringify(row));
}
