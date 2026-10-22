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
<style>{STYLE}</style></head>
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

{fig("fig-sizes", 1, FP1, f"Time per call against map size, both scales logarithmic, for five versions of the World rule that return the same answer: dashed, the measured build (1 of the 14 PRs); solid, the same with all 14. Before, the shipped rule's slope is {slope(B['base']['rows'], 'shipped'):.2f} (quadratic-ish) and the others are linear, except neighbours-only, which is flat; after, the shipped rule is linear too ({slope(B['b']['rows'], 'shipped'):.2f}) and lies on the unannotated one. The identity floor moves up. Values from <code>data/prs/</code>, the mean of two rounds.")}

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
<p class="note">What the limit gives up: a value recognized deeper inside a later push, as when shapes already checked one by one are checked again as a list. #2681's own browser measurement (#2635's woods picture, 563.5 to 497.5 ms per figure move) may lean on that, so it should be re-measured with the limit before #2681 takes it. On GitHub the trial branch passes Fast checks; {TESTS_D}.</p>

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

<h2 id="next">What next</h2>
<ol>
<li>Change the World and Square rules on matthewhammer/kids-choice-games#2: no annotations on recursive helpers, and neighbours only in World's <code>Globals</code>; re-time the game's moves at 16x16.</li>
<li>Land <a href="https://github.com/hazelgrove/hazel/pull/2661">#2661</a> and <a href="https://github.com/hazelgrove/hazel/pull/2681">#2681</a> in <code>dev</code>, then rebase <a href="https://github.com/hazelgrove/hazel/pull/2711">#2711</a> and <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> on it: the game gets the linear rule without changing its rules. (Measured here on <code>{BN["a"]["branch"]}</code>.)</li>
<li>Re-measure #2681's woods picture on #2635 with its memo limited to depth 1 (<code>{BN["d"]["branch"]}</code>), and if it keeps that gain, propose the limit on #2681.</li>
<li>Prototype <code>of_js</code> producing final values, and time the identity rule's floor.</li>
<li>Pin the noise floor: two rounds give a spread under {noise_p90*100:.0f}% for nine in ten of the times; five would say more.</li>
<li>Measure the compile's halving PR by PR (<a href="https://github.com/hazelgrove/hazel/pull/2603">#2603</a>, <a href="https://github.com/hazelgrove/hazel/pull/2651">#2651</a>, <a href="https://github.com/hazelgrove/hazel/pull/2608">#2608</a>).</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>Node v22.23.2 on the Ubuntu laptop (Intel i7), one process at a time. The library is hazel-lib.js from <a href="https://github.com/hazelgrove/hazel/pull/2719">#2719</a> at <code>0d66c36618</code>: the minified build for every time, the dev build <code>hazelLib.bc.js</code> for named profiles (3 s each). The rules are the game's at <code>2ebda59ab4</code>. Each time is one p50 over 20-60 reps after warm-up; for that first run the noise floor was not measured, so treat differences under about 10% as noise (the reruns below give it: under {noise_p90*100:.0f}% for nine in ten times). The target cell is mid-map, at (n/2-1, n/2), moving east; every variant's result was checked against the game's World handler. The library exposes no step count, so per-step costs are inferred from timings. The drivers are in <code>drivers/</code> (<code>r25.mjs</code> for the sizes, <code>steps.mjs</code>, <code>profheld.mjs</code>, and the earlier <code>prof.mjs</code> and <code>prof_noann.mjs</code>; they read the game and library from local checkouts); the data is in <a href="https://github.com/matthewhammer/hazel-reports/tree/main/025/data"><code>data/</code></a>, and the profiles, too big to keep, are summarized in <code>data/profiles.json</code>.</p>
<p>Before and after the PRs: <code>drivers/prs.sh</code> runs <code>r25.mjs</code> on GitHub's Deploy builds of three branches (hazelgrove/build, <code>&lt;branch&gt;/hazel-lib.js</code>): <code>js-library-embed</code> at <code>0d66c36618</code>, <code>{BN["a"]["branch"]}</code> at <code>{BN["a"]["commit"]}</code> and <code>{BN["b"]["branch"]}</code> at <code>{BN["b"]["commit"]}</code>, in two rounds with the builds interleaved (before, + #2681, after; then again), one node process at a time, pinned to two threads and niced, as this laptop needs. Every time above is the mean of the two rounds; each round is in <code>data/prs/</code>, with each build's compile times. The builds and the 14 PRs are in <code>data/prs.json</code>. The per-step costs are one round per build (<code>steps.mjs</code>). The figures and the first table use these reruns; <i>the first run</i> is the first draft's, kept as it was.</p>
</main></body></html>
"""
open(OUT, "w").write(PAGE)
print("wrote", OUT)
