#!/usr/bin/env python3
"""Writes 025/index.html, ^report(25): what a call into Hazel costs.
  python3 025/drivers/gen025.py   (then build.sh runs the series tools)
Figures are inline SVG drawn from 025/data/*.json."""
import json, os, math, re, glob
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
D = lambda f: json.load(open(os.path.join(R, "data", f)))
sizes = D("data_sizes.json"); steps = D("data_steps.json"); early = D("earlier.json")
OUT = os.path.join(R, "index.html")
by = {r["cells"]: r for r in sizes}
r256 = by[256]

# ---------- before and after the performance PRs (drivers/prs.sh: three builds, rounds interleaved)
PRS = D("prs.json")   # the builds and the 14 PRs, by hand
steps_pre, steps_post = D("prs/steps_base.json"), D("prs/steps_b.json")   # one round each
KEYS = ["js_globals", "idU", "idA", "game_World", "shipped", "noann", "index", "near", "held", "held_setup"]
def load_build(b):
    rounds = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(R, "data", "prs", f"data_{b}_*.json")))]
    comp = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(R, "data", "prs", f"compile_{b}_*.json")))]
    rows = []
    for i, r0 in enumerate(rounds[0]):
        row = {"n": r0["n"], "cells": r0["cells"]}
        for k in KEYS:
            vs = [rr[i][k] for rr in rounds]
            row[k] = sum(vs) / len(vs)
            row[k + "_spread"] = (max(vs) - min(vs)) / row[k] if row[k] else 0   # rounds' spread, as a share
        rows.append(row)
    cm = {k: sum(c[k] for c in comp) / len(comp) for k in ("run_ms", "compile_ms")}
    cm.update({k + "_all": [c[k] for c in comp] for k in ("run_ms", "compile_ms")})
    return {"rows": rows, "by": {r["cells"]: r for r in rows}, "compile": cm, "rounds": len(rounds)}
B = {b["key"]: load_build(b["key"]) for b in PRS["builds"]}
BN = {b["key"]: b for b in PRS["builds"]}
pre, mid, post = B["base"]["by"], B["a"]["by"], B["b"]["by"]
# the rounds' spread, every build, variant and size from 6x6 up: the noise floor these runs can claim
spreads = sorted(r[k + "_spread"] for bb in B.values() for r in bb["rows"] if r["cells"] >= 36 for k in KEYS if k != "js_globals")
noise_p90 = spreads[int(0.9 * (len(spreads) - 1))]
fmt = lambda v: f"{v:.3g}" if v < 100 else f"{v:.0f}"
# growth exponent from 64 to 576 cells: 1 is linear, 2 quadratic
slope = lambda rows, k: math.log({r["cells"]: r for r in rows}[576][k] / {r["cells"]: r for r in rows}[64][k]) / math.log(576 / 64)
from datetime import datetime
UPDATED = datetime.now().astimezone().strftime("%H:%M")

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

# ---------- figure 1, before and after: the same lines, dashed for the measured build, solid with all 14 PRs
SERIES = [("shipped", "shipped rule", "var(--bad)"), ("noann", "find unannotated", "var(--warn)"),
          ("held", "map held in a closure", "var(--accent2)"), ("idA", "identity rule (floor)", "var(--accent)"),
          ("near", "neighbours only", "var(--good)")]
def spread_labels(items, gap=13):
    """items: [y, ...] in drawing order -> ys pushed apart by at least gap, in the same order."""
    order = sorted(range(len(items)), key=lambda i: items[i]); ys = list(items)
    for a, b in zip(order, order[1:]):
        if ys[b] - ys[a] < gap: ys[b] = ys[a] + gap
    return ys
def fig_lines_prs(w=660, h=360):
    rows0, rows1 = B["base"]["rows"], B["b"]["rows"]
    L, Rr, T, Bm = 60, 220, 14, 40
    x0, x1 = math.log10(8), math.log10(700); y0, y1 = math.log10(0.3), math.log10(1000)
    X = lambda v: L + (math.log10(v) - x0) / (x1 - x0) * (w - L - Rr)
    Y = lambda v: h - Bm - (math.log10(max(v, 0.3)) - y0) / (y1 - y0) * (h - T - Bm)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Time per call against map size, log scales, before (dashed) and after (solid) the 14 performance PRs. The shipped rule at 24x24: {fmt(rows0[-1]["shipped"])} ms before, {fmt(rows1[-1]["shipped"])} ms after." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    for v in [1, 10, 100, 1000]:
        o.append(f'<line x1="{L}" x2="{w-Rr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" style="stroke:var(--line)"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end" style="fill:var(--muted)">{v} ms</text>')
    for r in rows0:
        o.append(f'<text x="{X(r["cells"]):.1f}" y="{h-Bm+16}" text-anchor="middle" style="fill:var(--muted)">{r["n"]}x{r["n"]}</text>')
    o.append(f'<text x="{(L+w-Rr)/2}" y="{h-6}" text-anchor="middle" style="fill:var(--muted)">map size (cells, log scale)</text>')
    o.append(f'<line x1="{L+8}" x2="{L+34}" y1="{T+6}" y2="{T+6}" style="stroke:var(--muted)" stroke-width="2" stroke-dasharray="5 4"/><text x="{L+40}" y="{T+10}" style="fill:var(--muted)">before: {BN["base"]["long"]}</text>'
             f'<line x1="{L+8}" x2="{L+34}" y1="{T+22}" y2="{T+22}" style="stroke:var(--muted)" stroke-width="2.4"/><text x="{L+40}" y="{T+26}" style="fill:var(--muted)">after: {BN["b"]["long"]}</text>')
    for k, name, col in SERIES:
        for rows, dash, op in ((rows0, ' stroke-dasharray="5 4"', ".55"), (rows1, "", "1")):
            pts = " ".join(f"{X(r['cells']):.1f},{Y(r[k]):.1f}" for r in rows)
            o.append(f'<polyline points="{pts}" fill="none" style="stroke:{col};opacity:{op}" stroke-width="2.2"{dash}/>')
            for r in rows:
                o.append(f'<circle cx="{X(r["cells"]):.1f}" cy="{Y(r[k]):.1f}" r="{2.6 if dash else 3}" style="fill:{"var(--bg)" if dash else col};stroke:{col};opacity:{op}"/>')
    ys = spread_labels([Y(rows1[-1][k]) + 4 for k, _, _ in SERIES])
    for (k, name, col), y in zip(SERIES, ys):
        a, b = rows1[-1][k], rows0[-1][k]
        o.append(f'<text x="{X(rows1[-1]["cells"])+8:.1f}" y="{y:.1f}" style="fill:{col}">{fmt(a)} ms {name} <tspan style="fill:var(--muted)">(was {fmt(b)})</tspan></text>')
    o.append('</svg>')
    return "".join(o)

# ---------- figure 3, before and after: one 16x16 call per variant, three builds
def fig_bars_prs(variants, cells=256, w=660):
    bh, gap, ggap, L = 15, 3, 14, 200
    builds = [("base", ".38"), ("a", ".68"), ("b", "1")]
    h = 30 + len(variants) * (3 * (bh + gap) + ggap)
    mx = max(B[b]["by"][cells][k] for k, _, _ in variants for b, _ in builds)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="One 16x16 call by version of the rule, in three builds: before, with #2681 and #2661, and with all 14 PRs. Shipped rule: {fmt(pre[cells]["shipped"])}, {fmt(mid[cells]["shipped"])} and {fmt(post[cells]["shipped"])} ms." style="width:100%;height:auto;font:12px system-ui,sans-serif">']
    x = 10
    for (b, op), lab in zip(builds, ["before (1 of 14 PRs)", "+ #2681 and #2661 (3 of 14)", "after (all 14)"]):
        o.append(f'<rect x="{x}" y="4" width="12" height="12" rx="2" style="fill:var(--ink);opacity:{op}"/><text x="{x+17}" y="14" style="fill:var(--muted)">{lab}</text>')
        x += 17 + 6.8 * len(lab) + 22
    y = 30
    for k, name, col in variants:
        o.append(f'<text x="{L-8}" y="{y + 1.5*(bh+gap) + 4:.1f}" text-anchor="end" style="fill:var(--ink)">{esc(name)}</text>')
        for b, op in builds:
            v = B[b]["by"][cells][k]; bw = max(2, (w - L - 70) * v / mx)
            o.append(f'<rect x="{L}" y="{y}" width="{bw:.1f}" height="{bh}" rx="2" style="fill:{col};opacity:{op}"/><text x="{L+bw+5:.1f}" y="{y+bh-3}" style="fill:var(--ink)">{fmt(v)} ms</text>')
            y += bh + gap
        y += ggap
    o.append('</svg>')
    return "".join(o)

# ---------- the shipped 16x16 call, split, before and after
def fig_stack_prs(w=380):
    """Drawn for the narrow column beside a short answer: few words, big type."""
    rows = [("before", pre[256]), ("after", post[256])]
    L = 54; W = w - L - 64
    names = [("conversion + ascription", "var(--accent)"), ("the walk", "var(--warn)"), ("the annotation's re-check", "var(--bad)")]
    h = 8 + 34 * len(rows) + 22 * len(names) + 6
    tot0 = rows[0][1]["shipped"]
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="The shipped 16x16 call split into the conversion floor, the walk and the annotation re-check, before ({fmt(pre[256]["shipped"])} ms) and after ({fmt(post[256]["shipped"])} ms) the 14 PRs." style="width:100%;height:auto;font:15px system-ui,sans-serif">']
    for i, (lab, col) in enumerate(names):
        ly = 8 + 34 * len(rows) + 22 * i
        o.append(f'<rect x="{L}" y="{ly}" width="13" height="13" rx="2" style="fill:{col}"/><text x="{L + 19}" y="{ly + 11}" style="fill:var(--muted)">{lab}</text>')
    for j, (lab, r) in enumerate(rows):
        y = 6 + 34 * j
        parts = [r["idA"], max(0, r["noann"] - r["idA"]), max(0, r["shipped"] - r["noann"])]
        o.append(f'<text x="{L-7}" y="{y+18}" text-anchor="end" style="fill:var(--ink)">{lab}</text>')
        x = L
        for v, (_, col) in zip(parts, names):
            bw = W * v / tot0
            o.append(f'<rect x="{x:.1f}" y="{y}" width="{bw:.1f}" height="24" style="fill:{col}"/>')
            x += bw
        o.append(f'<text x="{x+6:.1f}" y="{y+18}" style="fill:var(--ink);font-weight:600">{fmt(r["shipped"])} ms</text>')
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

def tr(cells): return "<tr>" + "".join(f"<td class=n>{c}</td>" if i else f"<td>{c}</td>" for i, c in enumerate(cells)) + "</tr>"

# ---------- the rules behind each line: drivers/r25.mjs's own text, with its hot spots marked
# ⟪kind|text⟫ marks a hot spot: bad (the annotation's re-check), warn (the walk), floor (the call boundary),
# held (converted once), good (the neighbours alone). Kinds match the figures' colours.
HS = {"bad": ("var(--bad)", "the annotation re-checks the rest of the list at every step: quadratic before #2681"),
      "warn": ("var(--warn)", "the walk over the cells: linear in the map"),
      "floor": ("var(--accent)", "the call boundary: the whole argument converted, re-stepped and checked against its type, every call"),
      "held": ("var(--accent2)", "the map converted once, at setup, and held in a closure"),
      "good": ("var(--good)", "only the neighbours: at most nine cells, whatever the map's size")}
HZ_KW = {"let", "in", "fun", "case", "end", "if", "then", "else", "type", "module", "true", "false"}
JS_KW = {"const", "let", "new", "return", "await", "async", "function", "true", "false"}
def hl(text, lang):
    """syntax highlighting of plain code text: keywords, constructors and types, strings, numbers, comments"""
    kw = HZ_KW if lang == "hz" else JS_KW
    tok = (r'(?P<c>#[^#\n]*#)|' if lang == "hz" else r'(?P<c>//[^\n]*)|') + r'(?P<s>"[^"\n]*")|(?P<n>\b\d+(?:\.\d+)?\b)|(?P<w>[A-Za-z_][A-Za-z_0-9]*)'
    out, i = [], 0
    for m in re.finditer(tok, text):
        out.append(esc(text[i:m.start()])); t = m.group(0)
        if m.group("c"): out.append(f'<span class="tk-c">{esc(t)}</span>')
        elif m.group("s"): out.append(f'<span class="tk-s">{esc(t)}</span>')
        elif m.group("n"): out.append(f'<span class="tk-n">{esc(t)}</span>')
        elif t in kw: out.append(f'<span class="tk-k">{esc(t)}</span>')
        elif lang == "hz" and t[0].isupper(): out.append(f'<span class="tk-t">{esc(t)}</span>')
        else: out.append(esc(t))
        i = m.end()
    out.append(esc(text[i:]))
    return "".join(out)
def code(src, lang="hz"):
    out, i = [], 0
    for m in re.finditer(r"⟪(\w+)\|(.*?)⟫", src, re.S):
        out.append(hl(src[i:m.start()], lang)); out.append(f'<span class="hs hs-{m.group(1)}" title="{esc(HS[m.group(1)][1])}">{hl(m.group(2), lang)}</span>'); i = m.end()
    out.append(hl(src[i:], lang))
    return "".join(out)
from listings_fmt import TILE_PREAMBLE, SHARED, MK, SHIPPED, NOANN, INDEX, HELD, IDA, NEAR, NTHU, FINDU   # laid out on more lines (listings_fmt.py)

JS_MAP = """const g = globalsOf(map, n, ac, ar);   // ⟪floor|all 17 fields; cells: n × n records {col, row, kind, ways}⟫
const ev = { tag: "Way", value: "E" };
V.{k}(g, ev)"""
LISTINGS = [
 ("shipped", "shipped rule", "var(--bad)", SHIPPED, JS_MAP.replace("{k}", "shipped"),
  "The driver's copy of the game's World rule: the game keeps <code>find</code> beside <code>on_event</code> and names <code>Common.dir</code> and <code>Common.opp</code> (its own text is folded below); here the lookup is passed to <code>mk</code>. The logic is the same, and the two times agree within noise above 8x8. Three costs stack: the boundary converts the whole map, the walk goes to the target, and the annotation on <code>findA</code> makes every step of the walk re-check the rest of the list."),
 ("noann", "find unannotated", "var(--warn)", NOANN, JS_MAP.replace("{k}", "noann"),
  "The same rule without the annotation on its helper: the walk is linear again. What #2681 gives the shipped rule without changing it."),
 ("index", "index arithmetic", "var(--warn)", INDEX, JS_MAP.replace("{k}", "index"),
  "Goes straight to the target's position, <code>r * cols + c</code>, with no comparison per cell; still a walk down the list to get there."),
 ("held", "map held in a closure", "var(--accent2)", HELD, """const hf = V.held(⟪held|g.cells⟫);   // once: the map converted into a Hazel closure
hf({ at_col: ac, at_row: ar, cols: n, rows: n }, ev)   // each event: four numbers""",
  f"The map crosses the boundary once, into a closure ({fmt(pre[256]['held_setup'])} ms at 16x16, once); each event passes four numbers. The walk remains, and the held list is still re-stepped when it is substituted into the call."),
 ("idA", "identity rule (floor)", "var(--accent)", IDA, JS_MAP.replace("{k}", "idA"),
  "Ignores its argument: what is left is the boundary alone, converting the whole map and checking it against <code>(Globals, Event)</code>. Every rule that is passed the map pays at least this."),
 ("near", "neighbours only", "var(--good)", NEAR, """const nb = { at_col: ac, at_row: ar, cols: n, rows: n,
  ⟪good|near: g.cells.filter(x => Math.abs(x.col - ac) <= 1 && Math.abs(x.row - ar) <= 1)⟫ };   // at most 9 cells
V.near(nb, ev)""",
  "The same decision, given only the squares around the player: JS picks the at most nine neighbours before the call, so the argument, the walk and the check are all small, and the cost does not grow with the map."),
]
def listing(k, name, col, hz, js, note):
    return (f'<div class="listing" id="code-{k}"><div class="lh"><span class="sw" style="background:{col}"></span><b>{name}</b>'
            f'<span class="ms">16x16: {fmt(pre[256][k])} ms before, {fmt(post[256][k])} ms after</span></div>'
            f'<pre class="code">{code(hz)}</pre>'
            f'<div class="tiles" data-k="{k}"><div class="tiles-note">Hazel\'s tile editor, read only: the same code, with what it needs before it (the program\'s types and the helpers), from hazel.org\'s build of <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a>. <button type="button" class="tiles-go">▶ show Hazel\'s tiles</button> <span class="tiles-phase"></span></div></div>'
            f'<div class="runbox" data-k="{k}"><div class="rb-row"><b>Run it</b> on a map of grass, the player mid-map, going east: '
            f'<select aria-label="the map\'s size"><option value="3">3x3</option><option value="8" selected>8x8</option><option value="16">16x16</option></select> '
            f'<button type="button">▶ run, with Hazel\'s JS library</button></div><pre class="rb-out">Hazel\'s library (hazel.org\'s build of #2719, the tiles\' build) loads on the first run.</pre></div>'
            f'<pre class="code js">{code(js, "js")}</pre><p class="note">{note}</p>'
            + (f'<details><summary>the game\'s own World rule (<code>dress-up/js/25-scripting.js</code> at <code>2ebda59ab4</code>, as the game compiles it)</summary><pre class="code">{code(GAME_WORLD)}</pre></details>' if k == "shipped" else "")
            + '</div>')
GAME_WORLD = """# Places with no way out on a side, whatever their ways say: the waterfall's N, its cliff. #
let no_way = fun (kind, d) : (String, String) -> kind == "waterfall" && d == "N";
let find = fun (cs, c, r) ⟪bad|: ([Cell], Int, Int)⟫ -> case cs | [] => None | x :: rest => if x.col == c && x.row == r then Some(x) else ⟪warn|find(rest, c, r)⟫ end;
# A way out walked through: into the square beside it, coming in from the side facing back, #
# if that square is on the map and has a way back; else nowhere. #
let on_event = ⟪floor|fun (g, e) : (Globals, Event)⟫ ->
  case e
  | Way(d) =>
    let (dx, dy) = Common.dir(d) in
    let c = g.at_col + dx in
    let r = g.at_row + dy in
    let back = Common.opp(d) in
    if c < 0 || r < 0 || c >= g.cols || r >= g.rows then Done
    else (case ⟪warn|find(g.cells, c, r)⟫
      | Some(x) => if Common.member(back, x.ways) && !no_way(x.kind, back) then GoSquare(c, r, back, Done) else Done
      | None => Done
      end)
  | _ => Done
  end"""
# ---------- each listing as a program for Hazel's tile editor (its embed, read only): the game's preamble, the helpers the
# listing needs, the listing itself, then the function it makes; drivers/tiles_check.mjs checks each with the library
PREAMBLE_TXT = open(os.path.join(HERE, "preamble.hz")).read()
_body = open(os.path.join(HERE, "r25.mjs")).read()
_line = lambda start: next(l for l in _body.split("\n") if l.startswith(start))
HELPERS_FMT = [SHARED[SHARED.index("let no_way"):]]   # the helpers, laid out as the shared box shows them
plain = lambda src: re.sub(r"⟪\w+\|(.*?)⟫", r"\1", src, flags=re.S)
def tile_program(k, hz):
    t = plain(hz).rstrip()
    last = t.split("\n")[-1]
    t = t + "\n" + {"shipped": "shipped", "noann": "noann", "index": "index", "held": "held", "idA": "idA", "near": "near"}[k]
    need = [SHARED.split("type Event =")[0].split("type Cell =")[0]] if False else []
    need = HELPERS_FMT + ([NTHU] if k == "held" else []) + ([FINDU] if k == "near" else [])
    return "\n".join([TILE_PREAMBLE.rstrip(), *([] if k == "idA" else need), t])
TILES = {L[0]: tile_program(L[0], L[3]) for L in LISTINGS}
json.dump(TILES, open(os.path.join(R, "data", "tiles.json"), "w"), indent=1)
LIST_HTML = "".join(listing(*L) for L in LISTINGS)
RUNBOX_JS = open(os.path.join(HERE, "runbox.js")).read().replace("if (typeof module !== \"undefined\") module.exports = RUNBOX;", "")
HS_LEGEND = "".join(f'<span class="hs hs-{k}">{esc(v[1].split(":")[0])}</span> ' for k, v in HS.items())
LIST_CSS = """
.hs { border-radius: 3px; padding: 0 1px; }
.hs-bad { background: color-mix(in srgb, var(--bad) 24%, transparent); box-shadow: inset 0 -2px var(--bad); }
.hs-warn { background: color-mix(in srgb, var(--warn) 24%, transparent); box-shadow: inset 0 -2px var(--warn); }
.hs-floor { background: color-mix(in srgb, var(--accent) 20%, transparent); box-shadow: inset 0 -2px var(--accent); }
.hs-held { background: color-mix(in srgb, var(--accent2) 22%, transparent); box-shadow: inset 0 -2px var(--accent2); }
.hs-good { background: color-mix(in srgb, var(--good) 22%, transparent); box-shadow: inset 0 -2px var(--good); }
.hslegend .hs { display: inline-block; margin: 2px 6px 2px 0; padding: 1px 6px; font-size: 0.86em; }
.listing { border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px 2px; margin: 14px 0; background: var(--bg); }
.listing .lh { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.listing .sw { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
.listing .ms { color: var(--muted); font-size: 0.9em; margin-left: auto; }
.listing pre.code { white-space: pre-wrap; word-break: break-word; font-size: 0.84em; margin: 8px 0; }
.listing pre.code.js { border-style: dashed; }
.gamepics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; align-items: start; }
.gamepics img { width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--line); display: block; }
.gamepics > div { display: grid; gap: 8px; }
@media (max-width: 640px) { .gamepics { grid-template-columns: 1fr; } }
.tiles { border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; margin: 8px 0; background: var(--paper); }
.tiles-note { color: var(--muted); font-size: 0.82em; }
.runbox { border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; margin: 8px 0; }
.runbox .rb-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; font-size: 0.9em; }
.runbox button, .runbox select { font: inherit; padding: 2px 8px; border-radius: 6px; border: 1px solid var(--line); background: var(--paper); color: var(--ink); cursor: pointer; }
.runbox .rb-out { margin: 6px 0 2px; white-space: pre-wrap; font-size: 0.84em; color: var(--muted); }
.runbox .rb-out b { color: var(--ink); }
.tiles-frame { width: 100%; height: 120px; border: 0; display: block; margin-top: 6px; border-radius: 6px; background: #fff; }
pre.code .tk-k { color: var(--accent); font-weight: 600; } pre.code .tk-t { color: var(--accent2); }
pre.code .tk-s { color: var(--good); } pre.code .tk-n { color: var(--warn); } pre.code .tk-c { color: var(--muted); font-style: italic; }
"""
cm = {b: B[b]["compile"] for b in B}
pc = lambda a, b: f"{round(100 * (1 - b / a))}%"   # how much less b is than a
x_ = lambda a, b: f"{a / b:.1f}x"
VARIANTS = [("shipped", "shipped rule", "var(--bad)"), ("noann", "find unannotated", "var(--warn)"), ("index", "index arithmetic", "var(--warn)"),
            ("held", "map held in a closure", "var(--accent2)"), ("idA", "identity rule (floor)", "var(--accent)"), ("near", "neighbours only", "var(--good)")]
FP1 = fig_lines_prs(); FP3 = fig_bars_prs(VARIANTS); FPS = fig_stack_prs()
def pr_link(n): return f'<a href="https://github.com/hazelgrove/hazel/pull/{n}">#{n}</a>'
pr_rows = "".join(tr([pr_link(p["pr"]), p["what"], p["state"], "yes" if "base" in p["in"] else "no", p["reaches"], p["why"]]) for p in PRS["prs"])
ba_cols = [("shipped", "shipped"), ("noann", "unannotated"), ("idA", "identity"), ("held", "held"), ("near", "neighbours")]
ba_rows = "".join(tr([f'{r["n"]}x{r["n"]} ({r["cells"]})'] + [x for k, _ in ba_cols for x in ([fmt(pre[r["cells"]][k]), fmt(mid[r["cells"]][k]), fmt(post[r["cells"]][k])] if k == "shipped" else [fmt(pre[r["cells"]][k]), fmt(post[r["cells"]][k])])]) for r in B["base"]["rows"])
ba_head = "<tr><th rowspan=2>map (cells)</th>" + "".join(f'<th colspan={3 if k == "shipped" else 2}>{n}</th>' for k, n in ba_cols) + "</tr><tr>" + "".join("<th>before</th><th>+ #2681</th><th>after</th>" if k == "shipped" else "<th>before</th><th>after</th>" for k, _ in ba_cols) + "</tr>"
# ---------- ^ticket(535): why #2681 raises the floor, and the depth-limited memo (drivers/floor.sh)
dd = B["d"]["by"]
FL = lambda f: json.load(open(os.path.join(R, "data", "floor", f)))
def counts(build, k, n="16x16"):
    """(memo, type-hash cache) counts of one call: the memo is the WeakMap with the most writes."""
    xs = FL(f"floor_count_{build}.json")[n][k]
    memo = max(xs, key=lambda x: x["set"]); th = [x for x in xs if x is not memo]
    return memo, (th[0] if th else {"get": 0, "hit": 0, "set": 0})
cnt = {(b, k): counts(b, k) for b in ("a", "d") for k in ("idA", "shipped")}
cnt_rows = "".join(tr([f'{name}, {lab}', f'{cnt[(b, k)][0]["get"]:,}', f'{cnt[(b, k)][0]["hit"]:,}', f'{cnt[(b, k)][0]["set"]:,}', f'{cnt[(b, k)][1]["get"]:,}'])
                   for k, name in (("idA", "identity rule"), ("shipped", "shipped rule")) for b, lab in (("a", "#2681"), ("d", "depth-limited")))
fl = {b: [FL(f"floor_plain_{b}_{r}.json") for r in (1, 2, 3)] for b in ("base", "a", "d")}
flm = lambda b, n, k: sum(x[n][k] for x in fl[b]) / len(fl[b])
flg = lambda b, n, k: sum(x[n]["gc_ms_per_call"][k] for x in fl[b]) / len(fl[b])
noset = [FL(f"floor_noset_a_{r}.json") for r in (1, 2)]
fl_rows = "".join(tr([lab, fmt(pre[c][k]), fmt(mid[c][k]), fmt(dd[c][k]), fmt(flm("base", n, k)), fmt(flm("a", n, k)), fmt(flm("d", n, k))])
                  for k, kn in (("idA", "identity rule"), ("shipped", "shipped rule")) for c, n in ((256, "16x16"), (576, "24x24")) for lab in [f"{kn}, {n}"])
TESTS_D = BN["d"].get("tests", "the full tests were still running at this writing")

# ---------- the woods on #2635 (trial/2635-memo-depth, .github/workflows/picview.yml): three runners, 21 runs each
WOODS_DIR = os.path.join(R, "data", "floor", "picview_a1e0189045")
SETTINGS = [("off", "off"), ("depth1", "depth 1"), ("depth2", "depth 2"), ("depth3", "depth 3"), ("full", "whole")]
def woods_runner(path):
    """{"cpu": ..., ("A"|"B"|"view", setting): {"min", "p25", "median"}} from one runner's picview.txt"""
    out = {}
    for line in open(path):
        if line.startswith("Model name:"): out["cpu"] = line.split(":", 1)[1].strip()
        m = re.match(r"PICVIEW (A|B) (\w+): .* ms; (.*)$", line) or re.match(r"PICVIEW (view) (\w+) \(B - A\): (.*?); results", line)
        if m: out[(m.group(1), m.group(2))] = {k: float(v) for k, v in (kv.split(" ") for kv in m.group(3).split(", "))}
    return out
woods = [woods_runner(os.path.join(WOODS_DIR, f"runner_{i}.txt")) for i in (1, 2, 3)]
kept = lambda w, s, stat="min": (w[("B", "off")][stat] - w[("B", s)][stat]) / (w[("B", "off")][stat] - w[("B", "full")][stat])
woods_rows = "".join(tr([f'{i + 1}: {w["cpu"].replace("AMD EPYC ", "EPYC ").replace(" Processor", "")}'] + [f'{w[("B", s)]["min"]:,.0f}' for s, _ in SETTINGS]
                        + [f'{100 * kept(w, "depth1"):.0f}%']) for i, w in enumerate(woods))
kept_min = sorted(100 * kept(w, "depth1") for w in woods); kept_med = sorted(100 * kept(w, "depth1", "median") for w in woods)
krange = lambda s, stat="min": (lambda v: f"{v[0]:.0f}-{v[-1]:.0f}%")(sorted(100 * kept(w, s, stat) for w in woods))
DB = {k: load_build(k)["by"] for k in ("d2", "d3")}   # depths 2 and 3, this report's driver, two rounds each
depth_rows = "".join(tr([lab, fmt(fl_[256]["idA"]), f'{round(100 * (fl_[256]["idA"] / pre[256]["idA"] - 1)):+d}%', kp]) for lab, fl_, kp in (
    ("no memo (before)", pre, "0%"), ("depth 1", dd, krange("depth1")), ("depth 2", DB["d2"], krange("depth2")),
    ("depth 3", DB["d3"], krange("depth3")), ("whole (#2681)", mid, "100%")))

comp_rows = "".join(tr([BN[b]["label"] + ": " + BN[b]["long"], f'{cm[b]["compile_ms"]:.0f} ({", ".join(f"{v:.0f}" for v in cm[b]["compile_ms_all"])})', f'{cm[b]["run_ms"]:.0f} ({", ".join(f"{v:.0f}" for v in cm[b]["run_ms_all"])})']) for b in ("base", "a", "b"))

bars16 = [("shipped rule", round(r256["shipped"]), "var(--bad)"), ("find unannotated", round(r256["noann"], 1), "var(--warn)"),
          ("index arithmetic, unannotated", round(r256["index"], 1), "var(--warn)"), ("map held in a closure", round(r256["held"], 1), "var(--accent2)"),
          ("identity rule (floor)", round(r256["idA"], 1), "var(--accent)"), ("neighbours only", round(r256["near"], 2), "var(--good)"),
          ("plain JS rule", 0.001, "var(--muted)")]
F1 = fig_lines(); F2 = fig_bars(bars16, aria="16x16 call by variant: shipped 153 ms, unannotated 22.6, index 17.1, held 12.4, identity 9.5, neighbours 0.96, JS under 0.001.")
F3 = fig_stack(); F4 = fig_floor()

cols = ["cells", "js_globals", "idU", "idA", "game_World", "shipped", "noann", "index", "near", "held", "held_setup"]
size_rows = "".join(tr([f'{r["n"]}x{r["n"]} ({r["cells"]})'] + [f'{r[k]:.3g}' for k in cols[1:]]) for r in sizes)
step_rows = "".join(tr([k, v]) for k, v in steps.items())
p2 = early["phase2_node_p50_p95_ms"]

STYLE = open(os.path.join(HERE, "style.css")).read()
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>What a Call into Hazel Costs</title>
<meta name="description" content="Why one Dress Up room rule, run as a Hazel function from JS, takes 40-150 ms on a 16x16 map, and what the open performance PRs do to it: #2681 makes the annotated rule linear ({fmt(pre[256]['shipped'])} to {fmt(mid[256]['shipped'])} ms), and the 14 PRs together halve the compile.">
<style>{STYLE}{LIST_CSS}</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>25<b>)</b></code> · performance · started 2026-10-22, updated 2026-10-22 {UPDATED} MDT · <span class="wip">work in progress</span> · about 11 minutes to read</p>
<h1>What a Call into Hazel Costs</h1>
<p class="sub">Matthew asked, on 2026-10-22, about <code class="ref"><b>^ticket(</b>531<b>)</b></code>, the experiment that moves Messed Up Dress Up's room rules into Hazel modules run through Hazel's JS library (<a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a>, the library; the game's side is the draft matthewhammer/kids-choice-games#2): <q>why is Hazel so slow here for 16 x 16 map? do more analysis please, and draft a new report.</q> The World room's rule takes a step on the map; in the game's own node run it costs 40.0 ms p50 at 16x16, against 0.003 ms for the same rule in JS. This report takes that one call apart.</p>
<p class="sub"><b>Which build.</b> Hazel's JS library, <code>hazel-lib.js</code>, from <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> (branch <code>js-library-embed</code> at <code>0d66c36618</code>), which is #2719 on <a href="https://github.com/hazelgrove/hazel/pull/2711">#2711</a> on <code>dev</code> at <code>962a7cb009</code>. Of the 14 performance PRs on the dashboard it has one, <a href="https://github.com/hazelgrove/hazel/pull/2679">#2679</a>, the only one merged into <code>dev</code>; the other 13 are open. Matthew, after the first draft: <q>Let's make it clear what branch we are measuring ... how many have been applied? If they are not all applied, how much would they help?</q> So every time below is measured three ways, on GitHub's builds of three branches: <b>before</b>, that build; <b>+ #2681</b>, with <a href="https://github.com/hazelgrove/hazel/pull/2681">#2681</a> merged (it carries <a href="https://github.com/hazelgrove/hazel/pull/2661">#2661</a>); and <b>after</b>, with all 14 (<a href="#prs">Before and after the performance PRs</a>).</p>

<div class="headline">
<p><b>Short answers.</b> All times are node on the Ubuntu laptop, p50 of one call with the target cell mid-map, the mean of two interleaved rounds; <i>before</i> is the measured build (1 of 14 PRs), <i>after</i> the same with all 14.</p>
<ol class="ans">
<li><div class="row"><p><b>Most of the time is a type annotation in the rule, and #2681 removes it: {fmt(pre[256]["shipped"])} ms becomes {fmt(mid[256]["shipped"])} ms at 16x16, {x_(pre[256]["shipped"], mid[256]["shipped"])} faster, with the rule unchanged.</b> The rule's recursive helper is written <code>fun (cs, c, r) : ([Cell], Int, Int) -&gt;</code>. Before, Hazel checks that ascription at run time on every call, by walking the value, so each step of the walk re-checks the rest of the list: one linear walk becomes a quadratic one ({fmt(pre[576]["shipped"])} ms at 24x24, against {fmt(pre[576]["noann"])} ms without the annotation). #2681 remembers which values are known to have a type, so the re-check is one lookup: {fmt(mid[576]["shipped"])} ms at 24x24, the same as the unannotated rule.</p>{mini(FPS, "The shipped 16x16 call, split by measuring the variants, before and after the 14 PRs.")}</div></li>
<li><div class="row"><p><b>Every call pays a floor that grows with the map, and the PRs raise it by about a quarter: {fmt(pre[256]["idA"])} ms at 16x16 before, {fmt(post[256]["idA"])} after ({fmt(pre[576]["idA"])} and {fmt(post[576]["idA"])} at 24x24).</b> Hazel's call boundary turns the whole JS argument into unevaluated Hazel syntax, gives every node a fresh id, and then evaluates it back into the value it already was, node by node; the <code>(Globals, Event)</code> parameter type walks it again. A rule that does nothing still pays this. No PR touches the library's conversion (<code>of_js</code>) or its fresh ids. And the argument is a new value on every call, so #2681 has never seen it: its first push walks it as before and also records every part in the memo. The rise is already there with #2681 alone ({fmt(mid[256]["idA"])} ms), and it repeats in both rounds. It comes from asking #2681's memo at every part of the argument; limited to the argument and its parts, the memo leaves the floor where it was ({fmt(dd[256]["idA"])} ms) and the shipped rule its gain (<a href="#floor">Why #2681 raises the floor</a>).</p>{mini(F4, "The floor of a 16x16 call that does nothing (13.8 ms in the profiled dev build, before), by profile share.")}</div></li>
<li><div class="row"><p><b>Underneath, each evaluation step costs about 3 &micro;s, so even the plain walk is 25-80 &micro;s per cell.</b> A countdown over plain Ints costs {steps_pre["countdown i=128"]} ms for 128 steps before, {steps_post["countdown i=128"]} after (one round each: {pc(steps_pre["countdown i=128"], steps_post["countdown i=128"])} less, not far past this laptop's noise). The time is spread over the evaluator's per-step pipeline, jsoo's generic calls, fresh ids and GC; there is no single hot spot, and none of the 14 PRs aims at it.</p></div></li>
<li><div class="row"><p><b>Passing only the neighbouring cells makes the call flat: {fmt(pre[256]["near"])} ms at 16x16, {fmt(pre[9]["near"])} ms at 3x3.</b> That is the one change, available today without touching Hazel, that removes the dependence on map size: {pre[256]["shipped"] / pre[256]["near"]:.0f}x faster than the shipped rule at 16x16 before the PRs, and still {post[256]["shipped"] / post[256]["near"]:.0f}x after them, with the same answer.</p></div></li>
<li><div class="row"><p><b>The 14 PRs together halve the compile: the game's rules compile in {cm["b"]["compile_ms"]:.0f} ms after, against {cm["base"]["compile_ms"]:.0f} ms before.</b> That is once per program, at load. Per call, everything they change is #2681's: the bars of <a href="#fig-16">Figure 3</a> for <i>+ #2681</i> and <i>after</i> agree within noise. Eight of the 14 cannot reach a library call at all; they speed up the editor, its worker and its recovering parser (the <a href="#prs">table</a>).</p></div></li>
</ol>
</div>

{fig("fig-sizes", 1, FP1, f"Time per call against map size, both scales logarithmic, for five versions of the World rule that return the same answer: dashed, the measured build (1 of the 14 PRs); solid, the same with all 14. Before, the shipped rule's slope is {slope(B['base']['rows'], 'shipped'):.2f} (quadratic-ish) and the others are linear, except neighbours-only, which is flat; after, the shipped rule is linear too ({slope(B['b']['rows'], 'shipped'):.2f}) and lies on the unannotated one. The identity floor moves up. Values from <code>data/prs/</code>, the mean of two rounds. The code behind each line is in <a href=\"#code\">The rules behind each line</a>.")}

<h2 id="code">The rules behind each line</h2>
<p>Every line in Figures 1 and 3 is one of these Hazel functions, compiled once and then called from JS with the same move: the player mid-map, going east (<code>Way("E")</code>). They are the driver's own code (<code>drivers/r25.mjs</code>), laid out here on more lines, Hazel's usual way (the same tokens; the layout is in <code>drivers/listings_fmt.py</code>), and each one returns the same <code>GoSquare</code>. What they share is folded first. The marks show where each one's time goes, in the figures' colours; each card's times are its 16x16 call before and after the 14 PRs. The top box is Hazel; the dashed one is the JS that calls it.</p>
<p class="hslegend">{HS_LEGEND}</p>
<details><summary>shared by all of them: the types, from the program's start, and the helpers</summary><pre class="code">{code(SHARED)}</pre></details>
{LIST_HTML}

<h2 id="prs">Before and after the performance PRs</h2>
<p>The dashboard lists 19 PRs against Hazel's performance. Five are not speed changes: {PRS["not_counted"].split(": ", 1)[1]} That leaves 14. Only <a href="https://github.com/hazelgrove/hazel/pull/2679">#2679</a> is merged into <code>dev</code>, so the measured build has 1 of the 14. To see what the other 13 would do, two trial branches were pushed to hazelgrove/hazel and built by GitHub's Deploy workflow, the same build as the measured one:</p>
<ul>
<li><b>+ #2681</b>: <code>{BN["a"]["branch"]}</code> at <code>{BN["a"]["commit"]}</code>, {BN["a"]["what"]}. 3 of 14.</li>
<li><b>after</b>: <code>{BN["b"]["branch"]}</code> at <code>{BN["b"]["commit"]}</code>, {BN["b"]["what"]}. 14 of 14.</li>
</ul>
<p>They merge cleanly but for three small conflicts (two test lists, and <a href="https://github.com/hazelgrove/hazel/pull/2610">#2610</a> and <a href="https://github.com/hazelgrove/hazel/pull/2614">#2614</a> both fixing the recovering parser), and both trial branches build. What each PR can reach in a library call follows from what the library runs: <code>FastParse</code>, then <code>Statics.mk</code> once per program, then <code>Evaluator.evaluate</code> from scratch on every call, on the page's own thread (<code>src/web/HazelLibCore.re</code>).</p>
<div class="scroll"><table><tr><th>PR</th><th>what it does</th><th>state</th><th>in the measured build</th><th>reaches</th><th>why</th></tr>{pr_rows}</table></div>
<p>Measured, at 16x16 (the mean of two rounds; the rounds' spread is under {noise_p90*100:.0f}% for nine in ten of the times from 6x6 up, so read smaller differences as noise):</p>
<div class="scroll"><table><tr><th>16x16, ms</th><th>before</th><th>+ #2681</th><th>after</th></tr>
{tr(["shipped rule", fmt(pre[256]["shipped"]), fmt(mid[256]["shipped"]), fmt(post[256]["shipped"])])}
{tr(["find unannotated", fmt(pre[256]["noann"]), fmt(mid[256]["noann"]), fmt(post[256]["noann"])])}
{tr(["identity rule (the floor)", fmt(pre[256]["idA"]), fmt(mid[256]["idA"]), fmt(post[256]["idA"])])}
{tr(["neighbours only", fmt(pre[256]["near"]), fmt(mid[256]["near"]), fmt(post[256]["near"])])}
{tr(["shipped rule at 24x24", fmt(pre[576]["shipped"]), fmt(mid[576]["shipped"]), fmt(post[576]["shipped"])])}
</table></div>
<ul>
<li><b>#2681 is the one that matters per call.</b> It makes the annotated rule linear: {x_(pre[256]["shipped"], mid[256]["shipped"])} faster at 16x16 and {x_(pre[576]["shipped"], mid[576]["shipped"])} at 24x24, where the quadratic part was largest. The game's own World handler moves the same way ({fmt(pre[256]["game_World"])} to {fmt(post[256]["game_World"])} ms at 16x16).</li>
<li><b>It costs the floor about a quarter</b> ({fmt(pre[256]["idA"])} to {fmt(mid[256]["idA"])} ms at 16x16): every call's argument is a fresh value, so its first push records it without ever reusing it. The unannotated rules carry the same rise. A memo of values from earlier calls cannot help here, since <code>of_js</code> never gives the same object twice; what would is not re-stepping the converted value at all (<a href="#fix">fix 1 below</a>).</li>
<li><b>The other 11 change nothing per call</b>, within noise. Three reach the compile, and with them it halves; eight cannot reach the library at all.</li>
</ul>
<div class="scroll"><table><tr><th>build</th><th>compile the game's rules, ms (each round)</th><th>compile and run this report's program, ms (each round)</th></tr>{comp_rows}</table></div>
<p class="note">Each compile is the first call in a fresh node process, so it includes the JIT's warm-up; there is one per round. The drop comes with the PRs that reach the compile (<a href="https://github.com/hazelgrove/hazel/pull/2603">#2603</a>, <a href="https://github.com/hazelgrove/hazel/pull/2651">#2651</a>, <a href="https://github.com/hazelgrove/hazel/pull/2608">#2608</a>); which of them carries it was not measured apart.</p>
<p class="note">Both trial branches pass Hazel's whole test suite on GitHub (Fast checks and Full tests): #2681 on the measured build, and all 14 PRs merged together.</p>

<h3 id="floor">Why #2681 raises the floor, and a fix</h3>
<p>Matthew, on the floor's rise: <q>find why #2681 raises the floor by about a quarter, and whether it can skip recording values it will never see again</q> (<code class="ref"><b>^ticket(</b>535<b>)</b></code>).</p>
<p><b>Why.</b> #2681 asks its memo (<code>has_type</code>, a WeakMap) at every part of every value an ascription is pushed through, and after a walk that gives a part back unchanged it records that part, and every tail of a list. Each ask and each record also looks up the type's hash (#2661's cache, another WeakMap). Counted by wrapping WeakMap's <code>get</code> and <code>set</code> around GitHub's build, without rebuilding (<code>drivers/floor2681.mjs</code>), one 16x16 call of the identity rule does {cnt[("a", "idA")][0]["get"]:,} memo lookups, all misses, {cnt[("a", "idA")][0]["set"]:,} writes (the tails of the cells' list and of every cell's <code>ways</code>, every record and every field) and {cnt[("a", "idA")][1]["get"]:,} type-hash lookups. The argument is converted afresh on every call, so nothing recorded is asked about again. The shipped rule's whole gain is {cnt[("a", "shipped")][0]["hit"]} hits, one per step of <code>find</code>.</p>
<p>The writes alone are not the cost. With only them switched off, the identity call was no faster ({" and ".join(fmt(x["16x16"]["idA"]) for x in noset)} ms in two rounds, against {fmt(flm("a", "16x16", "idA"))} ms with them), while the shipped rule, now missing every time, took {fmt(sum(x["16x16"]["shipped"] for x in noset) / len(noset))} ms: slower than before #2681 ({fmt(flm("base", "16x16", "shipped"))} ms), since every check still asks the memo and the type hash. Nor is it the collector: GC time per identity call was {flg("base", "16x16", "idA"):.2f}, {flg("a", "16x16", "idA"):.2f} and {flg("d", "16x16", "idA"):.2f} ms in the three builds below. The cost is the asking, at every part.</p>
<p><b>A fix.</b> The memo cannot tell which values it will see again, but the pattern it exists for has a fixed shape: a recursive function whose annotated parameter receives the tail of a list it was given, as the argument itself or as a part of an argument tuple, like <code>find(rest, c, r)</code> against <code>([Cell], Int, Int)</code>. So the trial branch <code>{BN["d"]["branch"]}</code> (<code>{BN["d"]["commit"]}</code>) asks and tells the memo only at a pushed value and its parts, depth 0 and 1 (<code>Ascriptions.memo_depth</code>); a record's label and a list's tail count as the same depth as the record or the list. Deeper parts are walked as before #2681.</p>
<div class="scroll"><table><tr><th>one 16x16 call</th><th>memo lookups</th><th>memo hits</th><th>memo writes</th><th>type-hash lookups</th></tr>{cnt_rows}</table></div>
<div class="scroll"><table><tr><th rowspan=2>ms per call</th><th colspan=3>this report's driver, 2 rounds</th><th colspan=3>the floor driver, 3 rounds</th></tr><tr><th>before</th><th>#2681</th><th>depth-limited</th><th>before</th><th>#2681</th><th>depth-limited</th></tr>{fl_rows}</table></div>
<p>So yes: limited this way, #2681 stops recording what these calls never see again. The floor is back where it was before #2681 ({fmt(dd[256]["idA"])} ms at 16x16 against {fmt(pre[256]["idA"])}), and the shipped rule keeps its gain ({fmt(dd[256]["shipped"])} ms against {fmt(mid[256]["shipped"])} with the whole memo, and {fmt(pre[256]["shipped"])} before). The two drivers disagree on how big the rise was ({round(100 * (mid[256]["idA"] / pre[256]["idA"] - 1))}% in this report's, which runs many variants and sizes in one process, {round(100 * (flm("a", "16x16", "idA") / flm("base", "16x16", "idA") - 1))}% in the floor driver's three variants); the limit removes it in both at 16x16. At 24x24 the floor driver's mean is {fmt(flm("d", "24x24", "idA"))} ms against {fmt(flm("base", "24x24", "idA"))} before, but one of its three rounds ran long ({" / ".join(fmt(x["24x24"]["idA"]) for x in fl["d"])} ms), and this report's driver puts it at {fmt(dd[576]["idA"])} against {fmt(pre[576]["idA"])}.</p>
<p>On GitHub the trial branch passes Fast checks; {TESTS_D}.</p>

<h3 id="woods">The woods, re-measured on #2635</h3>
<p>What the limit could give up: a value recognized deeper inside a later push, as when shapes already checked one by one are checked again inside a list. #2681 was first measured on #2635's woods picture (the Scenes slide), so Matthew asked: <q>re-measure #2681's woods picture on #2635 with the depth limit, on GitHub's runners, and if it keeps the gain, propose the limit on #2681.</q></p>
<p>The 2026-10-13 Firefox driver was lost with a crash's scratch folder; its node harness survived and is now <code>test/Test_PicView.re</code> on the trial branch <code>trial/2635-memo-depth</code> (#2635's head <code>2b080af683</code>, the same limit, and <code>memo_depth</code> made a reference so one build can time every setting). Program A is the Scenes slide's program up to its picture, B the same with the woods picture's view; each run times both at every setting in turn, after a full GC. <code>.github/workflows/picview.yml</code> builds the test runner and runs that group alone, on three runners at once, 21 runs each. Every setting gives the same result.</p>
<div class="scroll"><table><tr><th>runner</th><th>off</th><th>depth 1</th><th>depth 2</th><th>depth 3</th><th>whole</th><th>depth 1 keeps</th></tr>{woods_rows}</table></div>
<p class="note">The fastest of 21 runs, ms, program B (the Scenes program with the woods picture's view). <i>Depth 1 keeps</i> is its share of the whole memo's gain over <i>off</i>. Two earlier single runs of 9 disagreed, one finding depth 1 kept none of the gain and the other nearly all: each setting's runs fall in two clusters about 500 ms apart, so a median of nine can land in either. Hence three runners, the fastest run, and the median beside it ({krange("depth1", "median")} by the median). The raw runs are in <code>data/floor/picview_a1e0189045/</code>.</p>
<p>Depth 1 keeps {krange("depth1")} of the memo's gain on the woods. Deeper limits keep a little more of it and give back part of the library's floor:</p>
<div class="scroll"><table><tr><th>has_type asked and told to</th><th>library floor, 16x16 (ms)</th><th>against before</th><th>woods gain kept</th></tr>{depth_rows}</table></div>
<p class="note">The floor is this report's driver, two rounds each; depths 2 and 3 were timed in a later session than the rest, and this laptop's run-to-run noise is about 10%. Writes per 16x16 identity call: 3 at depth 1, 276 at depth 2, 532 at depth 3, 2,580 with the whole memo.</p>
<p>So depth 1 is the limit to propose: no rise in the library's floor, the annotated rule's gain kept in full, and most of the woods' gain.</p>

<h2 id="call">What happens in one call</h2>
<figure class="fig" id="fig-game"><div class="gamepics">
<img src="img/world-grid.webp" alt="Messed Up Dress Up's World design tab: the world's grid, 6 by 7, a place in each square; the forest clearing, D4, is selected, with the castle east of it, E4." loading="lazy">
<div><img src="img/clearing-at-its-east-way.webp" alt="The forest clearing, the friend at its east edge, where an arrow leads to the castle, E4." loading="lazy">
<img src="img/castle-at-its-west-way.webp" alt="The castle, the friend at its west edge, where an arrow leads back to the forest clearing." loading="lazy"></div></div>
<figcaption><b>The World room's move, in the game.</b> Left: the 🗺️ World design tab, the world's grid (6 by 7; the default world, Messed Up Dress Up 0.0.408); the forest clearing, D4, is selected, the castle beside it, E4. Right: the clearing, the friend at its east way, its arrow saying where it leads (the castle, E4); and the castle, the friend at its west way, back to the clearing. Walking through is the event <code>Way("E")</code> this report times: the rule finds the square east of the player in <code>cells</code> and answers <code>GoSquare(4, 3, "W", Done)</code> if it has a way back west (the rule counts from 0, so D4 is (3, 3)). Every arrow is shown here (🔬 Inspection's 🧭 all arrows); a player sees one when near it. Pictures from GitHub's runner (kids-choice-games, branch <code>shots-535</code>, <code>tools/shots.mjs</code>).</figcaption></figure>
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
<p>That is also why the game's own figure, 40 ms, is lower than this report's {fmt(pre[256]["shipped"])} ms: the cost depends on where the target sits in the list. With all four ways set, a target at index 1 costs 18 ms at 16x16 and the last one 244 ms; removing only the annotation brings the last to 33 ms (8x8: 23 to 8.9 ms). The Square room's <code>find</code> and <code>doors</code> helpers are annotated the same way, which fits a lever with 40 doors taking about 85 ms.</p>
{fig("fig-16", 3, FP3, f"One 16x16 World call, by version of the rule, in the three builds; every version returns the same <code>GoSquare</code>. <i>Index arithmetic</i> takes one <code>nth</code> at <code>r*cols+c</code>; <i>held</i> converts the map once into a Hazel closure ({fmt(pre[256]['held_setup'])} ms at setup) and calls it per event; <i>identity</i> is a rule that ignores its argument, so it is the floor. Only the shipped rule's bars move far, and only at <i>+ #2681</i>.")}

<h2 id="data">The numbers</h2>
<h3 id="t-prs">Before and after the PRs, by map size (ms, p50, the mean of two rounds)</h3>
<div class="scroll"><table>{ba_head}{ba_rows}</table></div>
<p class="note">Growth exponents from 64 to 576 cells, before / after: shipped {slope(B['base']['rows'], 'shipped'):.2f} / {slope(B['b']['rows'], 'shipped'):.2f}, unannotated {slope(B['base']['rows'], 'noann'):.2f} / {slope(B['b']['rows'], 'noann'):.2f}, identity {slope(B['base']['rows'], 'idA'):.2f} / {slope(B['b']['rows'], 'idA'):.2f}. Every round of every build is in <code>data/prs/</code>.</p>
<h3 id="t-steps-prs">Per-step costs, before and after (ms, p50)</h3>
<div class="scroll"><table><tr><th>program</th><th>before</th><th>after</th></tr>{"".join(tr([k, steps_pre[k], steps_post[k]]) for k in steps_pre)}</table></div>
<h3 id="t-sizes">The first run, before only (ms, p50)</h3>
<p class="note">The first draft's numbers, one run of the measured build, kept for the record; the reruns above agree with it within the rounds' noise.</p>
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
<li><b>Drop type annotations on recursive helpers</b> (World's <code>find</code>, Square's <code>find</code> and <code>doors</code>): {fmt(pre[256]["shipped"])} to {fmt(pre[256]["noann"])} ms at 16x16 on the measured build; linear instead of quadratic. Not needed once #2681 is in, which gives the same without touching the rules.</li>
<li><b>Pass only what the rule needs</b>: the neighbouring cells, not the map. Flat at about 0.9 ms at every size. All 17 <code>Globals</code> fields go to every room today, and each is converted and re-stepped per call.</li>
</ol>
<h3>In Hazel's library and evaluator</h3>
<ol>
<li><b>Do not re-step a converted value.</b> Have <code>of_js</code> produce something the evaluator treats as final (or bind the argument in the environment and apply to a variable). About half the floor.</li>
<li><b>An ascription fast path: this is <a href="https://github.com/hazelgrove/hazel/pull/2681">#2681</a>, measured above.</b> It remembers which values are known to have a type, so the recursive <code>find(rest, ...)</code> re-check is one lookup: the annotated rule becomes linear without changing it ({fmt(pre[256]["shipped"])} to {fmt(mid[256]["shipped"])} ms at 16x16). It is open, on top of <a href="https://github.com/hazelgrove/hazel/pull/2661">#2661</a>. What it does not do is cheapen a value's first push, which it now makes about a quarter dearer by recording it; checking a fresh value without allocating would.</li>
<li><b>A cheaper <code>Id.mk</code></b>, without <code>Uuidm.v4</code>'s byte copy under js_of_ocaml: about a fifth of all time.</li>
<li><b>Cut the per-step pipeline when nothing uses it</b>: the state merge, reuse check and probe sampling run on every step even with no probes and no reuse (8.1%, 8.0% and 6.8% inclusive in the walk's profile).</li>
</ol>
<p>Fix 2 already brings the shipped rule onto the unannotated one, on its branch. Fix 1 would take the floor to perhaps a third of today's, and with it the first-push cost #2681 adds; fix 4 is what would make a linear walk cheaper. None of them makes Hazel's walk cost what JS's does (under 1 &micro;s); a rule's design still decides whether the call depends on the map's size.</p>

<h2 id="library">Hazel's JS library, as this report uses it</h2>
<p>Matthew: <q>Let's use it to help me really review our JS library for Hazel, and how well it integrates when required or wanted.</q> This report leans on the library (<a href="https://github.com/hazelgrove/hazel/pull/2711">#2711</a>, and <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> for the frame) in four ways. Here is each, what worked, and what was rough. The rough parts are tickets now.</p>
<div class="scroll"><table><tr><th>use</th><th>how</th><th>what worked</th><th>what was rough</th><th>ticket</th></tr>
<tr><td>timing every rule (node)</td><td><code>Hazel.run(text)</code> on <code>hazel-lib.js</code>, then the function it gives back called from JS (<code>drivers/r25.mjs</code>)</td><td>One script, no build: GitHub's Deploy build of any branch is a library to time (the four trial builds here). A Hazel function comes back as a JS function; records, lists, strings and constructors convert both ways.</td><td>Every call converts its argument to syntax with fresh ids and re-steps it (the floor, 31 &micro;s a cell). No way to keep a Hazel value across calls except a closure (<a href="#code-held">held</a>). No step count, so per-step costs are inferred from times.</td><td><code class="ref"><b>^ticket(</b>539<b>)</b></code></td></tr>
<tr><td>the game's rules</td><td><code>Hazel.runProgram({{preamble, modules, tail}})</code>, a function per room (<code>25-scripting.js</code>)</td><td>Named modules with their own errors; the game plays the same with 🧩 on (^ticket(531)'s checks).</td><td>Compiling the rules costs 0.8 s before the PRs (0.4 s after, <a href="#prs">above</a>), first event or load. Handlers pay the boundary on all of <code>Globals</code>.</td><td><code class="ref"><b>^ticket(</b>540<b>)</b></code></td></tr>
<tr><td>the tiles under each listing</td><td>the embed frame, <code>index.html#embed</code>, protocol 1: <code>set</code> a program, get <code>ready</code>, <code>size</code>, <code>status</code></td><td>The protocol is small and did what it says: ready, then the program drawn with statics and Hazel's marks, its height and its verdict back.</td><td>The cell is a static view: no caret, no selection, so the tile shapes never show (Matthew: <q>They don't show up during selection</q>). A whole Hazel app per frame. It draws, sizes and reports only while it can render: a hidden or background page gets height 0 and no status. It takes programs only from origins compiled into it (matthewhammer.org, localhost).</td><td><code class="ref"><b>^ticket(</b>538<b>)</b></code></td></tr>
<tr><td>the run boxes</td><td><code>hazel-lib.js</code> as a plain script from hazel.org, <code>Hazel.run</code> on the first click</td><td>A page runs a listing in the reader's browser in a few lines: the value back, in Hazel's notation, and its time (neighbours only, 8x8: <code>GoSquare(4, 4, "W", Done)</code>, about 3 ms after a 0.1 s compile).</td><td>2.8 MB to load; the build to load is a branch's folder on hazel.org, which moves when the branch is pushed; nothing in the library says which version or protocol it is.</td><td><code class="ref"><b>^ticket(</b>537<b>)</b></code></td></tr>
</table></div>
<p><b>What the library could add, in order of what this report needed most:</b></p>
<ol>
<li><b>A selectable read-only view</b>: the embed's cell with a caret and selection but no edits, so the tiles show. Hazel has one already (<code>CodeSelectable</code>, used for results); a branch wiring it into the embed is being built (<code>embed-selectable</code>, ^ticket(538)).</li>
<li><b>Calls that do not convert what they were given before</b>: final values from <code>of_js</code>, or a handle to a value already in Hazel, so a rule called per event pays for what changed, not for the world (^ticket(539)).</li>
<li><b>A view mounted in the page, not a frame</b> (<code>Hazel.mountEditor</code>, #2711's planned next feature): one app for every listing on a page, drawn where the page is, off screen or not.</li>
<li><b>Counts as well as times</b>: evaluation steps and conversions per call, so a report can say what a call did, not only how long it took.</li>
<li><b>A version a page can ask for</b>: the library's build and the embed's protocol, from the library itself, and a stable URL per release, so a page does not follow a branch.</li>
</ol>

<h2 id="next">What next</h2>
<ol>
<li><b>Asymptotic analysis of every event handler</b> in the game's Hazel rules (matthewhammer/kids-choice-games#2, <code class="ref"><b>^ticket(</b>531<b>)</b></code>), against a world (the game's JSON world data) of size N. Matthew: <q>Each one should be O(1) or at the worst, O(log N), for a world (json data file) of size N.</q> For each room's <code>on_event</code> and each event it takes: its cost in N, counting the call boundary (today every call converts and checks all of <code>Globals</code>, so even a handler that does nothing is O(N)), and a version meeting the bound. Known so far: World's <code>Way</code> is O(N) in the cells (the <code>find</code> walk; quadratic with its annotation before #2681) and O(1) given only the neighbours (<a href="#code-near">neighbours only</a>); the Square's levers are O(doors), quadratic through the annotated <code>find</code> and <code>doors</code>; the Castle's <code>FallPit</code> and <code>WayOut</code> are O(rooms) through <code>index_of</code> and <code>nth</code>. The boundary itself is the first thing to take out of N: pass each handler only what it reads, or hold the world in Hazel once and pass only what changes, as <a href="#code-held">held</a> does, with lookups that are not walks.</li>
<li>Change the World and Square rules on matthewhammer/kids-choice-games#2: no annotations on recursive helpers, and neighbours only in World's <code>Globals</code>; re-time the game's moves at 16x16.</li>
<li>Land <a href="https://github.com/hazelgrove/hazel/pull/2661">#2661</a> and <a href="https://github.com/hazelgrove/hazel/pull/2681">#2681</a> in <code>dev</code>, then rebase <a href="https://github.com/hazelgrove/hazel/pull/2711">#2711</a> and <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> on it: the game gets the linear rule without changing its rules. (Measured here on <code>{BN["a"]["branch"]}</code>.)</li>
<li>The depth-1 limit is proposed on #2681 (<a href="https://github.com/hazelgrove/hazel/pull/2681#issuecomment-6344616722">the proposal</a>, with these numbers); if taken, its two commits go onto #2681's branch.</li>
<li>Prototype <code>of_js</code> producing final values, and time the identity rule's floor.</li>
<li>Pin the noise floor: two rounds give a spread under {noise_p90*100:.0f}% for nine in ten of the times; five would say more.</li>
<li>Measure the compile's halving PR by PR (<a href="https://github.com/hazelgrove/hazel/pull/2603">#2603</a>, <a href="https://github.com/hazelgrove/hazel/pull/2651">#2651</a>, <a href="https://github.com/hazelgrove/hazel/pull/2608">#2608</a>).</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>Node v22.23.2 on the Ubuntu laptop (Intel i7), one process at a time. The library is hazel-lib.js from <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> at <code>0d66c36618</code>: the minified build for every time, the dev build <code>hazelLib.bc.js</code> for named profiles (3 s each). The rules are the game's at <code>2ebda59ab4</code>. Each time is one p50 over 20-60 reps after warm-up; for that first run the noise floor was not measured, so treat differences under about 10% as noise (the reruns below give it: under {noise_p90*100:.0f}% for nine in ten times). The target cell is mid-map, at (n/2-1, n/2), moving east; every variant's result was checked against the game's World handler. The library exposes no step count, so per-step costs are inferred from timings. The drivers are in <code>drivers/</code> (<code>r25.mjs</code> for the sizes, <code>steps.mjs</code>, <code>profheld.mjs</code>, and the earlier <code>prof.mjs</code> and <code>prof_noann.mjs</code>; they read the game and library from local checkouts); the data is in <a href="https://github.com/matthewhammer/hazel-reports/tree/main/025/data"><code>data/</code></a>, and the profiles, too big to keep, are summarized in <code>data/profiles.json</code>.</p>
<p>Before and after the PRs: <code>drivers/prs.sh</code> runs <code>r25.mjs</code> on GitHub's Deploy builds of three branches (hazelgrove/build, <code>&lt;branch&gt;/hazel-lib.js</code>): <code>js-library-embed</code> at <code>0d66c36618</code>, <code>{BN["a"]["branch"]}</code> at <code>{BN["a"]["commit"]}</code> and <code>{BN["b"]["branch"]}</code> at <code>{BN["b"]["commit"]}</code>, in two rounds with the builds interleaved (before, + #2681, after; then again), one node process at a time, pinned to two threads and niced, as this laptop needs. Every time above is the mean of the two rounds; each round is in <code>data/prs/</code>, with each build's compile times. The builds and the 14 PRs are in <code>data/prs.json</code>. The per-step costs are one round per build (<code>steps.mjs</code>). The figures and the first table use these reruns; <i>the first run</i> is the first draft's, kept as it was.</p>

<h2 id="related">Where this sits: related work</h2>
<p>Matthew asked for this report to be set beside three lines of work: the semantics of game interfaces, the adventure-game engines Messed Up Dress Up draws on, and Scratch and its kin. Each frames the same question this report measures: what an event handler is given, and how its cost grows with the world.</p>

<h3 id="rel-lop">Languages of Play (2017)</h3>
<p>In <a href="https://arxiv.org/abs/1703.05410">Languages of Play: Towards Semantic Foundations for Game Interfaces</a> (Chris Martens and Matthew A. Hammer, 2017), a game's interface is a programming language of player intent. Its syntax is the intents the game recognizes. Its operational semantics is the mechanics, as rules for a step from a state and an intent to a new state and a response. Its type system is a contextual interface, in which only what makes sense in the current state can be said. <a href="https://matthewhammer.org/hazel/reports/020/">^report(20)</a> sets the paper beside Messed Up Dress Up at length, and <a href="https://matthewhammer.org/hazel/dress-up/">the game's page</a> cites it.</p>
<p>The World rule measured here is one such step: <code>on_event : (Globals, Event) -&gt; Cmd</code> takes a state and an intent (<code>Way("E")</code>) to a response (<code>GoSquare(4, 3, "W", Done)</code>). The paper's contextual interface has a cost reading that this report adds. A step that is given only its context (<a href="#code-near">neighbours only</a>: the squares a move can reach) is both well-scoped in the paper's sense and O(1) in the world. A step given the whole world, as the library's boundary gives it today, is O(N) before it does anything. The asymptotic next step (O(1) or O(log N) per handler) amounts to asking that each rule's input be its context, not the world.</p>

<h3 id="rel-engines">Adventure-game engines, 1984 to the early 1990s</h3>
<p>Messed Up Dress Up's places, rooms and ways out follow the graphical adventure games of that era:</p>
<ul>
<li>Sierra On-Line's AGI (the Adventure Game Interpreter, from <i>King's Quest</i>, 1984) and its successor SCI (1988);</li>
<li>Lucasfilm Games' SCUMM (the Script Creation Utility for <i>Maniac Mansion</i>, 1987, later <i>Monkey Island</i>);</li>
<li>Gray Design Associates' <i>Hugo's House of Horrors</i> (David P. Gray, 1990) and its sequels.</li>
</ul>
<p>Their worlds were rooms, each with its own scripts: what happens on entering, on a verb used on an object, on walking to an edge. The scripts were written in small languages run by an interpreter, on PCs thousands of times slower than today's. What made that work is the shape this report arrives at. A handler touched its room's objects and a few numbered flags and variables, and no event scanned the whole world. Dress Up's rules already have the same shape, a module per room with an <code>on_event</code>, but the library's boundary ships the whole world into every call. Those engines met the O(1)-per-event goal by construction; Hazel's rules can meet it the same way, by what they are given (<a href="#code-near">neighbours only</a>) or by holding the world once (<a href="#code-held">held</a>) with lookups that are not walks.</p>

<h3 id="rel-scratch">Scratch, and game creation in CS education</h3>
<p><a href="https://scratch.mit.edu/">Scratch</a> (MIT Media Lab) is built on the same event-handler shape: sprites with scripts that start on an event ("when this sprite is clicked", a broadcast message). Its blocks are a structure editor in which a script cannot be malformed, as Hazel's tiles are. Its kin take the idea in different directions:</p>
<ul>
<li><a href="https://snap.berkeley.edu/">Snap!</a> adds first-class procedures.</li>
<li>Alice teaches objects through 3D scenes.</li>
<li>Kodu writes rules as "when ... do ...".</li>
<li><a href="https://bootstrapworld.org/">Bootstrap</a> has students write a game as pure functions over a world value, one handler per event (a key, a tick), in Racket and in Pyret. That is closest to the rules here: a handler is a function from the world and an event to a new world or a command.</li>
</ul>
<p>Two differences matter for this report. First, Hazel's rules are typed and stay meaningful while half-written (holes), with the game's own controls inside them as livelits. Second, the cost question is the same one: Bootstrap's handlers are given the whole world value, as Dress Up's are here, and what a handler is given decides whether it grows with the world.</p>

<script type="application/json" id="tiles-data">{json.dumps(TILES).replace("</", "<\\/")}</script>
<script>
{RUNBOX_JS}
/* each run box: Hazel's library loaded once, on the first click (a plain script from hazel.org), then its listing run */
(() => {{
  const LIB = "https://hazel.org/build/js-library-embed/hazel-lib.js";
  let loading = null;
  const lib = () => loading || (loading = new Promise((ok, no) => {{
    if (window.Hazel) return ok(window.Hazel);
    const s = document.createElement("script"); s.src = LIB; s.onload = () => window.Hazel ? ok(window.Hazel) : no(new Error("no window.Hazel"));
    s.onerror = () => {{ loading = null; no(new Error("could not load " + LIB)); }}; document.head.appendChild(s);
  }}));
  const T = JSON.parse(document.getElementById("tiles-data").textContent);
  const esc = t => t.replace(/[&<>]/g, c => ({{ "&": "&amp;", "<": "&lt;", ">": "&gt;" }})[c]);
  document.querySelectorAll(".runbox[data-k]").forEach(box => {{
    const k = box.dataset.k, out = box.querySelector(".rb-out"), btn = box.querySelector("button"), sel = box.querySelector("select");
    btn.addEventListener("click", async () => {{
      btn.disabled = true; out.textContent = window.Hazel ? "running…" : "loading Hazel's library…";
      try {{
        const H = await lib(); out.textContent = "running…";
        await new Promise(r => setTimeout(r, 0));
        const r = RUNBOX.run(H, k, T[k], +sel.value);
        out.innerHTML = r.error ? esc(r.error) :
          "input:  " + esc(r.input) + "\\n<b>output: " + esc(r.output) + "</b>\\n" +
          "in this browser: " + r.ms.toFixed(2) + " ms a call (the median of 5, after one to warm up)" +
          (r.setup !== undefined ? "; holding the map: " + r.setup.toFixed(1) + " ms, once" : "") +
          (r.compileMs !== undefined ? "; compiled first, once: " + r.compileMs.toFixed(0) + " ms" : "");
      }} catch (e) {{ out.textContent = "could not run: " + (e && e.message || e); }}
      btn.disabled = false;
    }});
  }});
}})();
</script>
<script>
/* Hazel's tile editor below each listing: Hazel's app in a frame, in its embed mode (protocol 1, docs/hazel-as-a-js-library.md on
   #2719), which takes a program from this page (matthewhammer.org and localhost are on its list) and shows it read only, posting back
   its height and what Hazel says of the program. Each frame is made only when its box comes near the screen. */
(() => {{
  const URL = "https://hazel.org/build/js-library-embed/index.html#embed", ORIGIN = "https://hazel.org";
  const T = JSON.parse(document.getElementById("tiles-data").textContent);
  const frames = [];
  addEventListener("message", e => {{
    if (e.origin !== ORIGIN) return;
    const f = frames.find(f => f.iframe.contentWindow === e.source); if (!f) return;
    const m = e.data || {{}};
    const say = t => {{ f.phase.textContent = t; }};
    if (m.type === "ready") {{
      if (m.protocol !== 1) {{ say("these tiles speak protocol " + m.protocol + "; this page knows protocol 1"); return; }}
      f.iframe.contentWindow.postMessage({{ type: "set", text: T[f.k] }}, ORIGIN);
      say("ready (build " + String(m.build || "?").slice(0, 10) + "); program sent, waiting for Hazel to draw it");
    }} else if (m.type === "size") {{
      f.iframe.style.height = Math.max(40, Math.min(3000, Math.ceil(+m.height || 0))) + "px";
      if (!f.status) say("drawn, " + Math.ceil(+m.height || 0) + " px tall; waiting for Hazel's verdict");
    }} else if (m.type === "status") {{
      f.status = m; say("Hazel says: " + (m.ok ? "no errors" : (m.errors || 0) + " errors, " + (m.holes || 0) + " holes"));
    }} else if (m.type === "crash") say("the tiles stopped: " + (m.message || "an error"));
  }});
  const mount = box => {{
    if (box.querySelector("iframe")) return;
    const iframe = document.createElement("iframe");
    iframe.src = URL; iframe.className = "tiles-frame"; iframe.tabIndex = -1; iframe.loading = "eager";
    iframe.title = "Hazel's tile editor, read only: " + box.dataset.k;
    box.appendChild(iframe);
    const phase = box.querySelector(".tiles-phase"); phase.textContent = "loading Hazel…";
    box.querySelector(".tiles-go").remove();
    frames.push({{ iframe, k: box.dataset.k, note: box.querySelector(".tiles-note"), phase, status: null }});
  }};
  document.querySelectorAll(".tiles[data-k] .tiles-go").forEach(b => b.addEventListener("click", () => mount(b.closest(".tiles"))));
  const io = new IntersectionObserver(es => es.forEach(e => {{ if (e.isIntersecting) {{ io.unobserve(e.target); mount(e.target); }} }}), {{ rootMargin: "300px" }});
  document.querySelectorAll(".tiles[data-k]").forEach(b => io.observe(b));
}})();
</script>
</main></body></html>
"""
open(OUT, "w").write(PAGE)
print("wrote", OUT)
