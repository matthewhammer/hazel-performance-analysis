import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const prog = `let build = fun (n, acc) -> if n == 0 then acc else build(n - 1, n :: acc) in
let nest = fun (n, acc) -> if n == 0 then acc else nest(n - 1, [n, n] :: acc) in
let pairs = fun (n, acc) -> if n == 0 then acc else pairs(n - 1, (n, n) :: acc) in
let mk = fun held -> (once = (fun k -> let u = held in k), twice = (fun k -> let u = held in let w = held in k),
  in_tuple = (fun k -> let t = (held, 1) in k), via_fun = (fun k -> let g = (fun z -> held) in k), call_g = (fun k -> let g = (fun z -> held) in let u = g(0) in k)) in
(flat = fun n -> mk(build(n, [])), nested = fun n -> mk(nest(n, [])), tuples = fun n -> mk(pairs(n, [])),
 wrapped = fun n -> mk((xs = build(n, []), tag = 1)))`;
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
for (const how of ["flat", "nested", "tuples", "wrapped"]) {
  const h = r.value[how](1000); const row = [];
  for (const k of ["once", "twice", "in_tuple", "via_fun", "call_g"]) { h[k](7); H.stepCounts(); h[k](7); const c = H.stepCounts(); row.push(`${k} ${c.evaluate}`); }
  console.log(how.padEnd(8), row.join("  "));
}
