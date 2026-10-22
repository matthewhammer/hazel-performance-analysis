import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
const KCG="/home/matthew/kcg-531/dress-up/js/";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const page = { console, Math, JSON, Array, Object, String, Number, Boolean, Map, Set, Promise, RegExp, Error, Symbol, location: { search: "?logic=hazel" },
  setTimeout: () => 0, clearTimeout() {}, performance, document: { head: { append() {} }, getElementById: () => null, body: { classList: { contains: () => false } } }, addEventListener() {},
  state: { scripts: { on: false, common: null, rooms: {} }, background: {} } };
page.window = page; page.Hazel = H; vm.createContext(page);
vm.runInContext(fs.readFileSync(KCG+"25-scripting.js","utf8").replace("let find = fun (cs, c, r) : ([Cell], Int, Int) ->","let find = fun (cs, c, r) ->"), page);
const C = vm.runInContext("scriptCompile()", page); const none = vm.runInContext("scriptNoGlobals()", page);
const W = C.handlers.World;
const cells = n => { const out=[]; for (let r=0;r<n;r++) for (let c=0;c<n;c++) out.push({col:c,row:r,kind:"grass",ways:["N","E","S","W"]}); return out; };
const q=(a,p)=>a.slice().sort((x,y)=>x-y)[Math.floor(p*a.length)];
const T=(k,f,R=60)=>{for(let i=0;i<5;i++)f(); const t=[];for(let i=0;i<R;i++){const t0=performance.now();f();t.push(performance.now()-t0);} console.log(k.padEnd(52),"p50",q(t,.5).toFixed(2));};
const mode = process.argv[3]||"time";
const c16=cells(16), c8=cells(8), c3=cells(3);
if (mode==="prof2") { const t0=performance.now(); while(performance.now()-t0<3000) W({...none,cols:16,rows:16,cells:c16},{tag:"Nope"}); process.exit(0); }
if (mode==="prof") { const t0=performance.now(); while(performance.now()-t0<3000) W({...none,at_col:14,at_row:15,cols:16,rows:16,cells:c16},{tag:"Way",value:"E"}); process.exit(0); }
console.log("globals keys", Object.keys(none).length);
for (const [n,cs] of [[3,c3],[8,c8],[16,c16]]) {
  T(`${n}x${n}: target index 1 (E of 0,0)`, ()=>W({...none,at_col:0,at_row:0,cols:n,rows:n,cells:cs},{tag:"Way",value:"E"}));
  T(`${n}x${n}: target last (E of n-2,n-1)`, ()=>W({...none,at_col:n-2,at_row:n-1,cols:n,rows:n,cells:cs},{tag:"Way",value:"E"}));
  T(`${n}x${n}: off map (W of 0,0, no find)`, ()=>W({...none,at_col:0,at_row:0,cols:n,rows:n,cells:cs},{tag:"Way",value:"W"}));
  T(`${n}x${n}: Other event (case _ => Done)`, ()=>W({...none,at_col:0,at_row:0,cols:n,rows:n,cells:cs},{tag:"Nope"}));
}
T(`16x16 cells, ways [] (fewer nodes)`, ()=>W({...none,cols:16,rows:16,cells:c16.map(x=>({...x,ways:[]}))},{tag:"Nope"}));
T(`no cells, Other event`, ()=>W({...none},{tag:"Nope"}));
T(`1024 ints in an unused field? (cells=[0..])`, ()=>W({...none,cells:Array.from({length:1024},(_,i)=>i)},{tag:"Nope"}));
