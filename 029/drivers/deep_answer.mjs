// ^ticket(549): one deep answer in a fresh process (a trap leaves the wasm instance unusable), by the path it takes out:
//   list (an option list, structural JSON), arrays (nested arrays, structural JSON), printer (a function holding the list:
//   format_one_line), held (the list held, the answer 0). node deep_answer.mjs <case> <n>
import fs from "node:fs";
const dir = "/home/matthew/kcg-542/dress-up/vendor/fumola/2ec634b5df";
const F = await import(dir + "/fumola_wasm.js");
F.initSync({ module: fs.readFileSync(dir + "/fumola_wasm_bg.wasm") });
const DEF = "func build(n, acc) { if (n == 0) { acc } else { build(n - 1, ?(n, acc)) } }; func nest(n, acc) { if (n == 0) { acc } else { nest(n - 1, [acc]) } }; 0";
const [c, n] = [process.argv[2], +process.argv[3]];
const mk = { list: `build(${n}, null)`, arrays: `nest(${n}, [])`, printer: `let held = build(${n}, null); func f(k) { held }`, held: `let held = build(${n}, null); 0` }[c];
const id = F.fumola_create(); F.fumola_eval_top(id, DEF);
try { const s = F.fumola_eval_top(id, mk); const r = JSON.parse(s); console.log(r.ok ? `ok ${r.tag} ${s.length}` : `error ${String(r.error).slice(0, 70)}`); }
catch (e) { console.log("CRASH " + String(e).split("\n")[0].slice(0, 60)); }
