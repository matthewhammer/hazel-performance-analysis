// ^report(25): the run boxes' logic (runbox.js) in node, on each listing's program (data/tiles.json), at 3x3 and 8x8
//   node runbox_check.mjs <hazel-lib.js>
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
const require = createRequire(import.meta.url); globalThis.require = require;
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const R = require("./runbox.js");
const T = JSON.parse(fs.readFileSync(new URL("../data/tiles.json", import.meta.url), "utf8"));
for (const [k, text] of Object.entries(T)) for (const n of [3, 8]) {
  const r = R.run(globalThis.Hazel, k, text, n);
  console.log(k, n + "x" + n, r.error || `${r.output}  (${r.ms.toFixed(2)} ms; input ${r.input})`);
}
