#!/usr/bin/env python3
"""^report(21)'s page: reads 021/data/prs.json (one record per PR: what it changes, its mechanism, the argument
that it keeps types and values the same, its assumptions and risks, the tests that back it and the ones missing,
and a verdict) and 021/data/meta.json (title, question, short answers, the tests sections, what next, method),
and writes 021/index.html and 021/img/thumb.svg. Run from the repository's root, then the series tools
(report_refs, link_prs, add_steps, add_theme) and tools/theme_variants.py 021/img/thumb.svg.
  python3 021/drivers/gen021.py"""
import json, html, os

P = json.load(open("021/data/prs.json"))
M = json.load(open("021/data/meta.json"))
esc = html.escape

# a verdict, in order from no question to a problem: its label and its colour
VERDICTS = [
    ("none", "Cannot change a type or a value", "muted"),
    ("holds", "Same results: the argument holds", "good"),
    ("assumes", "Same results, under a stated assumption", "accent2"),
    ("spike", "Changes results: a spike, not for merging", "warn"),
    ("fails", "The argument does not hold", "bad"),
]
V = {k: (label, tone) for k, label, tone in VERDICTS}
AREAS = [("statics", "Statics"), ("evaluator", "Evaluator"), ("editor", "Parsing, editor, worker"), ("tests", "Tests, CI, spike")]
for p in P:
    assert p["verdict"] in V, (p["pr"], p["verdict"])
    assert p["area"] in dict(AREAS), (p["pr"], p["area"])
count = {k: sum(p["verdict"] == k for p in P) for k, _, _ in VERDICTS}

# the figure: a column per area, a box per PR in its verdict's colour
COLW, BOXH, GAP, TOP = 220, 30, 8, 58
rows = max(sum(p["area"] == a for p in P) for a, _ in AREAS)
W, H = 30 + len(AREAS) * (COLW + 14), TOP + rows * (BOXH + GAP) + 16
svg = [f'<svg viewBox="0 0 {W} {H}" role="img" class="chart" aria-label="{esc(M["fig_alt"])}">']
for i, (a, label) in enumerate(AREAS):
    x = 16 + i * (COLW + 14)
    mine = sorted((p for p in P if p["area"] == a), key=lambda p: p["pr"])
    svg.append(f'<text x="{x}" y="24" class="ct">{esc(label)}</text>')
    svg.append(f'<text x="{x}" y="42" class="cv">{len(mine)} PR{"s" if len(mine) != 1 else ""}</text>')
    for j, p in enumerate(mine):
        y = TOP + j * (BOXH + GAP)
        tone = V[p["verdict"]][1]
        svg.append(f'<a href="#pr-{p["pr"]}"><rect x="{x}" y="{y}" width="{COLW}" height="{BOXH}" rx="6" class="box {tone}"/>'
                   f'<text x="{x + 10}" y="{y + 20}" class="bl"><tspan class="bn">#{p["pr"]}</tspan> {esc(p["short"])}</text></a>')
svg.append("</svg>")
fig = "\n".join(svg)

# the thumbnail: the boxes alone, in their colours
LIGHT = {"warn": "#b45309", "good": "#15803d", "accent2": "#0e7490", "bad": "#b91c1c", "muted": "#8b939e"}
DARK = {"warn": "#fbbf24", "good": "#4ade80", "accent2": "#67e8f9", "bad": "#f87171", "muted": "#a2a9b3"}
rule = lambda pal: "".join(f".{k}{{fill:{v}}}" for k, v in pal.items())
tb = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180">',
      f'<style>{rule(LIGHT)}@media (prefers-color-scheme: dark) {{{rule(DARK)}}}</style>']
for i, (a, _) in enumerate(AREAS):
    mine = sorted((p for p in P if p["area"] == a), key=lambda p: p["pr"])
    for j, p in enumerate(mine):
        tb.append(f'<rect x="{22 + i * 72}" y="{20 + j * 24}" width="62" height="18" rx="4" class="{V[p["verdict"]][1]}"/>')
tb.append("</svg>")
os.makedirs("021/img", exist_ok=True)
open("021/img/thumb.svg", "w").write("\n".join(tb) + "\n")


def chip(p):
    label, tone = V[p["verdict"]]
    return f'<span class="chip {tone}">{esc(label)}</span>'


table = "\n".join(
    f'  <tr><td class="n"><a href="#pr-{p["pr"]}">#{p["pr"]}</a></td><td>{p["what"]}</td><td>{p["changes"]}</td><td>{chip(p)}</td></tr>'
    for a, _ in AREAS for p in sorted((q for q in P if q["area"] == a), key=lambda q: q["pr"]))


def section(p):
    li = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>" if xs else "<p class=\"note\">None.</p>"
    return f"""<section class="pr {V[p["verdict"]][1]}" id="pr-{p["pr"]}">
<h3>#{p["pr"]}: {esc(p["title"])} {chip(p)}</h3>
<p class="meta">Read at <code>{p["head"]}</code>{" · " + esc(p["note"]) if p.get("note") else ""}</p>
<p><b>What it changes.</b> {p["what"]}</p>
<p><b>Mechanism.</b> {p["mechanism"]}</p>
<p><b>Why the result is the same.</b> {p["argument"]}</p>
<p><b>What it assumes.</b> {p["assumes"]}</p>
<p><b>Where it is weakest.</b> {p["risk"]}</p>
<p><b>Tests that back it:</b></p>{li(p["tests_have"])}
<p><b>Tests to add:</b></p>{li(p["tests_missing"])}
</section>"""


sections = "\n\n".join(section(p) for a, label in AREAS
                       for p in sorted((q for q in P if q["area"] == a), key=lambda q: q["pr"]))
data_js = json.dumps({"meta": M, "prs": P}, ensure_ascii=False).replace("</", "<\\/")
lis = lambda xs: "".join(f"  <li>{x}</li>\n" for x in xs)

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(M["page_title"])}</title>
<style>
  :root {{
    --bg: #fbfaf7; --paper: #ffffff; --ink: #1f2328; --muted: #5b6470; --line: #e3e0d8;
    --accent: #6d28d9; --good: #15803d; --warn: #b45309; --bad: #b91c1c; --link: #1d4ed8; --accent2: #0e7490;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d;
      --accent: #c4b5fd; --good: #4ade80; --warn: #fbbf24; --bad: #f87171; --link: #93c5fd; --accent2: #67e8f9;
    }}
  }}
  :root[data-theme="dark"] {{ --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d;
    --accent: #c4b5fd; --good: #4ade80; --warn: #fbbf24; --bad: #f87171; --link: #93c5fd; --accent2: #67e8f9; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 system-ui, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 32px 16px 80px; }}
  h1 {{ font-size: 2em; line-height: 1.2; margin: 0 0 6px; }}
  h2 {{ font-size: 1.35em; margin: 48px 0 10px; padding-top: 8px; border-top: 2px solid var(--line); }}
  h3 {{ font-size: 1.08em; margin: 0 0 4px; }}
  p, li {{ max-width: 72ch; }}
  .sub {{ color: var(--muted); margin: 0 0 24px; }}
  .series {{ color: var(--muted); margin: 0 0 6px; font-size: 0.92em; }}
  .headline {{ background: var(--paper); border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; }}
  .headline ol > li {{ margin: 8px 0; }}
  a {{ color: var(--link); text-decoration: underline; text-underline-offset: 2px; }}
  a code {{ color: var(--link); }}
  code {{ font-size: 0.9em; background: color-mix(in srgb, var(--line) 50%, transparent); padding: 0 4px; border-radius: 4px; overflow-wrap: anywhere; }}
  figure.fig {{ background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; margin: 16px 0; }}
  figcaption {{ color: var(--muted); font-size: 0.9em; margin-top: 6px; max-width: 72ch; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.92em; }}
  th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; }}
  td.n {{ white-space: nowrap; }}
  .scroll {{ overflow-x: auto; }}
  .note {{ color: var(--muted); font-size: 0.9em; }}
  .chip {{ display: inline-block; font-size: 0.78em; font-weight: 600; white-space: nowrap; vertical-align: 2px;
           border-radius: 999px; padding: 1px 9px; border: 1px solid currentColor; }}
  .chip.warn {{ color: var(--warn); }} .pr.warn {{ border-left-color: var(--warn); }}
  svg.chart .box.warn {{ fill: color-mix(in srgb, var(--warn) 16%, var(--paper)); stroke: var(--warn); }}
  .chip.good {{ color: var(--good); }} .chip.accent2 {{ color: var(--accent2); }} .chip.bad {{ color: var(--bad); }} .chip.muted {{ color: var(--muted); }}
  .pr {{ background: var(--paper); border: 1px solid var(--line); border-left: 5px solid var(--line); border-radius: 8px; padding: 12px 16px; margin: 16px 0; }}
  .pr.good {{ border-left-color: var(--good); }} .pr.accent2 {{ border-left-color: var(--accent2); }} .pr.bad {{ border-left-color: var(--bad); }}
  .pr p {{ margin: 6px 0; }} .pr ul {{ margin: 2px 0 8px; }}
  .meta {{ color: var(--muted); font-size: 0.9em; }}
  svg.chart {{ width: 100%; height: auto; display: block; font: 12.5px system-ui, sans-serif; }}
  svg.chart .ct {{ fill: var(--ink); font-weight: 600; font-size: 14px; }}
  svg.chart .cv {{ fill: var(--muted); }}
  svg.chart .bl {{ fill: var(--ink); }} svg.chart .bn {{ font-weight: 700; }}
  svg.chart .box {{ stroke-width: 1.5; }}
  svg.chart .box.good {{ fill: color-mix(in srgb, var(--good) 16%, var(--paper)); stroke: var(--good); }}
  svg.chart .box.accent2 {{ fill: color-mix(in srgb, var(--accent2) 16%, var(--paper)); stroke: var(--accent2); }}
  svg.chart .box.bad {{ fill: color-mix(in srgb, var(--bad) 16%, var(--paper)); stroke: var(--bad); }}
  svg.chart .box.muted {{ fill: var(--paper); stroke: var(--muted); stroke-dasharray: 4 3; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 8px 0 0; font-size: 0.9em; }}
</style>
</head>
<body>
<main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>21<b>)</b></code> · {M["date"]}</p>
<h1>{M["title"]}</h1>
<p class="sub">{M["sub"]}</p>

<div class="headline">
<p><b>Short answers.</b> {M["as_of"]}</p>
<ol>
{lis(M["answers"])}</ol>
</div>

<figure class="fig" id="map">
{fig}
<div class="legend">{" ".join(f'<span class="chip {tone}">{esc(label)}: {count[k]}</span>' for k, label, tone in VERDICTS)}</div>
<figcaption>{M["fig_caption"]}</figcaption>
</figure>

<h2 id="table">All {len(P)} PRs</h2>
<div class="scroll"><table>
  <tr><th>PR</th><th>What it changes</th><th>Can it change a type or a value?</th><th>Verdict</th></tr>
{table}
</table></div>

<h2 id="prs">Each PR's argument</h2>
<p>{M["prs_intro"]}</p>
{sections}

<h2 id="tests">What the tests check today, and what to add</h2>
{M["tests"]}

<h2 id="next">What next</h2>
<ol>
{lis(M["next"])}</ol>

<h2 id="method">How this was put together</h2>
<ul>
{lis(M["method"])}  <li><b>The data:</b> in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <code>021/data/prs.json</code> and <code>021/data/meta.json</code>; the page is made by <code>021/drivers/gen021.py</code>.</li>
</ul>
</main>
<script type="application/json" id="report-data">{data_js}</script>
</body>
</html>
"""
open("021/index.html", "w").write(page)
print("wrote 021/index.html:", count)
