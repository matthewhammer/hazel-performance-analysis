#!/usr/bin/env python3
"""Writes 027/index.html, ^report(27): the World rule in Hazel at its best and in Fumola (wasm), 3x3 to 64x64 (^ticket(542)).
Data: data/fumola_{1,2}.json (drivers/measure.mjs), data/data_hazel_best_{1,2}.json (025/drivers/r25.mjs on trial/r25-best),
and ^report(25)'s measured build, before the PRs (025/data/prs/data_base_*.json, to 24x24)."""
import os, json, glob, math, html
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE)
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
esc = html.escape
def rounds(pat):
    rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(R, pat)))]
    out = {}
    for i, r0 in enumerate(rs[0]):
        row = {"n": r0["n"], "cells": r0["cells"]}
        for k, v in r0.items():
            if isinstance(v, (int, float)) and k not in ("n", "cells"): row[k] = sum(r[i][k] for r in rs) / len(rs)
        out[r0["cells"]] = row
    return out, len(rs)
FU, fu_rounds = rounds("data/fumola_*.json")
HB, hb_rounds = rounds("data/data_hazel_best_*.json")
H0, _ = rounds("../025/data/prs/data_base_*.json")
fmt = lambda v: "–" if v is None else (f"{v:.3g}" if v < 100 else f"{v:,.0f}")
slope = lambda D, k, a, b: math.log(D[b][k] / D[a][k]) / math.log(b / a)
SERIES = [  # (data, key, label, colour, dashed)
 (H0, "shipped", "Hazel before the PRs: the map passed", "var(--muted)", True),
 (HB, "shipped", "Hazel at its best: the map passed", "var(--bad)", False),
 (HB, "held", "Hazel at its best: the map held", "var(--accent2)", False),
 (HB, "near", "Hazel at its best: neighbours passed", "var(--good)", False),
 (FU, "passed", "Fumola: the map passed", "var(--bad)", True),
 (FU, "held_list", "Fumola: the map held, a list", "var(--accent2)", True),
 (FU, "held_map", "Fumola: the map held, a HashMap", "var(--accent)", True),
 (FU, "near", "Fumola: neighbours passed", "var(--good)", True),
]
def fig_lines(w=700, h=380):
    L, Rr, T, B = 58, 250, 14, 40
    x0, x1 = math.log10(7), math.log10(5000); y0, y1 = math.log10(0.2), math.log10(1000)
    X = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (w - L - Rr)
    Y = lambda v: h - B - (math.log10(max(v, 0.2)) - y0) / (y1 - y0) * (h - T - B)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Time per World call against map size, log scales, Hazel at its best (solid) and Fumola (dashed); Fumola with the map held in a HashMap stays near 0.5 ms from 3x3 to 64x64." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for v in [1, 10, 100, 1000]:
        o.append(f'<line x1="{L}" x2="{w-Rr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" style="stroke:var(--line)"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end" style="fill:var(--muted)">{v} ms</text>')
    for c in sorted(FU):
        n = int(round(math.sqrt(c)))
        if n in (3, 8, 16, 32, 64): o.append(f'<text x="{X(c):.1f}" y="{h-B+16}" text-anchor="middle" style="fill:var(--muted)">{n}x{n}</text>')
    o.append(f'<text x="{(L+w-Rr)/2}" y="{h-6}" text-anchor="middle" style="fill:var(--muted)">map size (cells, log scale)</text>')
    labels = []
    for D, k, name, col, dash in SERIES:
        pts = [(c, D[c][k]) for c in sorted(D) if k in D[c]]
        if not pts: continue
        o.append(f'<polyline points="{" ".join(f"{X(c):.1f},{Y(v):.1f}" for c, v in pts)}" fill="none" style="stroke:{col}" stroke-width="2.2"{" stroke-dasharray=\"6 4\"" if dash else ""}/>')
        for c, v in pts: o.append(f'<circle cx="{X(c):.1f}" cy="{Y(v):.1f}" r="2.6" style="fill:{"var(--bg)" if dash else col};stroke:{col}"/>')
        labels.append([Y(pts[-1][1]) + 4, X(pts[-1][0]) + 8, f"{fmt(pts[-1][1])} ms {name}", col])
    labels.sort()
    for i in range(1, len(labels)):
        if labels[i][0] - labels[i-1][0] < 13: labels[i][0] = labels[i-1][0] + 13
    for y, x, t, col in labels: o.append(f'<text x="{x:.1f}" y="{y:.1f}" style="fill:{col}">{esc(t)}</text>')
    o.append('</svg>'); return "".join(o)
def tr(cells): return "<tr>" + "".join(f"<td class=n>{c}</td>" if i else f"<td>{c}</td>" for i, c in enumerate(cells)) + "</tr>"
COLS = [(H0, "shipped"), (HB, "shipped"), (HB, "noann"), (HB, "held"), (HB, "near"), (FU, "passed"), (FU, "held_list"), (FU, "held_map"), (FU, "near"), (FU, "held_map_steps")]
size_rows = "".join(tr([f'{int(math.sqrt(c))}x{int(math.sqrt(c))} ({c})'] + [fmt(D[c][k]) if c in D and k in D[c] else "–" for D, k in COLS]) for c in sorted(FU))
open(os.path.join(R, "data", "summary.json"), "w").write(json.dumps({"fumola_rounds": fu_rounds, "hazel_rounds": hb_rounds}, indent=1))
# ---------- the code: Fumola's World rule and its held versions, with light highlighting
import re
FKW = {"func", "let", "var", "switch", "case", "if", "else", "for", "in", "null", "and", "or", "not", "true", "false"}
def hl(src):
    out, i = [], 0
    for m in re.finditer(r'(?P<c>//[^\n]*)|(?P<s>"[^"\n]*")|(?P<n>\b\d+\b)|(?P<v>#[A-Za-z]+)|(?P<w>[A-Za-z_][A-Za-z_0-9]*)', src):
        out.append(esc(src[i:m.start()])); t = m.group(0)
        cls = "tk-c" if m.group("c") else "tk-s" if m.group("s") else "tk-n" if m.group("n") else "tk-t" if m.group("v") or (m.group("w") and t in ("HashMap",)) else "tk-k" if t in FKW else None
        out.append(f'<span class="{cls}">{esc(t)}</span>' if cls else esc(t)); i = m.end()
    out.append(esc(src[i:])); return "".join(out)
WORLD = open(os.path.join(HERE, "world.fum")).read()
HELD = open(os.path.join(HERE, "held.fum.js")).read()
HELD = HELD[HELD.index("`") + 1:HELD.rindex("`")].replace("${cells}", "[ ...every cell, as written for a passed call... ]")
P = lambda c: FU[c]; Hb = lambda c: HB[c]
f64, h64, h24, f24 = FU[4096], HB[4096], H0[576], FU[576]
x = lambda a, b: f"{a / b:.0f}x" if a / b >= 10 else f"{a / b:.1f}x"
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The World Rule in Hazel and in Fumola</title>
<meta name="description" content="Dress Up's World rule in Hazel at its best and in Fumola (wasm), 3x3 to 64x64: Fumola with the world held in a HashMap answers in about 0.5 ms and 450 steps at every size; passed or walked, both grow with the map.">
<style>{STYLE}
pre.code .tk-k {{ color: var(--accent); font-weight: 600; }} pre.code .tk-t {{ color: var(--accent2); }} pre.code .tk-s {{ color: var(--good); }} pre.code .tk-n {{ color: var(--warn); }} pre.code .tk-c {{ color: var(--muted); font-style: italic; }}
pre.code {{ white-space: pre-wrap; font-size: 0.84em; }}
</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>27<b>)</b></code> · performance · started 2026-10-22 · <span class="wip">work in progress</span> · about 7 minutes to read</p>
<h1>The World Rule in Hazel and in Fumola</h1>
<p class="sub">Matthew, after <a href="../025/">^report(25)</a>: <q>do the same game logic that we've exported to Hazel in report 25, but now do a Hazel (best PRs for performance) against Fumola in Wasm, doing the same logic ... I especially want to compare the map-based version in Fumola (store world data in maps, not lists) --- so there's a chance at O(log N).</q> This is the World room's rule (a step to the square beside), written in Fumola, and timed against Hazel with every performance change we have, at map sizes from 3x3 to 64x64 (<code class="ref"><b>^ticket(</b>542<b>)</b></code>). The syntax of the two side by side is <a href="../028/">^report(28)</a>.</p>

<div class="headline">
<p><b>Short answers.</b> Node on the Ubuntu laptop, one process at a time, the median call, the mean of two rounds; every answer checked against the game's.</p>
<ol class="ans">
<li><b>Fumola with the world held in a HashMap is flat: about {fmt(f64["held_map"])} ms and {f64["held_map_steps"]:.0f} steps a call at 64x64, the same as at 3x3.</b> The map is built once, when the world changes ({fmt(f64["setup_ms"])} ms at 64x64), and each move passes four numbers and a direction and looks up one square. Fumola's <code>HashMap</code> is a persistent hash trie, O(log₃₂ N), constant at these sizes. That meets the goal set in <a href="../025/#next">^report(25)'s next steps</a>: O(1) or O(log N) in the world's size.</li>
<li><b>Hazel has no map to do the same.</b> Its best here walks a list: {fmt(h64["held"])} ms at 64x64 with the world held in a closure, {fmt(h64["shipped"])} ms passed in. Against Fumola's held map, that is {x(h64["held"], f64["held_map"])} and {x(h64["shipped"], f64["held_map"])}.</li>
<li><b>Like for like, Fumola is faster on every version that grows.</b> At 64x64, passing the whole map: {fmt(f64["passed"])} ms against Hazel's {fmt(h64["shipped"])} ({x(h64["shipped"], f64["passed"])}). Holding it as a list and walking it: {fmt(f64["held_list"])} ms against {fmt(h64["held"])} ({x(h64["held"], f64["held_list"])}).</li>
<li><b>With only the neighbours passed, the two are the same: about 1 ms, at every size</b> ({fmt(f64["near"])} and {fmt(h64["near"])} ms at 64x64). There the call boundary is all there is.</li>
<li><b>The boundaries differ.</b> Hazel's library converts JS values into Hazel's. Fumola's wasm build takes only source text, so a passed map is written out and parsed every call: {f64["passed_chars"]:,.0f} characters at 64x64, most of its {f64["passed_steps"]:,.0f} steps. Holding the world in the instance avoids that, in either language.</li>
</ol>
</div>

<figure class="fig" id="fig-sizes">{fig_lines()}<figcaption><b>Figure 1.</b> One World call against the map's size, both scales logarithmic. Solid: Hazel at its best. Dashed: Fumola, and Hazel before the PRs (grey, to 24x24, from <a href="../025/">^report(25)</a>). Colour is how the world reaches the rule: passed in (red), held as a list (teal), held in a HashMap (violet), only the neighbours (green). Values from <code>data/</code>.</figcaption></figure>

<h2 id="builds">What was measured</h2>
<ul>
<li><b>Hazel at its best:</b> its JS library built by GitHub from <code>trial/r25-best</code> (<code>bce9b4e5d1</code>): <a href="../025/#prs">all 14 performance PRs</a>, #2681's memo limited to depth 1 (<a href="https://github.com/hazelgrove/hazel/pull/2681#issuecomment-6344616722">proposed</a>), and the library binding a call's argument in the environment (<code class="ref"><b>^ticket(</b>539<b>)</b></code>). Timed with <a href="../025/#code">^report(25)'s driver and rules</a>: <i>passed</i> is the shipped rule, <i>held</i> the map held in a closure, <i>neighbours</i> the neighbours-only rule.</li>
<li><b>Fumola:</b> its wasm build (<code>fumola_wasm_bg.wasm</code>, from <code>667a34d</code>), in node through <code>initSync</code>, one instance per size. The rules are below; each call is <code>fumola_eval_top</code> of a call written as text, its answer read back from JSON and checked.</li>
</ul>

<h2 id="code">The Fumola rules</h2>
<p>The World rule, as the game's Hazel one reads (<a href="../028/#world">both, side by side</a>): a step in a direction, the square there found, and a <code>GoSquare</code> if it has a way back. <code>step</code> stays in Nat: it checks an edge before stepping off it, since Fumola keeps Nat and Int apart (<a href="../028/#traps">^report(28)'s traps</a>).</p>
<pre class="code">{hl(WORLD)}</pre>
<p>The held versions: the world bound once in the instance, as a list (<code>wl</code>) and as a HashMap keyed by <code>(col, row)</code> (<code>wm</code>). A move passes four numbers and a direction.</p>
<pre class="code">{hl(HELD)}</pre>

<h2 id="numbers">The numbers</h2>
<div class="scroll"><table><tr><th>map (cells)</th><th>Hazel before, passed</th><th>Hazel best, passed (shipped)</th><th>Hazel best, passed (unannotated)</th><th>Hazel best, held</th><th>Hazel best, neighbours</th><th>Fumola, passed</th><th>Fumola, held list</th><th>Fumola, held map</th><th>Fumola, neighbours</th><th>Fumola, held map: steps</th></tr>{size_rows}</table></div>
<p class="note">ms per call, the median of each round, the mean of {hb_rounds} rounds (Hazel) and {fu_rounds} (Fumola). Growth exponents from 64 to 4,096 cells (1 is linear, 0 flat): Hazel best passed {slope(HB, "shipped", 64, 4096):.2f}, held {slope(HB, "held", 64, 4096):.2f}, neighbours {slope(HB, "near", 64, 4096):.2f}; Fumola passed {slope(FU, "passed", 64, 4096):.2f}, held list {slope(FU, "held_list", 64, 4096):.2f}, held map {slope(FU, "held_map", 64, 4096):.2f}, neighbours {slope(FU, "near", 64, 4096):.2f}.</p>

<h2 id="hazel-map">What Hazel would need</h2>
<p>For the world's size to leave a move's cost alone, the rule must find a square without walking to it. Hazel's rules have lists and records, and no map. Three ways there:</p>
<ol>
<li><b>Pass only what the rule reads</b>: the neighbours. Flat today, in both languages (answer 4), but the game must know what each rule reads.</li>
<li><b>A map in Hazel, written in Hazel</b>: a balanced tree keyed by <code>(col, row)</code>, held as the world is held now. O(log N) evaluator steps a lookup. An estimate, not measured: a 64x64 world is twelve levels deep, and at a few dozen steps a level and about 3 µs a step (<a href="../025/#t-steps-prs">^report(25)</a>), a lookup would cost about a millisecond, at any size near this one.</li>
<li><b>A map built in</b>, as Fumola's <code>HashMap</code> is a primitive over a persistent hash trie: one step a lookup.</li>
</ol>
<p>That is <code class="ref"><b>^ticket(</b>540<b>)</b></code>'s question, every handler in O(1) or O(log N), now with a measured target.</p>

<h2 id="next">What next</h2>
<ol>
<li>Look at the game playing under Fumola: every room's rules are now in Fumola in <a href="https://github.com/matthewhammer/kids-choice-games/pull/4">matthewhammer/kids-choice-games#4</a> (a draft on top of #2), with <code>?logic=fumola</code> (the world held in a HashMap, rebuilt when its cells change) and <code>?logic=fumola-list</code> (the map passed in). A node check compares its answers with the Hazel rules' on 20,653 cases, and GitHub's browser checks pass (run 39823022799, its only failures the same nine as its base's). One run on GitHub's computer, for the order of things only: a rule call, median, 2.9 ms in Hazel, 1.1 ms in Fumola with the map held and 1.4 ms with it passed in; Fumola defines its rules in 4 ms, where Hazel compiles in 514 ms. Fumola's modes are not in the speed probe yet.</li>
<li>A map for Hazel's rules (above), and the World rule timed with it.</li>
<li>Fumola's boundary without source text: a JSON value in as a Fumola value, so a passed map is not parsed every call.</li>
<li>The same comparison in the game, in GitHub's browsers.</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>Node v22 on the Ubuntu laptop (Intel i7), one process at a time, pinned to two threads and niced. Fumola: <code>drivers/measure.mjs</code> (<code>world.fum</code>, <code>held.fum.js</code>), per size a fresh instance, three warm-up calls, then up to 60 timed (stopping after 2.5 s and at least 9), the median; its answer checked against the game's (<code>GoSquare(c + 1, r, "W", Done)</code>). Hazel: <code>025/drivers/r25.mjs</code> on <code>trial/r25-best</code>'s library, the same sizes. Two rounds each. The target cell is mid-map, moving east, as in ^report(25).</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE); print("wrote 027/index.html")
