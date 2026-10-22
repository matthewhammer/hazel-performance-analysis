import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const prog = `type Event = + Way(String) + Nope in
let nthU = fun (cs, i) -> case cs | [] => 0 | x :: rest => if i == 0 then x.col else nthU(rest, i - 1) end in
fun (cells : [(col = Int, row = Int)]) -> fun (n, e) -> nthU(cells, n)`;
const r = H.run(prog); if (r.errors?.length) { console.error(r.errors); process.exit(1);} 
const cells=[]; for(let i=0;i<256;i++) cells.push({col:i%16,row:i>>4});
const f = r.value(cells); f(136,{tag:"Nope"});
const t0=performance.now(); let k=0; while(performance.now()-t0<3000){f(136,{tag:"Nope"});k++;} console.log("calls",k,"ms/call",(3000/k).toFixed(2));
