// ^report(25): each listing's tile program (data/tiles.json) analyzed and run by Hazel's library, the build the embed frames load,
// so the tiles show the code with no error marks.   node tiles_check.mjs <hazel-lib.js>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const T = JSON.parse(fs.readFileSync(new URL("../data/tiles.json", import.meta.url), "utf8"));
let bad = 0;
for (const [k, text] of Object.entries(T)) {
  const r = globalThis.Hazel.run(text);
  const errs = r.errors || [];
  console.log(k, errs.length ? "ERRORS " + JSON.stringify(errs).slice(0, 400) : "ok, a " + typeof r.value);
  bad += errs.length ? 1 : 0;
}
process.exit(bad ? 1 : 0);
