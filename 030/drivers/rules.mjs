// ^report(30): the game's rules three ways, as kids-choice-games' script-boxes-566 has them (^ticket(566)): each room's Hazel and
// Fumola text, 📚 Common's in both, Hazel's preamble (the sum types), and each room's own JS (the functions 25-scripting.js's
// SCRIPT_JS names, their text from the game's parts; a [name, from, to] entry the lines between). Written to 030/data/rules.json.
//   node 030/drivers/rules.mjs <kids-choice-games checkout>
import fs from "node:fs"; import vm from "node:vm"; import path from "node:path"; import { execSync } from "node:child_process";
const kcg = process.argv[2], js = path.join(kcg, "dress-up", "js");
const page = { console, Math, JSON, Array, Object, String, Number, Boolean, Map, Set, Promise, RegExp, Error, Symbol, location: { search: "" },
  setTimeout: () => 0, clearTimeout() {}, performance, document: { head: { append() {} }, getElementById: () => null, body: { classList: { contains: () => false } } },
  addEventListener() {}, state: { scripts: { on: false, common: null, rooms: {} }, background: {} } };
page.window = page; vm.createContext(page);
vm.runInContext(fs.readFileSync(path.join(js, "25-scripting.js"), "utf8"), page);
vm.runInContext(fs.readFileSync(path.join(js, "25-fumola.js"), "utf8"), page);
const R = vm.runInContext(`({ rooms: SCRIPT_ROOMS, preamble: SCRIPT_PREAMBLE, common: SCRIPT_COMMON, hazel: SCRIPT_TEXTS, fcommon: FUMOLA_COMMON, fumola: FUMOLA_ROOM_TEXTS, jsSpec: SCRIPT_JS })`, page);
const all = fs.readdirSync(js).filter(f => f.endsWith(".js")).sort().map(f => [f, fs.readFileSync(path.join(js, f), "utf8")]);
const fnText = name => { for (const [f, t] of all) { const a = t.indexOf(`\nfunction ${name}(`); if (a < 0) continue;
  const rest = t.slice(a + 1), m = rest.search(/\n\}\n/); return { file: f, text: rest.slice(0, m + 2) }; } return { file: null, text: `// ${name}: not found` }; };
const jsOf = room => (R.jsSpec[room] || []).map(spec => { const [name, from, to] = Array.isArray(spec) ? spec : [spec];
  const { file, text } = fnText(name); if (!from) return { name, file, text };
  const ls = text.split("\n"), a = ls.findIndex(l => l.includes(from)), b = ls.findIndex((l, i) => i >= a && l.includes(to));
  return { name, file, text: `// in ${name}(), the lines that decide it:\n` + ls.slice(a, b + 1).map(l => l.replace(/^ {2}/, "")).join("\n") }; });
const commit = execSync("git rev-parse --short=10 HEAD", { cwd: kcg }).toString().trim();
const out = { source: `matthewhammer/kids-choice-games, branch script-boxes-566 at ${commit}`, commit,
  preamble: R.preamble, common: { hazel: R.common, fumola: R.fcommon },
  rooms: R.rooms.map(r => ({ name: r.name, label: r.label, hazel: R.hazel[r.kind], fumola: R.fumola[r.name], js: jsOf(r.name) })) };
fs.writeFileSync(path.join(path.dirname(new URL(import.meta.url).pathname), "..", "data", "rules.json"), JSON.stringify(out, null, 1));
console.log(out.source, out.rooms.map(r => `${r.name}: js ${r.js.map(j => j.name + (j.file ? "" : "?")).join("+")}`).join("; "));
