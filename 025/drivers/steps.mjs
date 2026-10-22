import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const mk = p => { const r = H.run(p); if (r.errors?.length) throw r.errors; return r.value; };
const walk = mk(`let nthU = fun (cs, i) -> case cs | [] => 0 | x :: rest => if i == 0 then x.col else nthU(rest, i - 1) end in
fun (cells : [(col = Int, row = Int)]) -> fun i -> nthU(cells, i)`);
const count = mk(`let cnt = fun i -> if i == 0 then 0 else cnt(i - 1) in fun i -> cnt(i)`);
const q=(a)=>a.sort((x,y)=>x-y)[a.length>>1];
const T=(f)=>{for(let i=0;i<3;i++)f();const t=[];for(let i=0;i<25;i++){const t0=performance.now();f();t.push(performance.now()-t0);}return +q(t).toFixed(3);};
const res={};
for (const L of [64,256,1024]) { const cs=[];for(let i=0;i<L;i++)cs.push({col:i,row:0}); const f=walk(cs);
  for (const i of [0,32,64,128]) if(i<L) res[`walk L=${L} i=${i}`]=T(()=>f(i)); }
for (const i of [0,32,64,128,256]) res[`countdown i=${i}`]=T(()=>count(i));
console.log(JSON.stringify(res,null,1)); fs.writeFileSync("data_steps.json",JSON.stringify(res,null,1));
