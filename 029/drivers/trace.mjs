import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const NAMES = "Invalid MultiHole DynamicErrorHole Deferral Atom DrvQuote ListLit Constructor Fun TypFun Tuple Label TupLabel Dot LivelitName Var Let Theorem ProofObject Forall FixF TyAlias Use Ap TypAp DeferredAp If Seq Test HintedTest Filter Closure Parens Projector Cons ListConcat UnOp BinOp BuiltinFun Match TupleExtension Asc Module ModuleExp".split(" ");
const CONST = ["EmptyHole", "Undefined", "ExplicitNonlabel"];
const name = e => { const t = e[1]; if (typeof t === "number") return CONST[t]; const nm = NAMES[t[0]];
  if (nm === "Var") return `Var(${t[1]})`; if (nm === "Atom") return `Atom`; if (nm === "ListLit") { let k = 0, l = t[1]; while (l && l !== 0) { k++; l = l[2]; } return `ListLit[${k}]`; }
  if (nm === "Closure" || nm === "Asc" || nm === "Let") return `${nm}(${name(t[2] && nm === "Closure" ? t[2] : t[1])})`; return nm; };
const r = H.run(`let build = fun (n, acc) -> if n == 0 then acc else build(n - 1, n :: acc) in
let mk = fun held -> (h_ref = (fun k -> let u = held in k)) in (go = fun n -> mk(build(n, [])))`);
if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 400)); process.exit(1); }
const h = r.value.go(4); h.h_ref(7);
globalThis.__T = []; h.h_ref(7); const T = globalThis.__T; globalThis.__T = null;
let depth = 0;
for (const [io, e, fin, kind] of T) {
  if (io === "in") { console.log("  ".repeat(depth) + "> " + name(e)); depth++; }
  else { depth--; console.log("  ".repeat(depth) + "< " + name(e) + (fin === 0 ? " Final" : " Uneval") + (kind === 0 ? " (no step)" : "")); }
}
