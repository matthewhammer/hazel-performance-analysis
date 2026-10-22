import fs from "node:fs"; import vm from "node:vm"; import { createRequire } from "node:module";
const KCG="/home/matthew/kcg-531/dress-up/js/";
globalThis.require = createRequire(import.meta.url);
vm.runInThisContext(fs.readFileSync(process.argv[2], "utf8"), { filename: "hazel-lib.js" });
const H = globalThis.Hazel;
const page = { console, Math, JSON, Array, Object, String, Number, Boolean, Map, Set, Promise, RegExp, Error, Symbol, location: { search: "?logic=hazel" },
  setTimeout: () => 0, clearTimeout() {}, performance, document: { head: { append() {} }, getElementById: () => null, body: { classList: { contains: () => false } } }, addEventListener() {},
  state: { scripts: { on: false, common: null, rooms: {} }, background: {} } };
page.window = page; page.Hazel = H; vm.createContext(page);
vm.runInContext(fs.readFileSync(KCG+"25-scripting.js","utf8")+";globalThis.__S={SCRIPT_PREAMBLE,SCRIPT_COMMON,SCRIPT_WORLD};", page);
const S = page.__S;
const none = vm.runInContext("scriptNoGlobals()", page);
const BODY = `
let no_way = fun (kind, d) : (String, String) -> kind == "waterfall" && d == "N" in
let dir = fun d : String -> if d == "N" then (0, 0 - 1) else if d == "NE" then (1, 0 - 1) else if d == "E" then (1, 0) else if d == "SE" then (1, 1) else if d == "S" then (0, 1) else if d == "SW" then (0 - 1, 1) else if d == "W" then (0 - 1, 0) else if d == "NW" then (0 - 1, 0 - 1) else (0, 0) in
let opp = fun d : String -> if d == "N" then "S" else if d == "NE" then "SW" else if d == "E" then "W" else if d == "SE" then "NW" else if d == "S" then "N" else if d == "SW" then "NE" else if d == "W" then "E" else if d == "NW" then "SE" else "" in
let member = fun (s, xs) : (String, [String]) -> case xs | [] => false | x :: rest => x == s || member(s, rest) end in
let findA = fun (cs, c, r) : ([Cell], Int, Int) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findA(rest, c, r) end in
let findU = fun (cs, c, r) -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else findU(rest, c, r) end in
let nthU = fun (cs, i) -> case cs | [] => None | x :: rest => if i == 0 then Some(x) else nthU(rest, i - 1) end in
let decide = fun (x, back, c, r) -> case x | Some(x) => if member(back, x.ways) && !no_way(x.kind, back) then GoSquare(c, r, back, Done) else Done | None => Done end in
let mk = fun look -> fun (g, e) : (Globals, Event) -> case e
  | Way(d) => let (dx, dy) = dir(d) in let c = g.at_col + dx in let r = g.at_row + dy in let back = opp(d) in
    if c < 0 || r < 0 || c >= g.cols || r >= g.rows then Done else decide(look(g.cells, c, r, g.cols), back, c, r)
  | _ => Done end in
let near = fun (n, e) -> case e
  | Way(d) => let (dx, dy) = dir(d) in let c = n.at_col + dx in let r = n.at_row + dy in let back = opp(d) in
    if c < 0 || r < 0 || c >= n.cols || r >= n.rows then Done else decide(findU(n.near, c, r), back, c, r)
  | _ => Done end in
let held = fun (cells : [Cell]) -> fun (n, e) -> case e
  | Way(d) => let (dx, dy) = dir(d) in let c = n.at_col + dx in let r = n.at_row + dy in let back = opp(d) in
    if c < 0 || r < 0 || c >= n.cols || r >= n.rows then Done else decide(nthU(cells, r * n.cols + c), back, c, r)
  | _ => Done end in
(shipped = mk(fun (cs, c, r, w) -> findA(cs, c, r)),
 noann = mk(fun (cs, c, r, w) -> findU(cs, c, r)),
 index = mk(fun (cs, c, r, w) -> nthU(cs, r * w + c)),
 idA = fun (g, e) : (Globals, Event) -> Done,
 idU = fun (g, e) -> Done,
 near = near, held = held)`;
const prog = [S.SCRIPT_PREAMBLE, BODY].join("\n");
const tRun = performance.now();
const r = H.run(prog); if (r.errors && r.errors.length) { console.error(r.errors); process.exit(1); }
const run_ms = +(performance.now() - tRun).toFixed(1);
const V = r.value;
// real World rule via game compile
const tCompile = performance.now();
const W = vm.runInContext("scriptCompile()", page).handlers.World;
const compile_ms = +(performance.now() - tCompile).toFixed(1);
// both are first calls in a fresh process: one sample each, so read them across runs
fs.writeFileSync(`compile_${process.argv[4]||"run"}.json`, JSON.stringify({ run_ms, compile_ms }));
console.log(JSON.stringify({ run_ms, compile_ms }));
const q=(a,p)=>a.slice().sort((x,y)=>x-y)[Math.floor(p*a.length)];
const T=(f,R)=>{for(let i=0;i<3;i++)f(); const t=[];const t00=performance.now();for(let i=0;i<R;i++){const t0=performance.now();f();t.push(performance.now()-t0); if(performance.now()-t00>2500&&i>=8)break;} return +q(t,.5).toFixed(3);};
// map like W.cells: {"c,r": {kind, ways}}
const mapOf = n => { const o={}; for (let r=0;r<n;r++) for (let c=0;c<n;c++) o[c+","+r]={kind:"grass",ways:["N","E","S","W"]}; return o; };
const globalsOf = (m, n, ac, ar) => ({...none, at_col:ac, at_row:ar, cols:n, rows:n,
  cells: Object.entries(m).map(([k,v])=>{const [col,row]=k.split(",").map(Number); return {col,row,kind:v.kind,ways:v.ways};}).sort((a,b)=>a.row-b.row||a.col-b.col)});
const ev = {tag:"Way", value:"E"};
const sizes = (process.argv[3]||"3,4,6,8,12,16,24").split(",").map(Number);
const out = [];
for (const n of sizes) {
  const m = mapOf(n); const ac = Math.floor(n/2)-1, ar = Math.floor(n/2); // target mid-map, like a typical move
  const g = globalsOf(m, n, ac, ar);
  const R = n>=16?20:60;
  const res = { n, cells:n*n, target_index: ar*n+ac+1 };
  res.js_globals = T(()=>globalsOf(m,n,ac,ar), 200);
  res.idU = T(()=>V.idU(g, ev), R);           // of_js + re-step of arg
  res.idA = T(()=>V.idA(g, ev), R);           // + parameter ascription
  res.game_World = T(()=>W(g, ev), R);        // shipped rule via game (globals prebuilt)
  res.shipped = T(()=>V.shipped(g, ev), R);
  res.noann = T(()=>V.noann(g, ev), R);
  res.index = T(()=>V.index(g, ev), R);
  const nb = {at_col:ac, at_row:ar, cols:n, rows:n, near: g.cells.filter(x=>Math.abs(x.col-ac)<=1&&Math.abs(x.row-ar)<=1)};
  res.near = T(()=>V.near(nb, ev), 200);
  const tH=performance.now(); const hf = V.held(g.cells); res.held_setup = +(performance.now()-tH).toFixed(2);
  const sm = {at_col:ac, at_row:ar, cols:n, rows:n};
  res.held = T(()=>hf(sm, ev), R);
  res.held_ok = JSON.stringify(hf(sm,ev)) === JSON.stringify(W(g,ev));
  res.near_ok = JSON.stringify(V.near(nb,ev)) === JSON.stringify(W(g,ev));
  res.result = W(g,ev);
  // plain JS
  const js = (gg,e)=>{const d={N:[0,-1],E:[1,0],S:[0,1],W:[-1,0]}[e.value]; const c=gg.at_col+d[0], r=gg.at_row+d[1]; const x=m[c+","+r]; return x&&x.ways.includes("W")?"Go":"Done";};
  res.js_rule = T(()=>js(g,ev), 2000);
  console.log(JSON.stringify(res)); out.push(res);
}
fs.writeFileSync(`data_${process.argv[4]||"run"}.json`, JSON.stringify(out,null,1));
