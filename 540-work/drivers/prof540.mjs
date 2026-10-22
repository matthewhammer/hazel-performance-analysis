// ^ticket(540): a CPU profile of the held tree's calls (tree.hz) at one size, for function names: run with node --cpu-prof
//   node --stack-size=8000 --cpu-prof --cpu-prof-dir=<dir> prof540.mjs <hazelLib.bc.js> <n> <calls>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"), "held_tree"].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
const n = +process.argv[3], cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
const ht = r.value(cells, n), sm = { at_col: n / 2 - 1, at_row: n / 2, cols: n, rows: n }, ev = { tag: "Way", value: "E" };
console.log(JSON.stringify(ht(sm, ev)));
const t0 = performance.now(); for (let i = 0; i < +process.argv[4]; i++) ht(sm, ev); console.log("ms a call", ((performance.now() - t0) / +process.argv[4]).toFixed(2));
