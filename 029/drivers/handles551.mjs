// ^ticket(551): the World rule with the map passed at every call, converted from JS each time against passed as a handle
// (Hazel.value, converted once), unannotated finder and annotated, per map size: median ms a call, answers checked.
//   node --stack-size=8000 handles551.mjs <hazel-lib.js> <sizes> <out.json>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel; const HANDLES = typeof H.value === "function";
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const rule = find => `fun (g, e) -> case e
  | Way(d) => let (dx, dy) = dir(d) in let c = g.at_col + dx in let r = g.at_row + dy in let back = opp(d) in
    if c < 0 || r < 0 || c >= g.cols || r >= g.rows then Done else decide(${find}(g.cells, c, r), back, c, r)
  | _ => Done end`;
const prog = [base,
  `let findU = fun (cs, c, r) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findU(rest, c, r) end in`,
  `let findA = fun (cs, c, r) : ([Cell], Int, Int) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findA(rest, c, r) end in`,
  `(passedU = (${rule("findU")}), passedA = (${rule("findA")}), ignore = (fun (g, e) -> Done))`].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 800)); process.exit(1); }
const V = r.value;
const q = a => a.slice().sort((x, y) => x - y)[a.length >> 1];
const time = (f, R) => { for (let i = 0; i < 3; i++) f(); const t = []; const t0 = performance.now(); for (let i = 0; i < R; i++) { const a = performance.now(); f(); t.push(performance.now() - a); if (performance.now() - t0 > 2500 && i >= 8) break; } return +q(t).toFixed(3); };
const out = [];
for (const n of process.argv[3].split(",").map(Number)) {
  const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  const ac = Math.floor(n / 2) - 1, ar = Math.floor(n / 2), ev = { tag: "Way", value: "E" };
  const want = JSON.stringify({ tag: "GoSquare", value: [ac + 1, ar, "W", { tag: "Done" }] });
  const g = { at_col: ac, at_row: ar, cols: n, rows: n, cells };
  let t0 = performance.now(); const hc = HANDLES ? H.value(cells) : null; const handle_ms = performance.now() - t0;
  const gh = HANDLES ? { ...g, cells: hc } : null;
  const R = n >= 32 ? 20 : 60;
  const row = { n, cells: n * n, handle_ms: +handle_ms.toFixed(2) };
  for (const [k, f] of [["passedU", () => V.passedU(g, ev)], ["passedA", () => V.passedA(g, ev)], ["ignore", () => V.ignore(g, ev)],
      ...(HANDLES ? [["passedU_h", () => V.passedU(gh, ev)], ["passedA_h", () => V.passedA(gh, ev)], ["ignore_h", () => V.ignore(gh, ev)]] : [])]) {
    if (!k.startsWith("ignore") && JSON.stringify(f()) !== want) { console.error(k, n, JSON.stringify(f()), "wanted", want); process.exit(1); }
    row[k] = time(f, R);
  }
  console.log(JSON.stringify(row)); out.push(row);
}
fs.writeFileSync(process.argv[4], JSON.stringify(out, null, 1));
