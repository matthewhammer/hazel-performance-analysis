// ^ticket(545): a CPU profile of only the calls (not the set-up) of one kernel, on the dev build (names kept):
//   node --stack-size=8000 prof_ref.mjs <hazelLib.bc.js> <kernel> <n> <calls> <out.cpuprofile>
// kernel: h_ref, h_walk, h_id (a list of n held, each call uses it), or count, fib, sumbuild, mapinc (each call is k(n)).
import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module"; import path from "node:path";
import { Session } from "node:inspector/promises";
const HERE = path.dirname(new URL(import.meta.url).pathname);
const [lib, k, nArg, callsArg, out] = process.argv.slice(2);
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(lib, "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const r = H.run(fs.readFileSync(path.join(HERE, "kernels.hz"), "utf8"));
if (r.errors && r.errors.length) { console.error(JSON.stringify(r.errors).slice(0, 600)); process.exit(1); }
const n = +nArg, calls = +callsArg;
let call;
if (k.startsWith("h_")) { const h = r.value.hold(n); call = () => h[k](7); } else call = () => r.value[k](n);
for (let i = 0; i < 3; i++) call();
const s = new Session(); s.connect();
await s.post("Profiler.enable"); await s.post("Profiler.setSamplingInterval", { interval: 200 }); await s.post("Profiler.start");
const t0 = performance.now(); for (let i = 0; i < calls; i++) call(); const ms = (performance.now() - t0) / calls;
const { profile } = await s.post("Profiler.stop");
fs.writeFileSync(out, JSON.stringify(profile));
console.log(k, n, "ms a call", ms.toFixed(3));
