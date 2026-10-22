#!/usr/bin/env python3
"""Writes 025/index.html, ^report(25): what a call into Hazel costs.
  python3 025/drivers/gen025.py   (then build.sh runs the series tools)
Figures are inline SVG drawn from 025/data/*.json."""
import json, os, math, re
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
D = lambda f: json.load(open(os.path.join(R, "data", f)))
sizes = D("data_sizes.json"); steps = D("data_steps.json"); early = D("earlier.json")
OUT = os.path.join(R, "index.html")
by = {r["cells"]: r for r in sizes}
r256 = by[256]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

# ---------- figure 1: time vs cells, log-log lines
def fig_lines(w=640, h=330):
    series = [("shipped", "shipped rule", "var(--bad)"), ("noann", "find unannotated", "var(--warn)"),
              ("held", "map held in a closure", "var(--accent2)"), ("idA", "identity rule (conversion floor)", "var(--accent)"),
              ("near", "neighbours only", "var(--good)")]
    xs = [r["cells"] for r in sizes]
    L, Rr, T, B = 60, 170, 14, 40
    x0, x1 = math.log10(8), math.log10(700); y0, y1 = math.log10(0.3), math.log10(1000)
    X = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (w - L - Rr)
    Y = lambda v: h - B - (math.log10(v) - y0) / (y1 - y0) * (h - T - B)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Time per call against map size, log scales: the shipped rule climbs from 1.4 ms at 3x3 to 735 ms at 24x24; without the annotation 45.5 ms; neighbours only stays near 1 ms." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for v in [1, 10, 100, 1000]:
        o.append(f'<line x1="{L}" x2="{w-Rr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" style="stroke:var(--line)"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end" style="fill:var(--muted)">{v} ms</text>')
    for c in xs:
        n = int(round(math.sqrt(c)))
        o.append(f'<text x="{X(c):.1f}" y="{h-B+16}" text-anchor="middle" style="fill:var(--muted)">{n}x{n}</text>')
    o.append(f'<text x="{(L+w-Rr)/2}" y="{h-6}" text-anchor="middle" style="fill:var(--muted)">map size (cells, log scale)</text>')
    for k, name, col in series:
        pts = " ".join(f"{X(r['cells']):.1f},{Y(max(r[k],0.3)):.1f}" for r in sizes)
        o.append(f'<polyline points="{pts}" fill="none" style="stroke:{col}" stroke-width="2.2"/>')
        for r in sizes:
            o.append(f'<circle cx="{X(r["cells"]):.1f}" cy="{Y(r[k]):.1f}" r="3" style="fill:{col}"/>')
        last = sizes[-1]
        o.append(f'<text x="{X(last["cells"])+8:.1f}" y="{Y(last[k])+4:.1f}" style="fill:{col}">{last[k]:.3g} ms {name}</text>')
    o.append('</svg>')
    return "".join(o)

# ---------- figure 2: 16x16 bars per variant
def fig_bars(rows, w=640, unit="ms", aria=""):
    bh, gap, L = 24, 8, 230
    h = len(rows) * (bh + gap) + 10
    mx = max(v for _, v, _ in rows)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(aria)}" style="width:100%;height:auto;font:12.5px system-ui,sans-serif">']
    for i, (lab, v, col) in enumerate(rows):
        y = 4 + i * (bh + gap)
        bw = max(2, (w - L - 80) * v / mx)
        o.append(f'<text x="{L-8}" y="{y+16}" text-anchor="end" style="fill:var(--ink)">{esc(lab)}</text>'
                 f'<rect x="{L}" y="{y}" width="{bw:.1f}" height="{bh}" rx="3" style="fill:{col}"/>'
                 f'<text x="{L+bw+6:.1f}" y="{y+16}" style="fill:var(--ink)">{v:g} {unit}</text>')
    o.append('</svg>')
    return "".join(o)

# ---------- figure 3: where the 16x16 shipped call goes (stacked)
def fig_stack(w=640, h=96):
    floor = round(r256["idA"], 1); walk = round(r256["noann"] - r256["idA"], 1); ann = round(r256["shipped"] - r256["noann"], 1)
    parts = [("conversion + parameter ascription", floor, "var(--accent)"), ("the find walk itself", walk, "var(--warn)"), ("find's annotation re-checking the list", ann, "var(--bad)")]
    tot = sum(p[1] for p in parts); L = 10; x = L; W = w - 20
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="The shipped 16x16 call, {tot:.0f} ms: {floor} ms conversion, {walk} ms walk, {ann} ms re-checking from find\'s annotation." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for i, (lab, v, col) in enumerate(parts):
        bw = W * v / tot
        o.append(f'<rect x="{x:.1f}" y="10" width="{bw:.1f}" height="30" style="fill:{col}"/>')
        o.append(f'<text x="{L + i*W/3:.1f}" y="{62}" style="fill:{col};font-weight:600">{v} ms</text><text x="{L + i*W/3:.1f}" y="78" style="fill:var(--muted)">{lab}</text>')
        x += bw
    o.append('</svg>'); return "".join(o)

# ---------- figure 4: the floor's shares
def fig_floor(w=640, h=96):
    parts = [("re-stepping the literal", 56, "var(--accent)"), ("parameter ascription", 16, "var(--accent2)"), ("of_js", 10, "var(--warn)"), ("GC, rest", 18, "var(--cx)")]
    x = 10; W = w - 20
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="The 13.8 ms floor of a 16x16 call that does nothing: 56% re-stepping the literal, 16% ascription, 10% of_js, 18% GC and the rest." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for i, (lab, v, col) in enumerate(parts):
        bw = W * v / 100
        o.append(f'<rect x="{x:.1f}" y="10" width="{bw:.1f}" height="30" style="fill:{col}"/><text x="{x+4:.1f}" y="62" style="fill:var(--ink);font-weight:600">{v}%</text><text x="{x+4:.1f}" y="78" style="fill:var(--muted)">{lab}</text>')
        x += bw
    o.append('</svg>'); return "".join(o)

def fig(fid, n, svg, cap):
    return f'<figure class="fig" id="{fid}">{svg}<figcaption><b>Figure {n}.</b> {cap}</figcaption></figure>'

def mini(svg, cap):
    return f'<figure class="mini">{svg}<figcaption>{cap}</figcaption></figure>'

bars16 = [("shipped rule", round(r256["shipped"]), "var(--bad)"), ("find unannotated", round(r256["noann"], 1), "var(--warn)"),
          ("index arithmetic, unannotated", round(r256["index"], 1), "var(--warn)"), ("map held in a closure", round(r256["held"], 1), "var(--accent2)"),
          ("identity rule (floor)", round(r256["idA"], 1), "var(--accent)"), ("neighbours only", round(r256["near"], 2), "var(--good)"),
          ("plain JS rule", 0.001, "var(--muted)")]
F1 = fig_lines(); F2 = fig_bars(bars16, aria="16x16 call by variant: shipped 153 ms, unannotated 22.6, index 17.1, held 12.4, identity 9.5, neighbours 0.96, JS under 0.001.")
F3 = fig_stack(); F4 = fig_floor()

def tr(cells): return "<tr>" + "".join(f"<td class=n>{c}</td>" if i else f"<td>{c}</td>" for i, c in enumerate(cells)) + "</tr>"
cols = ["cells", "js_globals", "idU", "idA", "game_World", "shipped", "noann", "index", "near", "held", "held_setup"]
size_rows = "".join(tr([f'{r["n"]}x{r["n"]} ({r["cells"]})'] + [f'{r[k]:.3g}' for k in cols[1:]]) for r in sizes)
step_rows = "".join(tr([k, v]) for k, v in steps.items())
p2 = early["phase2_node_p50_p95_ms"]

STYLE = open(os.path.join(HERE, "style.css")).read()
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What a Call into Hazel Costs</title>
<meta name="description" content="Why one Dress Up room rule, run as a Hazel function from JS, takes 40-150 ms on a 16x16 map: the call converts the whole map to syntax and re-evaluates it, the parameter type re-checks it, and an annotated recursive helper re-checks the rest of the list at every step.">
<style>{STYLE}</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>25<b>)</b></code> · performance · 2026-10-22 · <span class="wip">work in progress</span> · about 9 minutes to read</p>
<h1>What a Call into Hazel Costs</h1>
<p class="sub">Matthew asked, on 2026-10-22, about <code class="ref"><b>^ticket(</b>531<b>)</b></code>, the experiment that moves Messed Up Dress Up's room rules into Hazel modules run through Hazel's JS library (<a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a>, the library; the game's side is the draft matthewhammer/kids-choice-games#2): <q>why is Hazel so slow here for 16 x 16 map? do more analysis please, and draft a new report.</q> The World room's rule takes a step on the map; in the game's own node run it costs 40.0 ms p50 at 16x16, against 0.003 ms for the same rule in JS. This report takes that one call apart.</p>

<div class="headline">
<p><b>Short answers.</b> All times are node, the minified library at <code>0d66c36618</code>, p50 of one call with the target cell mid-map, unless said otherwise.</p>
<ol class="ans">
<li><div class="row"><p><b>Most of the time is a type annotation in the rule: {r256["shipped"]:.0f} ms becomes {r256["noann"]:.1f} ms when it goes.</b> The rule's recursive helper is written <code>fun (cs, c, r) : ([Cell], Int, Int) -&gt;</code>. Hazel checks that ascription at run time on every call, by walking the value, so each step of the walk re-checks the rest of the list: one linear walk becomes a quadratic one. At 24x24 it is {by[576]["shipped"]:.0f} ms against {by[576]["noann"]:.1f} ms.</p>{mini(fig_stack(420, 96) if False else F3, "The shipped 16x16 call, split by measuring the variants.")}</div></li>
<li><div class="row"><p><b>Every call pays a floor that grows with the map: about {r256["idA"]:.1f} ms at 16x16, 31 &micro;s per cell.</b> Hazel's call boundary turns the whole JS argument into unevaluated Hazel syntax, gives every node a fresh id, and then evaluates it back into the value it already was, node by node; the <code>(Globals, Event)</code> parameter type walks it again. A rule that does nothing still pays this.</p>{mini(F4, "The floor of a 16x16 call that does nothing (13.8 ms), by profile share.")}</div></li>
<li><div class="row"><p><b>Underneath, each evaluation step costs about 3 &micro;s, so even the plain walk is 25-80 &micro;s per cell.</b> A countdown over plain Ints costs {steps["countdown i=128"]} ms for 128 steps. The time is spread over the evaluator's per-step pipeline, jsoo's generic calls, fresh ids and GC; there is no single hot spot.</p></div></li>
<li><div class="row"><p><b>Passing only the neighbouring cells makes the call flat: {r256["near"]:.2f} ms at 16x16, {by[9]["near"]:.2f} ms at 3x3.</b> That is the one change, available today without touching Hazel, that removes the dependence on map size: 160x faster than the shipped rule at 16x16, with the same answer.</p></div></li>
</ol>
</div>

{fig("fig-sizes", 1, F1, "Time per call against map size, both scales logarithmic, for five versions of the World rule that return the same answer. The shipped rule's slope is 1.78 (quadratic-ish); the others are linear (slope 1.0), except neighbours-only, which is flat. Values from <code>data/data_sizes.json</code>.")}

<h2 id="call">What happens in one call</h2>
<p>The game compiles each room's module once (<code>runProgram</code>) and keeps the JS function Hazel gives back for the room's <code>on_event</code>. On each event it calls that function with two arguments, <code>Globals</code> and <code>Event</code>. For the World room, <code>Globals</code> holds the player's position, the map size and <code>cells</code>, a list with one record per square: <code>{{col, row, kind, ways}}</code>. The game rebuilds it on every event (0.098 ms in JS at 16x16, negligible). Inside the library (<code>src/web/HazelLibCore.re</code>, <code>function_of</code>), each call then:</p>
<ol>
<li>runs <code>of_js</code> on each argument. This does not build Hazel values: arrays become <code>ListLit</code> syntax, objects a <code>Tuple</code> of <code>TupLabel</code>s, and every node gets a fresh id (<code>Exp.fresh</code>, which calls <code>Id.mk</code>, a UUID). 256 cells make about 4.6k nodes.</li>
<li>builds <code>Ap(f, arg)</code> and evaluates it from scratch, with no statics and no reuse.</li>
<li>the evaluator steps the argument back into a value, one node at a time, through the whole stepping pipeline (<code>Transition.re</code>'s <code>ListLit</code>, <code>Tuple</code> and <code>TupLabel</code> cases).</li>
<li>matching the parameter pattern <code>(g : Globals, e : Event)</code> pushes the type ascription through the whole record (<code>Ascriptions.re</code>), allocating a fresh <code>Asc</code> node and id per element even where nothing changes.</li>
<li>runs the rule, then converts the (small) result back with <code>to_js</code>.</li>
</ol>
<p>A 16x16 call with an event the rule ignores (<code>| _ =&gt; Done</code>) costs 13.8 ms; the same call with no cells costs 0.44 ms. That difference is steps 1, 3 and 4 alone, about 3 &micro;s per node. Its profile shares are in Figure 2; <code>Id.mk</code> is about 20% of all time, and the top self-time entry is <code>caml_subarray_to_jsbytes</code>, the byte copy in its UUID.</p>
{fig("fig-floor", 2, F4, "Where the floor of a 16x16 call goes, from a 3 s profile of the dev build: re-stepping the converted literal, pushing the parameter ascription, <code>of_js</code>, and GC with the rest. Profiled times run long; the shares are what to read.")}

<h2 id="quadratic">Why the rule's walk is quadratic</h2>
<p>The World rule finds the target square with a recursive helper:</p>
<pre class="code">let find = fun (cs, c, r) : ([Cell], Int, Int) -&gt;
  case cs | [] =&gt; ... | x :: rest =&gt; if x.col == c &amp;&amp; x.row == r then ... else find(rest, c, r) end</pre>
<p>Hazel's evaluator treats a pattern with a type ascription as a run-time check: <code>PatternMatch.re</code> wraps the argument in <code>Asc(d, ty)</code> and <code>Ascriptions.transition_multiple</code> pushes it through the value, element by element and field by field. So <code>find(rest, c, r)</code> re-checks all of <code>rest</code>, at every step. A walk to index <i>i</i> in a list of length <i>L</i> costs about <i>i</i> &times; <i>L</i>. In a profile of a deep find, 58.6% of the time is in <code>transition_multiple</code> under <code>matches_inner</code>.</p>
<p>That is also why the game's own figure, 40 ms, is lower than this report's 153 ms: the cost depends on where the target sits in the list. With all four ways set, a target at index 1 costs 18 ms at 16x16 and the last one 244 ms; removing only the annotation brings the last to 33 ms (8x8: 23 to 8.9 ms). The Square room's <code>find</code> and <code>doors</code> helpers are annotated the same way, which fits a lever with 40 doors taking about 85 ms.</p>
{fig("fig-16", 3, F2, "One 16x16 World call, by version of the rule; every version returns the same <code>GoSquare</code>. <i>Index arithmetic</i> takes one <code>nth</code> at <code>r*cols+c</code>; <i>held</i> converts the map once into a Hazel closure (62 ms at setup) and calls it per event; <i>identity</i> is a rule that ignores its argument, so it is the floor.")}

<h2 id="data">The numbers</h2>
<h3 id="t-sizes">By map size (ms, p50)</h3>
<div class="scroll"><table><tr><th>map (cells)</th><th>JS Globals</th><th>identity, no ascription</th><th>identity</th><th>game's World</th><th>shipped</th><th>unannotated</th><th>index</th><th>neighbours</th><th>held</th><th>held setup</th></tr>{size_rows}</table></div>
<p class="note"><i>game's World</i> is the rule as the game compiles it; <i>shipped</i> is the same text rebuilt in the driver (they agree within noise above 8x8). Growth exponents from 64 to 576 cells: shipped 1.78, unannotated 1.03, index 1.01, identity 1.00, held 1.32, neighbours 0.35.</p>
<h3 id="t-steps">Per-step costs (ms, p50)</h3>
<div class="scroll"><table><tr><th>program</th><th>ms</th></tr>{step_rows}</table></div>
<p class="note">A <i>walk</i> goes to index <i>i</i> of a list of length <i>L</i> held in a closure; at <i>i</i> = 0 it still costs O(<i>L</i>), since the held list is re-stepped when it is substituted into the call. The countdown uses no data at all.</p>
<h3 id="t-game">The game's own measurements</h3>
<div class="scroll"><table><tr><th>measure</th><th>value</th></tr>
{tr(["World 3x3, node p50 / p95", f'{p2["World 3x3"][0]} / {p2["World 3x3"][1]} ms'])}
{tr(["World 8x8, node p50 / p95", f'{p2["World 8x8"][0]} / {p2["World 8x8"][1]} ms'])}
{tr(["World 16x16, node p50 / p95", f'{p2["World 16x16"][0]} / {p2["World 16x16"][1]} ms'])}
{tr(["World in plain JS", f'{p2["World JS"]} ms'])}
{tr(["FallPit, WayOut", f'{p2["FallPit"]}, {p2["WayOut"]} ms'])}
{tr(["lever with 2, 8, 40 doors", f'{p2["lever 2 doors"]}, {p2["lever 8 doors"]}, about {p2["lever 40 doors"]} ms'])}
{tr(["browser (Chrome, 8 runners): Hazel adds per event", "0.4-3.2 ms (red lever on EPYC 7763: 9.4 to 12.1 ms)"])}
{tr(["browser: page load, Hazel vs JS", "about 525 vs 270 ms"])}
{tr(["browser: first compile of the rules", "340-520 ms"])}
{tr(["browser: heap, Hazel vs JS", "67 vs 51 MB"])}
</table></div>
<p class="note">The browser rows are the phase-1 comparison on GitHub's runners, on the small rooms of the shipped game; they show that at the game's real sizes Hazel adds a few milliseconds per event, and that the large maps of this report are where it stops fitting a 16 ms frame.</p>

<h2 id="fix">What would fix it</h2>
<h3>In the game's rules, available today</h3>
<ol>
<li><b>Drop type annotations on recursive helpers</b> (World's <code>find</code>, Square's <code>find</code> and <code>doors</code>): 153 to 22.6 ms at 16x16; linear instead of quadratic.</li>
<li><b>Pass only what the rule needs</b>: the neighbouring cells, not the map. Flat at about 0.9 ms at every size. All 17 <code>Globals</code> fields go to every room today, and each is converted and re-stepped per call.</li>
</ol>
<h3>In Hazel's library and evaluator</h3>
<ol>
<li><b>Do not re-step a converted value.</b> Have <code>of_js</code> produce something the evaluator treats as final (or bind the argument in the environment and apply to a variable). About half the floor.</li>
<li><b>An ascription fast path.</b> Check that a value conforms to a type without allocating, or skip the run-time <code>Asc</code> when the argument's type already equals the parameter's, which is exactly the recursive <code>find(rest, ...)</code> case. This makes the annotated rule linear without changing it.</li>
<li><b>A cheaper <code>Id.mk</code></b>, without <code>Uuidm.v4</code>'s byte copy under js_of_ocaml: about a fifth of all time.</li>
<li><b>Cut the per-step pipeline when nothing uses it</b>: the state merge, reuse check and probe sampling run on every step even with no probes and no reuse (8.1%, 8.0% and 6.8% inclusive in the walk's profile).</li>
</ol>
<p>Fixes 1 and 2 of the library would bring the shipped rule near the unannotated one, and the floor to perhaps a third of today's; fix 4 is what would make a linear walk cheaper. None of them makes Hazel's walk cost what JS's does (under 1 &micro;s); a rule's design still decides whether the call depends on the map's size.</p>

<h2 id="next">What next</h2>
<ol>
<li>Change the World and Square rules on matthewhammer/kids-choice-games#2: no annotations on recursive helpers, and neighbours only in World's <code>Globals</code>; re-time the game's moves at 16x16.</li>
<li>Prototype the ascription fast path in <code>Ascriptions.re</code> and time the shipped rule against this report's numbers.</li>
<li>Prototype <code>of_js</code> producing final values, and time the identity rule's floor.</li>
<li>Measure the noise floor: repeat the 16x16 row five times.</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>Node v22.23.2 on the Ubuntu laptop (Intel i7), one process at a time. The library is hazel-lib.js from <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> at <code>0d66c36618</code>: the minified build for every time, the dev build <code>hazelLib.bc.js</code> for named profiles (3 s each). The rules are the game's at <code>2ebda59ab4</code>. Each time is one p50 over 20-60 reps after warm-up; the noise floor was not measured, so treat differences under about 10% as noise. The target cell is mid-map, at (n/2-1, n/2), moving east; every variant's result was checked against the game's World handler. The library exposes no step count, so per-step costs are inferred from timings. The drivers are in <code>drivers/</code> (<code>r25.mjs</code> for the sizes, <code>steps.mjs</code>, <code>profheld.mjs</code>, and the earlier <code>prof.mjs</code> and <code>prof_noann.mjs</code>; they read the game and library from local checkouts); the data is in <a href="https://github.com/matthewhammer/hazel-reports/tree/main/025/data"><code>data/</code></a>, and the profiles, too big to keep, are summarized in <code>data/profiles.json</code>.</p>
</main></body></html>
"""
open(OUT, "w").write(PAGE)
print("wrote", OUT)
