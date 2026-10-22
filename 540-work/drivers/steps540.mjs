// ^ticket(540): evaluator steps by kind for one call of each probe (trial/r25-stats's Hazel.stepCounts()), at a few sizes: which
// kinds grow with the held value. node --stack-size=8000 steps540.mjs <hazel-lib.js> <sizes>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
const HERE = path.dirname(new URL(import.meta.url).pathname);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel; if (typeof H.stepCounts !== "function") { console.error("no Hazel.stepCounts in this build"); process.exit(1); }
const T = JSON.parse(fs.readFileSync(path.join(HERE, "../../025/data/tiles.json"), "utf8"));
const held = T.held.split("\n"); const base = held.slice(0, held.lastIndexOf("let held = fun (cells : [Cell]) ->")).join("\n");
const probes = `(
  ignore = (fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> Done),
  uses = (fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> let u = t in Done),
  lookup = (fun (cells, w) -> let (t, _) = build(cells, length(cells), w) in fun (n, e) -> case lookup(t, 3) | Some(_) => Done | None => Done end),
  held_tree = held_tree
)`;
const prog = [base, fs.readFileSync(path.join(HERE, "tree.hz"), "utf8"), probes].join("\n");
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 800)); process.exit(1); }
const out = {};
for (const n of process.argv[3].split(",").map(Number)) {
  const cells = []; for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
  const sm = { at_col: n / 2 - 1, at_row: n / 2, cols: n, rows: n }, ev = { tag: "Way", value: "E" };
  for (const k of ["ignore", "uses", "lookup", "held_tree"]) {
    const f = r.value[k](cells, n); f(sm, ev); H.stepCounts();
    f(sm, ev); const c = H.stepCounts();
    out[`${k} ${n}x${n}`] = c;
    console.log(k, `${n}x${n}`, JSON.stringify(Object.fromEntries(Object.entries(c).sort((a, b) => b[1] - a[1]))));
  }
}
fs.writeFileSync("steps540.json", JSON.stringify(out, null, 1));
