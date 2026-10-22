// ^ticket(540): which use of a held tree costs O(N) a call. Each probe builds the tree inside Hazel (tree.hz's build), holds it in a closure and does
// one thing with it per call; median ms per call at each size. node --stack-size=8000 probe540.mjs <hazel-lib.js> <sizes>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const probes = `
let mk = fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in t in
let ignore = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> Done in
let match_top = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> case t | Leaf => Done | Node(_, _, _, _) => Done end in
let pass = fun (cells, w) -> let t = mk(cells, w) in let f = fun u -> 0 in fun (n, e) -> if f(t) == 0 then Done else Done in
let first = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> case lookup(t, 0) | Some(_) => Done | None => Done end in
let mid = fun (cells, w) -> let t = mk(cells, w) in fun (n, e) -> case lookup(t, n.at_row * n.cols + n.at_col) | Some(_) => Done | None => Done end in
(mk = mk, ignore = ignore, match_top = match_top, pass = pass, first = first, mid = mid)`;
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"), probes].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 800)); process.exit(1); }
const V = r.value, q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
for (const n of process.argv[3].split(",").map(Number)) {
  const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  const sm = { at_col: n / 2 - 1, at_row: n / 2, cols: n, rows: n }, ev = { tag: "Way", value: "E" };
  const row = { n };
  for (const k of ["ignore", "match_top", "pass", "first", "mid"]) {
    const f = V[k](cells, n); for (let i = 0; i < 3; i++) f(sm, ev);
    const ts = []; for (let i = 0; i < 30; i++) { const a = performance.now(); f(sm, ev); ts.push(performance.now() - a); }
    row[k] = +q(ts).toFixed(3);
  }
  console.log(JSON.stringify(row));
}
