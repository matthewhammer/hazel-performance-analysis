#!/usr/bin/env python3
"""Writes 029/index.html, ^report(29): where the Hazel/Fumola gap comes from, on the same small programs (^ticket(545)).
Data: data/{fumola_wasm,hazel_best,hazel_stats}_laptop_*.json (drivers/kernels.mjs), data/prof_*.json (drivers/prof_ref.mjs,
profiles.py, on a dev build with names), and data/gh/ (Adapton/fumola branch bench/545-contrast: Fumola native and wasm and
Hazel, on one GitHub runner), when it is there."""
import os, json, glob, math, html, re
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE)
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
esc = html.escape

def load(pat):
    """rows of every round matching pat, as {(kernel, n): row} with ms the mean of the rounds' medians"""
    fs = sorted(glob.glob(os.path.join(R, "data", pat)))
    if not fs: return {}, 0
    acc = {}
    for f in fs:
        for r in json.load(open(f)): acc.setdefault((r["k"], r["n"]), []).append(r)
    out = {}
    for key, rs in acc.items():
        row = dict(rs[0]); row["ms"] = sum(r["ms"] for r in rs) / len(rs); row["rounds"] = len(rs); out[key] = row
    return out, len(fs)
FL, _ = load("fumola_wasm_laptop_*.json")
HL, hl_rounds = load("hazel_best_laptop_*.json")
SL, _ = load("hazel_stats_laptop_*.json")
GN, gh_rounds = load("gh/fumola_native_*.json")
GW, _ = load("gh/fumola_wasm_*.json")
GH, _ = load("gh/hazel_best_*.json")
HAVE_GH = bool(GN and GW and GH)
LSCPU = open(os.path.join(R, "data", "gh", "lscpu.txt")).read() if os.path.exists(os.path.join(R, "data", "gh", "lscpu.txt")) else ""
CPU = (re.search(r"Model name:\s*(.+)", LSCPU) or [None, "GitHub's runner"])[1].strip() if LSCPU else "GitHub's runner"
PROF = {k: json.load(open(os.path.join(R, "data", f"prof_{k}.json"))) for k in ("count_5000", "sumbuild_1000", "h_ref_3000")}

KERNELS = [  # (name, what it does, sizes)
 ("count", "a loop: <code>count(n)</code> counts down to zero", [100, 1000, 5000]),
 ("fib", "calls: <code>fib(n)</code>, doubly recursive", [10, 13, 16]),
 ("sumbuild", "a list built by an accumulator, then summed", [100, 1000, 3000]),
 ("mapinc", "a list built, a closure mapped over it, its length", [100, 1000, 3000]),
 ("h_ref", "a held list of n, referred to once: <code>let u = held in k</code>", [100, 1000, 3000]),
 ("h_walk", "a held list of n, walked: <code>len(held)</code>", [100, 1000, 3000]),
 ("h_id", "a held list of n, not touched: <code>k</code>", [100, 1000, 3000]),
 ("skip", "a list of n passed in from JS and ignored: the boundary", [100, 1000, 3000]),
]
fmt = lambda v: "–" if v is None else (f"{v:.2g}" if v < 0.1 else f"{v:.3g}" if v < 100 else f"{v:,.0f}")
x = lambda a, b: f"{a / b:.0f}x" if a / b >= 10 else f"{a / b:.1f}x"
def kinds(k, n):
    """Hazel's evaluator passes for one call, split: all passes, those that took a step, and those that found a final term"""
    c = SL[(k, n)]["by_kind"]; ev = c.get("evaluate", 0); nostep = c.get("no step", 0)
    return ev, ev - nostep, nostep

# ---------- Figure 1: one small log-log panel per kernel
SER = [("hazel", "Hazel (js), best build", "var(--bad)", ""), ("wasm", "Fumola (wasm)", "var(--accent)", "6 4"), ("native", "Fumola (native)", "var(--accent2)", "2 3")]
def panel(k, title, sizes, data, w=250, h=178):
    L, Rr, T, B = 44, 10, 22, 30
    pts = {s: [(n, data[s][(k, n)]["ms"]) for n in sizes if (k, n) in data.get(s, {})] for s, *_ in SER}
    vals = [v for p in pts.values() for _, v in p]
    lo, hi = math.floor(math.log10(min(vals))), math.ceil(math.log10(max(vals)))
    if hi - lo < 2: hi = lo + 2
    x0, x1 = math.log10(sizes[0]), math.log10(sizes[-1])
    X = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (w - L - Rr)
    Y = lambda v: h - B - (math.log10(v) - lo) / (hi - lo) * (h - T - B)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}: ms per call against n, log scales" style="width:100%;height:auto;font:12px system-ui,sans-serif">',
         f'<text x="{L}" y="13" style="fill:var(--ink);font-weight:600">{esc(k)}</text>']
    for e in range(lo, hi + 1):
        v = 10 ** e; lab = f"{v:g}" if v >= 0.01 else f"{v:.0e}"
        o.append(f'<line x1="{L}" x2="{w-Rr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" style="stroke:var(--line)"/><text x="{L-5}" y="{Y(v)+4:.1f}" text-anchor="end" style="fill:var(--muted)">{lab}</text>')
    for n in sizes: o.append(f'<text x="{X(n):.1f}" y="{h-B+14}" text-anchor="middle" style="fill:var(--muted)">{n:,}</text>')
    o.append(f'<text x="{(L+w-Rr)/2:.0f}" y="{h-3}" text-anchor="middle" style="fill:var(--muted)">n</text>')
    for s, name, col, dash in SER:
        p = pts[s]
        if not p: continue
        o.append(f'<polyline points="{" ".join(f"{X(n):.1f},{Y(v):.1f}" for n, v in p)}" fill="none" style="stroke:{col}" stroke-width="2"{f" stroke-dasharray=\"{dash}\"" if dash else ""}/>')
        for n, v in p: o.append(f'<circle cx="{X(n):.1f}" cy="{Y(v):.1f}" r="2.4" style="fill:{col}"><title>{esc(name)}, n = {n:,}: {fmt(v)} ms</title></circle>')
    o.append("</svg>"); return "".join(o)
FIG_DATA = {"hazel": GH, "wasm": GW, "native": GN} if HAVE_GH else {"hazel": HL, "wasm": FL}
panels = "".join(f'<div class="panel">{panel(k, t, s, FIG_DATA)}<p>{t}</p></div>' for k, t, s in KERNELS)
legend = "".join(f'<span class="key"><svg width="26" height="10"><line x1="1" x2="25" y1="5" y2="5" style="stroke:{c}" stroke-width="2.4"{f" stroke-dasharray=\"{d}\"" if d else ""}/></svg>{esc(nm)}</span>'
                 for s, nm, c, d in SER if FIG_DATA.get(s))

# ---------- Table 1: steps and the cost of each, laptop, largest size
def t1row(k, n):
    h, f = HL[(k, n)], FL[(k, n)]; ev, st, ns = kinds(k, n)
    return (f"<tr><td><code>{k}</code></td><td class=n>{n:,}</td><td class=n>{fmt(h['ms'])}</td><td class=n>{fmt(f['ms'])}</td><td class=n><b>{x(h['ms'], f['ms']) if h['ms'] >= f['ms'] else '1/' + x(f['ms'], h['ms'])}</b></td>"
            f"<td class=n>{ev:,}</td><td class=n>{st:,}</td><td class=n>{f['steps']:,}</td><td class=n>{1000 * h['ms'] / ev:.2f}</td><td class=n>{1000 * f['ms'] / f['steps']:.3f}</td></tr>")
T1 = "".join(t1row(k, n) for k, _, s in KERNELS for n in s)
ev_c, st_c, _ = kinds("count", 1000); f_c = FL[("count", 1000)]
ev_f, st_f, _ = kinds("fib", 16); f_f = FL[("fib", 16)]
us_hc, us_fc = 1000 * HL[("count", 5000)]["ms"] / kinds("count", 5000)[0], 1000 * FL[("count", 5000)]["ms"] / FL[("count", 5000)]["steps"]

# ---------- Figure 2: where a Hazel call's time goes (three call-only profiles)
GCOL = {"garbage collection": "var(--muted)", "the evaluator's stages": "var(--bad)", "trampolines": "var(--warn)", "the step's rule": "var(--good)",
        "fresh ids": "var(--accent)", "pushing types through values": "var(--accent2)", "environments": "#8a7d5c", "terms and their ids": "#b07aa1", "everything else": "var(--cx)"}
gcol = lambda g: next((c for k, c in GCOL.items() if g.startswith(k)), "var(--cx)")
def fig_profiles(w=760):
    rows = [("count_5000", "count(5000), a loop"), ("sumbuild_1000", "sumbuild(1000), a list built and summed"), ("h_ref_3000", "h_ref, one reference to a held list of 3,000")]
    L, bar, gap, top = 250, 26, 18, 8; h = top + len(rows) * (bar + gap) + 8
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Where a Hazel call spends its time, three profiles, as shares of one bar each" style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for i, (key, label) in enumerate(rows):
        y = top + i * (bar + gap); x0 = L
        o.append(f'<text x="{L-8}" y="{y+bar/2+4:.0f}" text-anchor="end" style="fill:var(--ink)">{esc(label)}</text>')
        for g in PROF[key]["groups"]:
            ww = g["share"] * (w - L - 4)
            if ww < 0.5: continue
            o.append(f'<rect x="{x0:.1f}" y="{y}" width="{ww:.1f}" height="{bar}" style="fill:{gcol(g["group"])}"><title>{esc(g["group"])}: {100*g["share"]:.0f}%</title></rect>')
            if ww > 34: o.append(f'<text x="{x0+ww/2:.1f}" y="{y+bar/2+4:.0f}" text-anchor="middle" style="fill:var(--bg);font-weight:600">{100*g["share"]:.0f}%</text>')
            x0 += ww
    o.append("</svg>"); return "".join(o)
seen = []
for p in PROF.values():
    for g in p["groups"]:
        if g["group"] not in seen: seen.append(g["group"])
glegend = "".join(f'<span class="key"><span class="sw" style="background:{gcol(g)}"></span>{esc(g)}</span>' for g in seen)
share = lambda key, start: sum(g["share"] for g in PROF[key]["groups"] if g["group"].startswith(start))

# ---------- the kernels, side by side, lightly highlighted
HKW = {"let", "in", "fun", "if", "then", "else", "case", "end", "type"}
FKW = {"func", "let", "var", "switch", "case", "if", "else", "for", "in", "null", "and", "or", "not", "true", "false"}
def hl(src, kw, cmt):
    out, i = [], 0
    for m in re.finditer(cmt + r'|(?P<s>"[^"\n]*")|(?P<n>\b\d+\b)|(?P<w>[A-Za-z_][A-Za-z_0-9]*)', src):
        out.append(esc(src[i:m.start()])); t = m.group(0)
        cls = "tk-c" if m.group("c") else "tk-s" if m.group("s") else "tk-n" if m.group("n") else "tk-k" if t in kw else None
        out.append(f'<span class="{cls}">{esc(t)}</span>' if cls else esc(t)); i = m.end()
    out.append(esc(src[i:])); return "".join(out)
KHZ = open(os.path.join(HERE, "kernels.hz")).read(); KFU = open(os.path.join(HERE, "kernels.fum")).read()
KFU_HELD = "let held = build(n, null); func h_id(k) { k }; func h_ref(k) { let u = held; k }; func h_walk(k) { len(held) }; 0"

# ---------- Fumola native against wasm, on one runner
if HAVE_GH:
    def ghrow(k, n):
        a, b, c = GN[(k, n)], GW[(k, n)], GH[(k, n)]
        return (f"<tr><td><code>{k}</code></td><td class=n>{n:,}</td><td class=n>{fmt(a['ms'])}</td><td class=n>{fmt(b['ms'])}</td><td class=n>{fmt(c['ms'])}</td>"
                f"<td class=n><b>{x(b['ms'], a['ms'])}</b></td><td class=n><b>{x(c['ms'], b['ms']) if c['ms'] >= b['ms'] else '1/' + x(b['ms'], c['ms'])}</b></td><td class=n>{1000*a['ms']/a['steps']:.3f}</td><td class=n>{1000*b['ms']/b['steps']:.3f}</td></tr>")
    GHT = "".join(ghrow(k, s[-1]) for k, _, s in KERNELS)
    step_kernels = [("count", 5000), ("fib", 16), ("sumbuild", 3000), ("mapinc", 3000), ("h_walk", 3000)]
    wr = [GW[q]["ms"] / GN[q]["ms"] for q in step_kernels]
    WASM_RATIO = f"{min(wr):.1f}x to {max(wr):.1f}x"
    NATIVE = f"""<p>On one of GitHub's runners ({esc(CPU)}), Fumola built twice from the same commit (<code>2ec634b</code>) runs every kernel through the same entry point, <code>fumola_eval_top</code>: once compiled to the machine, once to wasm in node. Hazel's best build runs beside them. The mean of {gh_rounds} rounds, ms per call at the largest size:</p>
<div class="scroll"><table><tr><th>kernel</th><th>n</th><th>Fumola native</th><th>Fumola wasm</th><th>Hazel (js)</th><th>wasm / native</th><th>Hazel / Fumola wasm</th><th>native µs a step</th><th>wasm µs a step</th></tr>{GHT}</table></div>
<p><b>Wasm costs Fumola {WASM_RATIO} on the programs that run many steps</b> (the median of each program's ratio at its largest size: {sorted(wr)[len(wr)//2]:.1f}x). That is all the compilation target does to Fumola, and it is small beside the gap: against native Fumola, Hazel is {x(GH[("count", 5000)]["ms"], GN[("count", 5000)]["ms"])} slower on the loop and {x(GH[("fib", 16)]["ms"], GN[("fib", 16)]["ms"])} on calls; against Fumola in wasm, {x(GH[("count", 5000)]["ms"], GW[("count", 5000)]["ms"])} and {x(GH[("fib", 16)]["ms"], GW[("fib", 16)]["ms"])}. Hazel's own js penalty cannot be measured the same way: its core does not build natively (its utility library depends on a browser UI library, <code>bonsai.web</code>), so what js costs it shows only where a profile names a js-only cost, as with ids above.</p>
<p>One more difference this table shows: <b>a call's floor</b>. A Fumola call that does nothing (<code>h_id</code>) costs {fmt(GN[("h_id", 3000)]["ms"])} ms natively and {fmt(GW[("h_id", 3000)]["ms"])} ms in wasm, the price of parsing the call's text and writing its answer as JSON, natively too. Hazel's is {fmt(GH[("h_id", 3000)]["ms"])} ms: a JS function called with a JS value. For a game that asks a rule once a frame, Fumola's floor is about 2% of a 60 fps frame; Hazel's is nothing.</p>"""
else:
    WASM_RATIO = None
    NATIVE = """<p class="pending"><b>Running.</b> On one of GitHub's runners, Fumola built twice from the same commit (<code>2ec634b</code>), native and wasm, runs every kernel through the same entry point (<code>fumola_eval_top</code>), with Hazel's best build beside them: Adapton/fumola branch <code>bench/545-contrast</code>, run 39850338974. This section fills in when it finishes.</p>"""

# ---------- report 27's Figure 1, read again
R27F = {r["n"]: r for r in json.load(open(os.path.join(R, "..", "027", "data", "fumola_1.json")))}
R27H = {r["n"]: r for r in json.load(open(os.path.join(R, "..", "027", "data", "data_hazel_best_1.json")))}
f64, h64 = R27F[64], R27H[64]

sb3h, sb3f = HL[("sumbuild", 3000)]["ms"], FL[("sumbuild", 3000)]["ms"]
sb1h = HL[("sumbuild", 100)]["ms"]
hr = {n: HL[("h_ref", n)]["ms"] for n in (100, 1000, 3000)}; fr = {n: FL[("h_ref", n)]["ms"] for n in (100, 1000, 3000)}
sk = {n: (HL[("skip", n)]["ms"], FL[("skip", n)]["ms"]) for n in (100, 1000, 3000)}
ev_r3 = kinds("h_ref", 3000)[0]
INSIDE = [json.loads(l) for l in open(os.path.join(R, "data", "inside_vs_js_laptop_1.jsonl")) if l.strip()]
IN_ROWS = "".join(f"<tr><td class=n>{r['n']:,}</td><td class=n>{r['passes_per_call_inside_hazel']:.0f}</td><td class=n>{r['passes_per_call_from_js']:,}</td><td class=n>{fmt(r['ms_per_call_from_js'])}</td></tr>" for r in INSIDE)

# ---------- first fixes, on trial branches (^ticket(547), 548, 551): data/fixes/, when there
FX = os.path.join(R, "data", "fixes")
def fx(name):
    p = os.path.join(FX, name)
    if not os.path.exists(p): return None
    return [json.loads(l) for l in open(p) if l.strip()] if p.endswith(".jsonl") else json.load(open(p))
def by(rows): return {(r["k"], r["n"]): r for r in rows} if rows else {}
K0, K547, K548 = by(fx("kernels_stats.json")), by(fx("kernels_closures.json")), by(fx("kernels_asc.json"))
TR0, TR547 = fx("tree_stats.json"), fx("tree_closures.json")
HD = fx("handles_handles.json")
def fixrow(label, k, n, before, after):
    b, a = before.get((k, n)), after.get((k, n))
    if not (b and a): return ""
    return f"<tr><td>{label}</td><td><code>{k}</code></td><td class=n>{n:,}</td><td class=n>{fmt(b['ms'])}</td><td class=n>{fmt(a['ms'])}</td><td class=n><b>{x(b['ms'], a['ms']) if b['ms'] >= a['ms'] else '1/' + x(a['ms'], b['ms'])}</b></td></tr>"
FIXROWS = "".join(fixrow("^ticket(547) closures", k, n, K0, K547) for k in ("h_ref", "h_walk", "h_id") for n in (100, 1000, 3000)) + \
          "".join(fixrow("^ticket(548) ascriptions", k, n, K0, K548) for k in ("sumbuild", "mapinc") for n in (100, 1000, 3000)) + \
          "".join(fixrow(lab, k, n, K0, K) for lab, K in (("^ticket(547) closures", K547), ("^ticket(548) ascriptions", K548)) for k in ("count",) for n in (5000,)) 
def treerows():
    if not (TR0 and TR547): return ""
    b = {r["n"]: r for r in TR0}; a = {r["n"]: r for r in TR547}
    return "".join(f"<tr><td class=n>{n}x{n} ({n*n:,})</td><td class=n>{fmt(b[n]['held'])}</td><td class=n>{fmt(a[n]['held'])}</td><td class=n>{fmt(b[n]['tree'])}</td><td class=n>{fmt(a[n]['tree'])}</td><td class=n>{fmt(a[n]['near'])}</td></tr>" for n in sorted(a) if n in b)
def handlerows():
    if not HD: return ""
    return "".join(f"<tr><td class=n>{r['n']}x{r['n']} ({r['cells']:,})</td><td class=n>{fmt(r['ignore'])}</td><td class=n>{fmt(r['ignore_h'])}</td><td class=n>{fmt(r['passedU'])}</td><td class=n>{fmt(r['passedU_h'])}</td><td class=n>{fmt(r['passedA'])}</td><td class=n>{fmt(r['passedA_h'])}</td><td class=n>{fmt(r['handle_ms'])}</td></tr>" for r in HD if 'passedU_h' in r)
FIXES = ""
if FIXROWS or treerows() or handlerows():
    FIXES = '<h2 id="fixes">First fixes, on trial branches</h2>\n<p>Three of the findings above, each fixed on a trial branch of the counter build (<code>trial/r25-stats</code>), built by GitHub, measured on the laptop as before against the counter build itself (so both sides carry the counter). Not PRs yet.</p>\n<ul>\n<li><code>trial/r25-closures</code> (<code class="ref"><b>^ticket(</b>547<b>)</b></code>): the library hands JS functions unfinished, as closures over their environments (<code>Evaluator.evaluate_unfinished</code>), in <code>run</code> and in every call.</li>\n<li><code>trial/r25-asc</code> (<code class="ref"><b>^ticket(</b>548<b>)</b></code>): a list push stops at a tail #2681\'s memo already knows; the memo stops remembering at one; and the evaluator\'s <code>Asc</code> rule no longer asks a throwaway stepwise push first.</li>\n<li><code>trial/r25-handles</code> (<code class="ref"><b>^ticket(</b>551<b>)</b></code>, on the closures branch): <code>Hazel.value(x)</code> converts once and returns a handle a call takes in x\'s place.</li>\n</ul>\n'
    if FIXROWS:
        FIXES += f'<div class="scroll"><table><tr><th>fix</th><th>program</th><th>n</th><th>ms before</th><th>ms after</th><th>faster</th></tr>{FIXROWS}</table></div>\n'
    if treerows():
        FIXES += f'<h3 id="fix-world-held">The World rule, the world held</h3><p>^report(25)\'s held list (walked) and <code class="ref"><b>^ticket(</b>540<b>)</b></code>\'s balanced tree (looked up), each built once and held in a closure, ms a move, before and after <code class="ref"><b>^ticket(</b>547<b>)</b></code>:</p><div class="scroll"><table><tr><th>map (cells)</th><th>held list, before</th><th>held list, after</th><th>tree, before</th><th>tree, after</th><th>neighbours passed</th></tr>{treerows()}</table></div>\n'
    if handlerows():
        FIXES += f'<h3 id="fix-world-passed">The World rule, the world passed</h3><p>The map passed at every call, as JS (converted each time) and as a handle (converted once, <code>Hazel.value</code>), ms a call; <i>ignore</i> is a rule that does not look at it, so the boundary alone; <i>U</i> and <i>A</i> the unannotated and annotated finder:</p><div class="scroll"><table><tr><th>map (cells)</th><th>ignore, JS</th><th>ignore, handle</th><th>U, JS</th><th>U, handle</th><th>A, JS</th><th>A, handle</th><th>Hazel.value, once</th></tr>{handlerows()}</table></div>\n'
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where the Gap Comes From</title>
<meta name="description" content="Hazel and Fumola on the same small programs, with step counts and profiles: Hazel takes about half Fumola's steps but each costs about fifteen times as much; lists in Hazel are re-walked on every reference and re-typed on every loop; wasm is a small part.">
<style>{STYLE}
pre.code .tk-k {{ color: var(--accent); font-weight: 600; }} pre.code .tk-s {{ color: var(--good); }} pre.code .tk-n {{ color: var(--warn); }} pre.code .tk-c {{ color: var(--muted); font-style: italic; }}
pre.code {{ white-space: pre-wrap; font-size: 0.82em; }}
.panels {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 10px; }}
.panel p {{ margin: 0; font-size: 0.78em; color: var(--muted); }}
.keys {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 0.85em; color: var(--muted); margin: 6px 0; }}
.key {{ display: inline-flex; align-items: center; gap: 6px; }} .sw {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; }}
.side {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px; }}
@media (max-width: 760px) {{ .side {{ grid-template-columns: minmax(0, 1fr); }} }}
.side h4 {{ margin: 4px 0; font-size: 0.9em; color: var(--muted); }}
.pending {{ border-left: 4px solid var(--warn); padding: 6px 12px; background: var(--paper); border-radius: 6px; }}
</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>29<b>)</b></code> · performance · started 2026-10-22 · <span class="wip">work in progress</span> · about 10 minutes to read</p>
<h1>Where the Gap Comes From</h1>
<p class="sub">Matthew, on <a href="../027/#fig-sizes">^report(27)'s Figure 1</a>: <q>seems to say that Hazel and Fumola are less than 3x apart in this situation. How would you attribute the difference in performance? Is it Wasm vs JS -- or more than that? Both use a small-step evaluation system, for a language with purely-functional, higher order data. Let's draft a report WIP --- looking more into the contrast and how it shows up with actual analysis of each system, while running the same programs.</q> Eight small programs, written the same way in both languages, timed, step-counted and profiled (<code class="ref"><b>^ticket(</b>545<b>)</b></code>).</p>

<div class="headline">
<p><b>Short answers.</b> More than wasm against js. The first three are the causes, each measured below; the last two are where the target and the boundary come in.</p>
<ol class="ans">
<li><b>Hazel takes fewer steps, and each costs far more.</b> For the same loop, Hazel's evaluator makes about half as many passes as Fumola's machine takes steps ({ev_c:,} against {f_c['steps']:,} for <code>count(1000)</code>): Fumola's steps are finer. But a Hazel pass costs about {us_hc:.1f} µs and a Fumola step about {us_fc:.2f} µs, some {us_hc / us_fc:.0f} times as much. Net, Fumola is {x(HL[("count", 5000)]["ms"], FL[("count", 5000)]["ms"])} faster on the loop and {x(HL[("fib", 16)]["ms"], FL[("fib", 16)]["ms"])} on calls.</li>
<li><b>A Hazel step pays for the editor around it.</b> Every term the evaluator visits, values included, goes through five stages: state merging, a reuse check, probe sampling, recording effects, then the rule itself. On the loop, the rule is {100 * share("count_5000", "the step's rule"):.0f}% of the time; garbage collection is {100 * share("count_5000", "garbage collection"):.0f}%, and the stages and their trampolines {100 * (share("count_5000", "the evaluator's stages") + share("count_5000", "trampolines")):.0f}%. Fumola's machine keeps values apart from syntax and steps a continuation: one match, no stages.</li>
<li><b>On lists, Hazel's costs grow with the list, so the gap does too.</b> Two causes, both found here:
 <ul>
 <li><b>A function handed to JS carries its captured values as text.</b> When Hazel's JS library returns a function, it writes the function's environment into its body (<code>finish</code>: <code>Substitution.in_exp</code>), so a list the function holds becomes a list literal inside it, evaluated again, element by element, at every call: {fmt(hr[100])}, {fmt(hr[1000])} and {fmt(hr[3000])} ms for lists of 100, 1,000 and 3,000, where Fumola's stays at about {fmt(fr[3000])} ms. Called from inside Hazel, the same function costs {INSIDE[0]['passes_per_call_inside_hazel']:.0f} passes at every size: <b>Hazel's evaluator holds values in O(1); its library does not.</b> This is what holding the world cost in <a href="../027/">^report(27)</a>, and what <code class="ref"><b>^ticket(</b>540<b>)</b></code> was chasing.</li>
 <li><b>A list loop is quadratic.</b> Each iteration that passes the growing list on pushes its type, <code>[Int]</code>, over every element again, minting a fresh id for each part and then keeping none of them. Building and summing 3,000 numbers: {fmt(sb3h)} ms in Hazel, {fmt(sb3f)} ms in Fumola, {x(sb3h, sb3f)}.</li>
 </ul></li>
<li><b>Where js does show, it is in Hazel's ids.</b> A fresh id is a UUID written into 16 bytes, and js_of_ocaml turns bytes into a JS string by hand: about three quarters of minting an id, and {100 * share("sumbuild_1000", "fresh ids"):.0f}% of the list loop's time. A native build would copy 16 bytes. {"Wasm costs Fumola " + WASM_RATIO + " against its native build on the same runner." if WASM_RATIO else "What wasm costs Fumola, native against wasm on one runner, is running on GitHub (below)."}</li>
<li><b>Hazel's boundary is the cheaper one.</b> Passing in 3,000 numbers from JS costs Hazel {fmt(sk[3000][0])} ms; Fumola, which takes only source text, parses them in {fmt(sk[3000][1])} ms. For ^report(27)'s map of 4,096 cells: {fmt(h64["idU"])} ms in Hazel, most of Fumola's {fmt(f64["passed"])}.</li>
</ol>
</div>

<figure class="fig" id="fig-kernels"><div class="keys">{legend}</div><div class="panels">{panels}</div><figcaption><b>Figure 1.</b> ms per call against n, both scales logarithmic, one panel per program. {"On one GitHub runner, the mean of " + str(gh_rounds) + " rounds." if HAVE_GH else "Node on the Ubuntu laptop (Intel i7), one round so far."} Where the lines stay parallel the gap is a constant factor; where Hazel's climbs faster (<code>sumbuild</code>, <code>mapinc</code>, <code>h_ref</code>) it is growing with the data. <code>skip</code> is the only one Hazel wins.</figcaption></figure>

<h2 id="programs">The programs</h2>
<p>Each written the way the other language would, as near as the two allow: recursion over numbers, and lists built from pairs (Hazel's <code>::</code>, Fumola's <code>?(x, rest)</code>, since Fumola's <code>[...]</code> are arrays). No type annotations in either; Hazel infers and inserts its own. A <i>held</i> list is built once, outside the call, and captured: in Hazel by a closure, in Fumola by a top-level binding. Every call's answer is checked.</p>
<div class="side"><div><h4>Hazel (<code>drivers/kernels.hz</code>)</h4><pre class="code">{hl(KHZ, HKW, r"(?P<c>#[^#\n]*#)")}</pre></div>
<div><h4>Fumola (<code>drivers/kernels.fum</code>)</h4><pre class="code">{hl(KFU, FKW, r"(?P<c>//[^\n]*)")}</pre>
<p class="note">and, for a held list of n, one text:</p><pre class="code">{hl(KFU_HELD, FKW, r"(?P<c>//[^\n]*)")}</pre></div></div>

<h2 id="steps">Steps, and what each costs</h2>
<p>Fumola counts its steps in every answer. Hazel's count came from a measuring build (<code>trial/r25-stats</code>: the best build, with a counter in the evaluator) that tallies every pass of the evaluator by the kind of step it took, or none when the term was already final. Times are from the best build without the counter, on the laptop.</p>
<div class="scroll"><table><tr><th>program</th><th>n</th><th>Hazel ms</th><th>Fumola ms</th><th>Hazel / Fumola</th><th>Hazel passes</th><th>Hazel steps</th><th>Fumola steps</th><th>Hazel µs a pass</th><th>Fumola µs a step</th></tr>{T1}</table></div>
<p class="note">A Hazel <i>pass</i> is one trip through the evaluator's stages for one term; a <i>step</i> is a pass that rewrote the term (the rest found a value). Fumola's step is one transition of its machine. Hazel's steps for <code>count(1000)</code>: {st_c:,}, nine an iteration (a lookup, an application, a comparison, a subtraction, ...); Fumola's: {f_c['steps']:,}, twenty-seven an iteration, since its machine writes down every frame it pushes and pops.</p>
<p><b>Read across a row.</b> Where the passes grow with n and the µs a pass stays put (<code>count</code>, <code>fib</code>, <code>h_walk</code>), the gap is steps times the cost of each: a constant factor, about {x(HL[("h_walk", 3000)]["ms"], FL[("h_walk", 3000)]["ms"])} to {x(HL[("count", 5000)]["ms"], FL[("count", 5000)]["ms"])}. Where the µs a pass climbs with n (<code>sumbuild</code>: {1000 * HL[("sumbuild", 100)]["ms"] / kinds("sumbuild", 100)[0]:.1f}, then {1000 * HL[("sumbuild", 1000)]["ms"] / kinds("sumbuild", 1000)[0]:.1f}, then {1000 * HL[("sumbuild", 3000)]["ms"] / kinds("sumbuild", 3000)[0]:.1f} µs), some pass is doing work that grows with the data. And where the passes themselves grow with a list the program never walks (<code>h_ref</code>: {ev_r3:,} passes for one reference to 3,000 numbers), the evaluator is visiting it anyway.</p>

<h2 id="hazel-step">What a Hazel step costs</h2>
<p>Hazel's evaluator is small-step in what it records, but it runs as a recursive descent: <code>evaluate</code> asks for each subterm's value by calling itself, on a trampoline so deep recursion does not overflow JS's stack. Every call goes through the same stack of stages (<code>src/language/dynamics/Evaluator.re</code>):</p>
<ol>
<li><code>eval_5_state_merge</code>: at the top level, a fresh state, merged back after.</li>
<li><code>eval_4_reuse</code>: has this term's value been kept from a previous run? (the incremental evaluation of live programming)</li>
<li><code>eval_3_record_probe_sample</code>: is this term probed? Open and close a sample.</li>
<li><code>eval_2_until_final</code>: step until the term is final.</li>
<li><code>eval_1_effects</code>: run the step's effects on the state (stack frames, pattern matches for probes), update the reuse map.</li>
<li><code>eval_0_main</code>: the rule itself (<code>Transition.re</code>), with the stages above as its way of evaluating subterms.</li>
</ol>
<p>The stages are what make Hazel's live features work: probes, the stepper, results kept across edits. They run for every term, including numbers and lists that are already values. Profiles of the calls alone (set-up excluded), on a build that keeps OCaml's names (<code>embed-520</code>'s dev build, 2026-10-21; its evaluator is the same shape as the best build's):</p>
<figure class="fig" id="fig-profile"><div class="keys">{glegend}</div>{fig_profiles()}<figcaption><b>Figure 2.</b> Where a Hazel call's time goes, by the OCaml file each sample's code came from (js_of_ocaml's runtime helpers counted with their caller). <code>drivers/prof_ref.mjs</code> and <code>drivers/profiles.py</code>; values in <code>data/prof_*.json</code>.</figcaption></figure>
<ul>
<li><b>The loop</b> (<code>count</code>): garbage collection is the largest part. Each pass allocates: a trampoline closure per request, a new state record, a fresh term for each result. The rule is {100 * share("count_5000", "the step's rule"):.0f}%.</li>
<li><b>The list loop</b> (<code>sumbuild</code>): {100 * share("sumbuild_1000", "fresh ids"):.0f}% minting fresh ids, and most of the rest pushing types and collecting the garbage. The next section is why.</li>
<li><b>One reference to a held list, from JS</b> (<code>h_ref</code>): all of it in the stages and their trampolines: {ev_r3:,} passes, one for the list and one for each number in it, each finding a value and taking no step (why: the next section).</li>
</ul>

<h2 id="lists">Why lists cost more in Hazel</h2>
<h3 id="re-walk">A function returned to JS re-evaluates what it holds</h3>
<p>Using a list that a function holds costs a pass for every part of the list, when the function is called from JS: <code>let u = held in k</code>, <code>(held, 1)</code>, <code>case held | _ =&gt; k end</code>, <code>(fun x -&gt; k)(held)</code> all cost n + 8 passes for a list of n, twice that for two references, and three passes a pair for a list of pairs. It does not matter how the list was made (built in Hazel, passed in from JS, annotated). A reference in a branch not taken costs nothing.</p>
<p>A trace of every pass (a copy of the dev build, patched to log the term each pass visits) shows why. The function's body, as the library calls it, is not <code>let u = held in k</code> but <code>let u = [1, 2, 3, 4] in k</code>: the held list has become a literal in the body. Evaluating a literal list evaluates each element, as it must for <code>[1 + 1, f(x)]</code>.</p>
<pre class="code">&gt; Closure(Let(...))                 the body, after the call's FunAp
  &gt; Let(...)
    &gt; ListLit[4]                    held, written in as a literal
      &gt; Atom  &lt; Atom Final (no step)   ... once for each element
    &lt; ListLit[4] Final (no step)
  &gt; Closure(Var(k))  &lt; Final</pre>
<p>The literal is written in by the library, not the evaluator. <code>Evaluator.evaluate</code> finishes every result with <code>finish = e =&gt; e |&gt; Substitution.in_exp(env) |&gt; Exp.replace_all_ids</code>, which turns a closure (a function and its environment) into a closed term by substituting the environment's values into the body. <code>HazelLibCore.to_js</code> then wraps that closed term as a JS function. Inside Hazel nothing is substituted: a closure keeps its environment, and a variable's lookup is one step (<code>Transition.re</code> marks a looked-up list final and returns it as it is). Measured with the counter build, the same held function called 100 times by a Hazel loop against called once from JS:</p>
<div class="scroll"><table><tr><th>list held (n)</th><th>passes a call, from Hazel</th><th>passes a call, from JS</th><th>ms a call, from JS</th></tr>{IN_ROWS}</table></div>
<p>So this cost is the library's, and the fix is the library's: hand JS the closure as the evaluator left it, environment and all, rather than its finished form; the call then applies the closure as Hazel would. That is the same move as <code class="ref"><b>^ticket(</b>539<b>)</b></code>'s change for a call's argument (bind it in the environment, do not write it in), made for what comes back. Fumola never has this problem: its values are not syntax, so there is nothing to write back into a body.</p>
<h3 id="re-type">A loop re-types its list</h3>
<p>Hazel is gradually typed: it inserts type ascriptions where it infers types, and pushes them through values as it runs. In <code>build(n - 1, n :: acc)</code> the accumulator meets <code>[Int]</code> once an iteration (the counter build shows one <code>Ascription</code> step per iteration), and the push walks the whole list, with a fresh term and a fresh id for each element (<code>src/language/dynamics/transition/Ascriptions.re</code>):</p>
<pre class="code">| (ListLit(ds), List(ty)) =&gt;
  let ds' = List.map(d =&gt; recur(Asc(d, ty) |&gt; DHExp.fresh), ds);
  unchanged(ds, ds')
    ? Some(e)
    : Some(IdTagged.fast_copy(DHExp.rep_id(e), ListLit(ds') |&gt; DHExp.fresh));</pre>
<p>In the profile of <code>sumbuild(1000)</code>, 60% of the time is spent inside <code>Ascriptions.re</code>, the ids it mints included. When every element already has the type, <code>unchanged</code> gives back the list as it was, so the result is right and small; but the n wrappers and their n ids were made first and are thrown away. Over a loop of n iterations that is about n²/2 ids. #2681's memo (<a href="../026/">^report(26)</a>) skips this push for a value it has seen at the top of an annotated call; an accumulator is new at every iteration, so it is never seen.</p>
<p>Two changes would help, neither tried yet: check whether a part needs the push before wrapping it (an element of type <code>Int</code> that is an <code>Int</code> needs nothing), and mint ids only for parts that change.</p>
<h3 id="ids">And a fresh id is dear under js</h3>
<p>Hazel's ids are UUIDs (<code>src/util/Id.re</code>). Minting one is already cheap in OCaml terms (a counter written into 16 bytes, not a random draw), but <code>Uuidm.v4</code> copies the bytes into a string, and under js_of_ocaml bytes are an array and a string is a JS string, so the copy is a loop over 16 characters building a JS string. In the list loop's profile, {100 * share("sumbuild_1000", "fresh ids"):.0f}% of the time is under <code>Id.mk</code>, and three quarters of that is js_of_ocaml's <code>caml_subarray_to_jsbytes</code> and <code>caml_convert_bytes_to_array</code>. This is the one place where the target clearly costs Hazel: natively it would be a 16-byte copy.</p>

<h2 id="fumola-step">What a Fumola step is</h2>
<p>Fumola's machine (<code>crates/fumola_semantics/src/lib/vm_step.rs</code>) is a continuation machine: its state is the current continuation (an expression to evaluate or a value to return), a stack of frames, and an environment, a persistent hash map (<code>im_rc</code>) from names to values. Values are their own type, apart from syntax, so a list held in the environment is a pointer that is never looked into again. A step is one transition: push a frame, pop one, look a name up. Steps are many and small (twenty-seven an iteration of <code>count</code>) and cost about {us_fc:.2f} µs each in wasm. Fumola's incremental machinery (Adapton's graph) is paid only when a program uses it; Hazel's stages run for every term. <code>do big {{ ... }}</code> runs a region without writing its intermediate states down, about twice as fast again (Adapton/fumola#128, not used here).</p>
<p>One thing found on the way: a Fumola answer that is a list over about 1,000 deep crashes the wasm instance (<q>memory access out of bounds</q>): turning the answer into JSON recurses, and wasm's stack runs out. Holding a list is fine; returning it is not. The kernels end their set-up text with <code>0</code> to stay clear.</p>

<h2 id="native">Wasm against native</h2>
{NATIVE}

<h2 id="report-27">Report 27's Figure 1, read again</h2>
<p>At 64x64 (4,096 cells), the World rule:</p>
<ul>
<li><b>Passed in: Hazel {fmt(h64["shipped"])} ms, Fumola {fmt(f64["passed"])} ms ({x(h64["shipped"], f64["passed"])}).</b> Close, for different reasons. Fumola spends most of its time parsing the map, written out as {f64["passed_chars"]:,} characters of source text, every call ({f64["passed_steps"]:,} steps). Hazel spends {fmt(h64["idU"])} ms bringing the map over from JS (a rule that ignores it, given the same map: <a href="../025/">^report(25)</a>'s <code>idU</code>), records and lists of text being dearer to convert than the numbers of <code>skip</code>, and the rest, {fmt(h64["shipped"] - h64["idU"])} ms, walking the list, about {1000 * (h64["shipped"] - h64["idU"]) / 4096:.0f} µs a cell, a few dozen passes each. The finder's annotation costs one look-up a call, not a walk: #2681's memo knows every tail of a list it has checked.</li>
<li><b>Held as a list and walked: Hazel {fmt(h64["held"])} ms, Fumola {fmt(f64["held_list"])} ms ({x(h64["held"], f64["held_list"])}).</b> Steps times their cost, as in <code>h_walk</code>, plus, in Hazel, the held world re-evaluated as a literal at every call, since the rule is a function the library returned to JS.</li>
<li><b>Neighbours only: about 1 ms each.</b> The boundary is all there is, and the two boundaries cost about the same for a handful of cells.</li>
</ul>
<p>So the Figure's under-3x lines are the ones where something other than stepping dominates. Where stepping dominates, the gap is {x(HL[("h_walk", 3000)]["ms"], FL[("h_walk", 3000)]["ms"])} to {x(HL[("count", 5000)]["ms"], FL[("count", 5000)]["ms"])}; where Hazel's per-use walks and re-typing apply, it grows without bound.</p>

{FIXES}
<h2 id="next">What next</h2>
<ol>
<li><b>Keep closures whole across the library</b> (<code class="ref"><b>^ticket(</b>547<b>)</b></code>): functions returned to JS as the evaluator left them, not finished, on a trial branch stacked with <code class="ref"><b>^ticket(</b>539<b>)</b></code>'s, and these programs measured again: <code>h_ref</code> should be flat. Then <code class="ref"><b>^ticket(</b>540<b>)</b></code>'s balanced tree for the World rule can pay off: a held world, O(log N) a move.</li>
<li><b>Push types without copying</b> (<code class="ref"><b>^ticket(</b>548<b>)</b></code>): check before wrapping in <code>Ascriptions.re</code>, and measure <code>sumbuild</code> again: it should become linear.</li>
<li><b>Cheaper ids under js</b>: an id that is a JS string from the start, or an integer, and what that does to the loop's 4%, the list loop's {100 * share("sumbuild_1000", "fresh ids"):.0f}%.</li>
<li><b>Fumola's deep answers</b> (<code class="ref"><b>^ticket(</b>549<b>)</b></code>): turn answers into JSON without recursion (an issue for Adapton/fumola, not filed yet).</li>
<li>The per-pass cost of the stages when nothing is probed and nothing reused: a fast path for terms that are already values would skip all five.</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>Node v22 on the Ubuntu laptop (Intel i7), one process at a time, pinned to two threads and niced. <code>drivers/kernels.mjs</code> runs the programs: Hazel through its JS library (<code>Hazel.run</code> once, then each program a JS function, called with n), Fumola through its wasm build (<code>fumola_eval_top</code> of the call's text, pinned build <code>2ec634b5df</code>). Three warm-up calls, then up to 60 timed (stopping after 2.5 s and at least 5), the median. Hazel's library: <code>trial/r25-best</code> (all the performance PRs, <a href="../025/#prs">^report(25)</a>) for times, <code>trial/r25-stats</code> (the same with a counter, <code>Hazel.stepCounts()</code>) for passes. Profiles: <code>drivers/prof_ref.mjs</code> records only the calls, through node's inspector, on a dev build with OCaml's names and source positions; <code>drivers/profiles.py</code> splits them by source file. {"GitHub: Adapton/fumola branch <code>bench/545-contrast</code> builds Fumola natively (<code>crates/fumola_wasm/examples/kernels.rs</code>, calling the same <code>fumola_eval_top</code>) and as wasm, and runs both and Hazel's best build, three rounds interleaved." if HAVE_GH else ""} One round on the laptop so far: read single differences under about 10% as noise.</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE); print("wrote 029/index.html", "with GitHub data" if HAVE_GH else "(GitHub data pending)")
