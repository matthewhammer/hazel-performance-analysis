# A copy of the dev build that logs every evaluator pass: the term on the way in, and on the way out whether it is final
# and the step it took (globalThis.__T, when set). For trace.mjs. python3 patch_trace.py <hazelLib.bc.js> <out.js>
import sys
src, dst = sys.argv[1:3]; s = open(src, encoding="utf-8").read()
a = "    function eval_1_effects\n    (reuse_map, in_closure, call_stack, delegations, state, env, exp){\n"
assert s.count(a) == 1
s = s.replace(a, a + "     if (globalThis.__T) globalThis.__T.push(['in', exp]);\n")
b = "               var\n                next =\n                   /*<<src/language/dynamics/Evaluator.re:205:4>>*/ param[4],\n"
assert s.count(b) == 1
s = s.replace(b, "               if (globalThis.__T) globalThis.__T.push(['out', exp, param[1], param[3]]);\n" + b)
open(dst, "w", encoding="utf-8").write(s); print("patched")
