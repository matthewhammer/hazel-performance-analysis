// ^ticket(540): the World rule with the map held in a balanced search tree (tree.hz), beside ^report(25)'s held list, unannotated
// list and neighbours-only rules, in Hazel's JS library, per map size: median ms a call, answers checked against the game's.
//   node --stack-size=8000 tree540.mjs <hazel-lib.js> <sizes> <label>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
// the shared preamble and helpers (^report(25)'s held listing's program, its last line dropped), then the tree, then a record of rules
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const nthU = `let nthU = fun (cs, i) -> case cs | [] => None | x :: rest => if i == 0 then Some(x) else nthU(rest, i - 1) end in`;
const findU = `let findU = fun (cs, c, r) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findU(rest, c, r) end in`;
const prog = [base, nthU, findU, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"),
  held.slice(held.lastIndexOf("let held = fun (cells : [Cell]) ->"), -1).join("\n").replace("fun (cells : [Cell])", "fun cells"),
  T.near.split("\n").slice(T.near.split("\n").findIndex(l => l.startsWith("let near = fun (n, e)")), -1).join("\n"),
  `(held = held, held_tree = held_tree, near = near)`].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 800)); process.exit(1); }
const V = r.value;
const q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
const time = (f, R) => { for (let i = 0; i < 3; i++) f(); const t = []; const t0 = performance.now(); for (let i = 0; i < R; i++) { const a = performance.now(); f(); t.push(performance.now() - a); if (performance.now() - t0 > 2500 && i >= 8) break; } return +q(t).toFixed(3); };
const out = [];
for (const n of process.argv[3].split(",").map(Number)) {
  const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  const ac = Math.floor(n / 2) - 1, ar = Math.floor(n / 2), ev = { tag: "Way", value: "E" }, sm = { at_col: ac, at_row: ar, cols: n, rows: n };
  const want = JSON.stringify({ tag: "GoSquare", value: [ac + 1, ar, "W", { tag: "Done" }] });
  let t0 = performance.now(); const ht = V.held_tree(cells, n); const tree_setup = performance.now() - t0;
  t0 = performance.now(); const hl = V.held(cells); const held_setup = performance.now() - t0;
  const near = cells.filter(x => Math.abs(x.col - ac) <= 1 && Math.abs(x.row - ar) <= 1);
  for (const [k, f] of [["tree", () => ht(sm, ev)], ["held", () => hl(sm, ev)], ["near", () => V.near({ ...sm, near }, ev)]])
    if (JSON.stringify(f()) !== want) { console.error(k, n, JSON.stringify(f()), "wanted", want); process.exit(1); }
  const R = n >= 32 ? 20 : 60;
  const row = { n, cells: n * n, tree_setup: +tree_setup.toFixed(2), held_setup: +held_setup.toFixed(2),
    tree: time(() => ht(sm, ev), R), held: time(() => hl(sm, ev), R), near: time(() => V.near({ ...sm, near }, ev), R) };
  console.log(JSON.stringify(row)); out.push(row);
}
fs.writeFileSync(`tree_${process.argv[4] || "run"}.json`, JSON.stringify(out, null, 1));
