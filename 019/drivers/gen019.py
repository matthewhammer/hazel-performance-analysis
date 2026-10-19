#!/usr/bin/env python3
"""^report(19)'s page: reads 019/data/surfaces.json and 019/data/meta.json and writes 019/index.html and
019/img/thumb.svg. Run from the repository's root, then the series tools (report_refs, link_prs, add_steps,
add_theme) and tools/theme_variants.py 019/img/thumb.svg.
  python3 019/drivers/gen019.py"""
import json, html, re

D = "019/data/"
S = json.load(open(D + "surfaces.json"))
M = json.load(open(D + "meta.json"))
esc = html.escape

# the four ways the UI draws syntax, in order from most to least interactive
CLASSES = [
    ("edit", "Tiles you edit", "good"),
    ("select", "Read-only tiles you can select", "accent2"),
    ("static", "Tiles you can only look at", "accent"),
    ("text", "Plain text", "warn"),
]
CLS = {c: (label, var) for c, label, var in CLASSES}
by = {c: [s for s in S["surfaces"] if s["cls"] == c and s.get("seen") != "debug"] for c, _, _ in CLASSES}
debug = [s for s in S["surfaces"] if s.get("seen") == "debug"]
total = sum(len(v) for v in by.values())


def code(t):
    """`x` in data -> <code>x</code>, escaped"""
    return re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", esc(t))


# ---- Figure 1: every surface, as a chip in its class's column ----
W, COLW, X0, Y0, CH, GAP = 900, 218, 10, 64, 26, 6


def chip_w(s):
    return min(COLW - 8, 16 + 6.6 * len(s))


rows = max(len(v) for v in by.values())
H = Y0 + rows * (CH + GAP) + 16
svg = [f'<svg viewBox="0 0 {W} {H}" role="img" class="chart" aria-label="{esc(M["fig_alt"])}">']
for i, (c, label, var) in enumerate(CLASSES):
    x = X0 + i * (COLW + 6)
    svg.append(f'<rect x="{x}" y="6" width="{COLW}" height="{H - 12}" rx="10" class="col {c}"/>')
    svg.append(f'<text x="{x + 10}" y="28" class="ct">{esc(label)}</text>')
    svg.append(f'<text x="{x + 10}" y="47" class="cv">{len(by[c])} surface{"s" if len(by[c]) != 1 else ""}</text>')
    for j, s in enumerate(by[c]):
        y = Y0 + j * (CH + GAP)
        w = chip_w(s["short"])
        svg.append(f'<rect x="{x + 8}" y="{y}" width="{w:.0f}" height="{CH}" rx="6" class="chip {c}"/>'
                   f'<text x="{x + 16}" y="{y + 17}" class="cl">{esc(s["short"])}</text>')
svg.append("</svg>")
fig1 = "\n".join(svg)

# ---- thumbnail: the four counts as bars ----
tb = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180">',
      "<style>.e{fill:#15803d}.s{fill:#0e7490}.t{fill:#6d28d9}.x{fill:#b45309}.l{fill:#1f2328;font:600 15px system-ui,sans-serif}"
      "@media (prefers-color-scheme: dark) {.e{fill:#4ade80}.s{fill:#67e8f9}.t{fill:#c4b5fd}.x{fill:#fbbf24}.l{fill:#e8e6e3}}</style>"]
mx = max(len(v) for v in by.values())
for i, (c, k) in enumerate(zip([c for c, _, _ in CLASSES], ["e", "s", "t", "x"])):
    h = 120 * len(by[c]) / mx
    tb.append(f'<rect x="{30 + i * 72}" y="{150 - h:.0f}" width="50" height="{h:.0f}" rx="5" class="{k}"/>'
              f'<text x="{55 + i * 72}" y="{142 - h:.0f}" text-anchor="middle" class="l">{len(by[c])}</text>')
tb.append("</svg>")
open("019/img/thumb.svg", "w").write("\n".join(tb))


# ---- the tables, one per class ----
def table(c):
    out = ['<div class="scroll"><table>',
           "<tr><th>Surface</th><th>Shows</th><th>What a click does</th><th>Drawn by</th><th>Checked</th></tr>"]
    for s in by[c]:
        out.append(f'<tr id="s-{s["id"]}"><td><b>{esc(s["surface"])}</b>'
                   + (f'<div class="note">{code(s["where"])}</div>' if s.get("where") else "")
                   + f'</td><td>{esc(s["shows"])}</td><td>{code(s["interact"])}</td>'
                   f'<td>{"<br>".join(code(x) for x in s["code"])}</td>'
                   f'<td>{"in the app" if s["checked"] == "app" else "in the code"}</td></tr>')
    out.append("</table></div>")
    return "\n".join(out)


sections = []
for c, label, var in CLASSES:
    sections.append(f'<h3 id="{c}" class="k {c}">{esc(label)}: {len(by[c])}</h3>\n<p>{M["class_text"][c]}</p>\n{table(c)}')
if debug:
    sections.append('<h3 id="debug">Debug-only</h3>\n<p>' + M["debug_text"] + "</p>\n<ul>" +
                    "".join(f'<li><b>{esc(s["surface"])}</b> ({esc(s["shows"])}): {code(s["interact"])} '
                            f'{" ".join(code(x) for x in s["code"])}</li>' for s in debug) + "</ul>")

head = open("019/drivers/head-from-018.html").read()
head = re.sub(r"<title>.*?</title>", f"<title>{esc(M['tab_title'])}</title>", head)
extra_css = """
  .col { stroke: var(--line); stroke-width: 1; fill: var(--paper); }
  svg.chart .chip.edit { fill: color-mix(in srgb, var(--good) 18%, var(--paper)); stroke: var(--good); }
  svg.chart .chip.select { fill: color-mix(in srgb, var(--accent2) 18%, var(--paper)); stroke: var(--accent2); }
  svg.chart .chip.static { fill: color-mix(in srgb, var(--accent) 16%, var(--paper)); stroke: var(--accent); }
  svg.chart .chip.text { fill: color-mix(in srgb, var(--warn) 16%, var(--paper)); stroke: var(--warn); stroke-dasharray: 4 3; }
  h3.k { border-left: 6px solid var(--line); padding-left: 10px; }
  h3.k.edit { border-color: var(--good); } h3.k.select { border-color: var(--accent2); }
  h3.k.static { border-color: var(--accent); } h3.k.text { border-color: var(--warn); }
  .kinds { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 14px 0; }
  .kind { background: var(--paper); border: 1px solid var(--line); border-top-width: 4px; border-radius: 8px; padding: 8px 12px; font-size: 0.93em; }
  .kind.edit { border-top-color: var(--good); } .kind.select { border-top-color: var(--accent2); }
  .kind.static { border-top-color: var(--accent); } .kind.text { border-top-color: var(--warn); }
  .kind b { display: block; margin-bottom: 2px; }
</style>"""
head = head.replace("</style>", extra_css, 1)

kinds = '<div class="kinds">' + "".join(
    f'<div class="kind {c}"><b>{esc(label)}: {len(by[c])}</b>{M["kind_text"][c]}</div>' for c, label, _ in CLASSES) + "</div>"

data = {"report": 19, "title": M["title"], "date": M["date"], "question": M["question_plain"],
        "build": M["build"], "classes": {c: label for c, label, _ in CLASSES},
        "counts": {c: len(by[c]) for c, _, _ in CLASSES}, "surfaces": S["surfaces"]}
data_js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

page = f"""{head}
<body>
<main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>19<b>)</b></code> · {M["date"]}</p>
<h1>{M["title"]}</h1>
<p class="sub">{M["sub"]}</p>

<div class="headline">
<p><b>Short answers.</b> {M["as_of"]}</p>
<ol>
{"".join(f"  <li>{a}</li>" + chr(10) for a in M["answers"])}</ol>
</div>

<figure class="fig" id="map">
{fig1}
<figcaption>{M["fig_caption"]}</figcaption>
</figure>

<h2 id="kinds">Four ways to draw syntax</h2>
{M["kinds_intro"]}
{kinds}
{M["kinds_after"]}

<h2 id="surfaces">Every surface, by kind</h2>
<p>{M["surfaces_intro"]}</p>
{chr(10).join(sections)}

<h2 id="asks">What this means for the open asks</h2>
{M["asks"]}

<h2 id="next">What next</h2>
<ol>
{"".join(f"  <li>{a}</li>" + chr(10) for a in M["next"])}</ol>

<h2 id="method">How this was put together</h2>
<ul>
{"".join(f"  <li>{a}</li>" + chr(10) for a in M["method"])}</ul>
</main>
<script type="application/json" id="report-data">{data_js}</script>
</body>
</html>
"""
open("019/index.html", "w").write(page)
print("wrote 019/index.html:", {c: len(by[c]) for c, _, _ in CLASSES}, "debug", len(debug))
