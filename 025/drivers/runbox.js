/* ^report(25)'s run boxes: each listing's program run by Hazel's JS library (hazel-lib.js, window.Hazel, the hazel.org build of
   #2719 that the tiles use, loaded on the first Run) on an example map and move, as drivers/r25.mjs calls it; the value Hazel gives
   back, written in Hazel's notation, and the call's time in this browser. Shared with drivers/runbox_check.mjs (node). */
const RUNBOX = (() => {
  // the World room's Globals for an n x n map of grass, every square with all four ways, the player mid-map (r25.mjs's globalsOf)
  const globalsOf = n => {
    const cells = [];
    for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) cells.push({ col, row, kind: "grass", ways: ["N", "E", "S", "W"] });
    return { lever_L: false, lever_R: false, wiring: "", draws: [], pits_on: [], covered: [], hatch: false, things: [], rooms: [], exits: [],
      out: "", out_room: 0, at_col: Math.floor(n / 2) - 1, at_row: Math.floor(n / 2), cols: n, rows: n, cells };
  };
  const ev = { tag: "Way", value: "E" };
  // how each listing is called (r25.mjs): the map's Globals, or four numbers to a closure holding the map, or the neighbours only
  const calls = {
    held: (f, g) => { const t0 = performance.now(); const hf = f(g.cells); const setup = performance.now() - t0;
      return { setup, call: () => hf({ at_col: g.at_col, at_row: g.at_row, cols: g.cols, rows: g.rows }, ev),
               input: `held(cells), then ({at_col: ${g.at_col}, at_row: ${g.at_row}, cols: ${g.cols}, rows: ${g.rows}}, Way("E"))` }; },
    near: (f, g) => { const near = g.cells.filter(x => Math.abs(x.col - g.at_col) <= 1 && Math.abs(x.row - g.at_row) <= 1);
      return { call: () => f({ at_col: g.at_col, at_row: g.at_row, cols: g.cols, rows: g.rows, near }, ev),
               input: `({at_col: ${g.at_col}, at_row: ${g.at_row}, cols: ${g.cols}, rows: ${g.rows}, near: ${near.length} cells}, Way("E"))` }; },
  };
  const plain = (f, g) => ({ call: () => f(g, ev), input: `(Globals with ${g.cells.length} cells, at (${g.at_col}, ${g.at_row}), Way("E"))` });
  // a value as Hazel writes it: constructors as C(args), tuples in parentheses, strings quoted
  const show = v => v === null || v === undefined ? "()" : typeof v === "string" ? JSON.stringify(v)
    : Array.isArray(v) ? "(" + v.map(show).join(", ") + ")"
    : typeof v === "object" && "tag" in v ? v.tag + ("value" in v ? (Array.isArray(v.value) ? show(v.value) : "(" + show(v.value) + ")") : "")
    : typeof v === "object" ? "(" + Object.entries(v).map(([k, x]) => k + " = " + show(x)).join(", ") + ")" : String(v);
  const compiled = {};
  // run listing k's program (text) on an n x n map: { output, input, ms, setup?, compileMs? } or { error }
  function run(H, k, text, n) {
    let compileMs;
    if (!compiled[k]) {
      const t0 = performance.now(); const r = H.run(text); compileMs = performance.now() - t0;
      if (r.errors && r.errors.length) return { error: "Hazel says: " + JSON.stringify(r.errors).slice(0, 300) };
      compiled[k] = r.value;
    }
    const g = globalsOf(n), c = (calls[k] || plain)(compiled[k], g);
    c.call();   // a first call, warming up
    const ts = [];
    for (let i = 0; i < 5; i++) { const t0 = performance.now(); var out = c.call(); ts.push(performance.now() - t0); }
    ts.sort((a, b) => a - b);
    return { output: show(out), input: c.input, ms: ts[2], setup: c.setup, compileMs };
  }
  return { run, show, globalsOf };
})();
if (typeof module !== "undefined") module.exports = RUNBOX;
