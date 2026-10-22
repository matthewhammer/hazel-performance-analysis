// ^ticket(540): a CPU profile of one use of a held tree (passed to a function that ignores it), for names. node --cpu-prof ...
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"),
  "fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> let u = t in Done"].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
const n = +process.argv[3], cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
const f = r.value(cells, n), sm = { at_col: 1, at_row: 1, cols: n, rows: n }, ev = { tag: "Way", value: "E" };
for (let i = 0; i < 5; i++) f(sm, ev);
const t0 = performance.now(); for (let i = 0; i < +process.argv[4]; i++) f(sm, ev); console.log("ms a call", ((performance.now() - t0) / +process.argv[4]).toFixed(2));
