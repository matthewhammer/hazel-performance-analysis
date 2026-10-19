#!/usr/bin/env python3
"""^report(20)'s page, an agenda: reads 020/data/agenda.json and writes 020/index.html. Kept as a work in
progress until the meeting: edit the JSON (an item, its status and as_of, the updated line), run this from the
repository's root, then the series tools (report_refs, link_prs, add_theme).
  python3 020/drivers/gen020.py"""
import json, html, os, re

A = json.load(open("020/data/agenda.json"))
# the agenda is public (Matthew, 2026-10-19): a report it cites that is not published yet is a chip without a link,
# never a link that fails; it links once that report is published
PUBLISHED = os.path.expanduser("~/matthewhammer.github.io/hazel/reports")


def unlink_unpublished(s):
    return re.sub(r'<a href="\.\./(\d{3})/">(<code class="ref">.*?</code>)</a>',
                  lambda m: m.group(0) if os.path.isdir(os.path.join(PUBLISHED, m.group(1)))
                  else f'<span title="not published yet">{m.group(2)}</span>', s)
esc = html.escape
TONES = {"good", "warn", "accent", "accent2", "muted"}


def item(n, it):
    assert it["tone"] in TONES, it["tone"]
    ticket = (f' · <code class="ref"><b>^ticket(</b>{it["ticket"]}<b>)</b></code>'
              if it.get("ticket") else "")
    prs = ""
    if it.get("prs"):
        prs = ("<details><summary>The " + str(len(it["prs"])) + " PRs</summary><ul class=\"prs\">"
               + "".join(f"<li>#{p}</li>" for p in sorted(it["prs"])) + "</ul></details>")
    return f"""<section class="item {it["tone"]}" id="{it["id"]}">
<h3><span class="n">{n}.</span> {it["title"]} <span class="chip {it["tone"]}">{esc(it["status"])}</span></h3>
<p class="meta">Asked by {esc(it["asked"])}{ticket} · as of {esc(it["as_of"])}</p>
{it["body"]}
{prs}
<p class="ask"><b>For the meeting:</b> {it["meeting"]}</p>
</section>"""


rows = "\n".join(
    f'  <tr><td class="n">{n}</td><td><a href="#{it["id"]}">{it["title"]}</a></td>'
    f'<td><span class="chip {it["tone"]}">{esc(it["status"])}</span></td></tr>'
    for n, it in enumerate(A["items"], 1))
items = "\n\n".join(item(n, it) for n, it in enumerate(A["items"], 1))
data_js = json.dumps(A, ensure_ascii=False).replace("</", "<\\/")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(A["page_title"])}</title>
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
  body {{ margin: 0; background: var(--bg); color: var(--ink);
         font: 16px/1.55 system-ui, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 32px 16px 80px; }}
  h1 {{ font-size: 2em; line-height: 1.2; margin: 0 0 6px; }}
  h2 {{ font-size: 1.35em; margin: 48px 0 10px; padding-top: 8px; border-top: 2px solid var(--line); }}
  h3 {{ font-size: 1.1em; margin: 0 0 4px; }}
  p, li {{ max-width: 72ch; }}
  .sub {{ color: var(--muted); margin: 0 0 24px; }}
  .series {{ color: var(--muted); margin: 0 0 6px; font-size: 0.92em; }}
  .wip {{ display: inline-block; font-size: 0.8em; font-weight: 600; letter-spacing: 0.02em; color: var(--warn);
          border: 1px solid var(--warn); border-radius: 999px; padding: 0 8px; margin-left: 4px; }}
  .headline {{ background: var(--paper); border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; }}
  .headline ol > li {{ margin: 8px 0; }}
  a {{ color: var(--link); text-decoration: underline; text-underline-offset: 2px; }}
  a code {{ color: var(--link); }}
  code {{ font-size: 0.9em; background: color-mix(in srgb, var(--line) 50%, transparent); padding: 0 4px; border-radius: 4px; overflow-wrap: anywhere; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.95em; }}
  th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; }}
  td.n {{ font-variant-numeric: tabular-nums; color: var(--muted); }}
  .scroll {{ overflow-x: auto; }}
  .chip {{ display: inline-block; font-size: 0.78em; font-weight: 600; white-space: nowrap; vertical-align: 2px;
           border-radius: 999px; padding: 1px 9px; border: 1px solid currentColor; }}
  .chip.good {{ color: var(--good); }} .chip.warn {{ color: var(--warn); }} .chip.accent {{ color: var(--accent); }}
  .chip.accent2 {{ color: var(--accent2); }} .chip.muted {{ color: var(--muted); }}
  .item {{ background: var(--paper); border: 1px solid var(--line); border-left: 5px solid var(--line);
           border-radius: 8px; padding: 12px 16px; margin: 16px 0; }}
  .item.good {{ border-left-color: var(--good); }} .item.warn {{ border-left-color: var(--warn); }}
  .item.accent {{ border-left-color: var(--accent); }} .item.accent2 {{ border-left-color: var(--accent2); }}
  .item h3 .n {{ color: var(--muted); }}
  .meta {{ color: var(--muted); font-size: 0.9em; margin: 0 0 8px; }}
  .ask {{ border-top: 1px dashed var(--line); padding-top: 8px; margin-bottom: 2px; }}
  details {{ margin: 6px 0 10px; }} summary {{ cursor: pointer; color: var(--muted); }}
  ul.prs {{ columns: 2 22em; margin: 6px 0; }}
</style>
</head>
<body>
<main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>{A["report"]}<b>)</b></code> · agenda <span class="wip">work in progress</span> · started {A["started"]}, updated {esc(A["updated"])}</p>
<h1>{A["title"]}</h1>
<p class="sub">{A["sub"]}</p>

<div class="headline">
<p><b>In short.</b> As of {esc(A["updated"])}.</p>
<ol>
{"".join(f"  <li>{s}</li>" + chr(10) for s in A["short"])}</ol>
</div>

<h2 id="items">The items</h2>
<div class="scroll"><table>
  <tr><th></th><th>Item</th><th>Status</th></tr>
{rows}
</table></div>

{items}

<h2 id="if-time">If there is time</h2>
<ul>
{"".join(f"  <li>{s}</li>" + chr(10) for s in A["if_time"])}</ul>

<h2 id="method">How this agenda is kept</h2>
<ul>
{"".join(f"  <li>{s}</li>" + chr(10) for s in A["method"])}  <li><b>The data:</b> in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <code>020/data/agenda.json</code>; the page is made by <code>020/drivers/gen020.py</code>.</li>
</ul>
</main>
<script type="application/json" id="report-data">{data_js}</script>
</body>
</html>
"""
open("020/index.html", "w").write(unlink_unpublished(page))

# the series card's thumbnail: the meeting's date, and one bar per item in its status colour (then
# tools/theme_variants.py 020/img/thumb.svg makes its light and dark copies)
LIGHT = {"good": "#15803d", "warn": "#b45309", "accent": "#6d28d9", "accent2": "#0e7490", "muted": "#5b6470", "ink": "#1f2328"}
DARK = {"good": "#4ade80", "warn": "#fbbf24", "accent": "#c4b5fd", "accent2": "#67e8f9", "muted": "#a2a9b3", "ink": "#e8e6e3"}
rule = lambda pal: "".join(f".{k}{{fill:{v}}}" for k, v in pal.items())
month, day = {"10": "OCT", "11": "NOV", "12": "DEC"}.get(A["meeting"][5:7], A["meeting"][5:7]), str(int(A["meeting"][8:]))
step = min(21, 150 // max(1, len(A["items"])))
bars = "".join(
    f'<circle cx="140" cy="{24 + i * step + 6}" r="5" class="{it["tone"]}"/>'
    f'<rect x="152" y="{24 + i * step}" width="{min(150, 60 + 2 * len(re.sub("<[^>]+>|&[a-z]+;", "", it["title"])))}" height="12" rx="6" class="{it["tone"]}"/>'
    for i, it in enumerate(A["items"]))
os.makedirs("020/img", exist_ok=True)
open("020/img/thumb.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 180">\n'
    f'<style>{rule(LIGHT)}.box{{fill:none;stroke:#5b6470;stroke-width:2}}.m{{font:700 14px system-ui,sans-serif;letter-spacing:2px}}.d{{font:700 44px system-ui,sans-serif}}.mt{{fill:#ffffff}}'
    f'@media (prefers-color-scheme: dark) {{{rule(DARK)}.box{{fill:none;stroke:#a2a9b3;stroke-width:2}}.mt{{fill:#15171a}}}}</style>\n'
    f'<rect x="20" y="40" width="96" height="100" rx="10" class="box"/><rect x="20" y="40" width="96" height="26" rx="10" class="accent"/>'
    f'<rect x="20" y="56" width="96" height="10" class="accent"/>'
    f'<text x="68" y="58" text-anchor="middle" class="m mt">{month}</text>'
    f'<text x="68" y="122" text-anchor="middle" class="d ink">{day}</text>\n{bars}\n</svg>\n')
print("wrote 020/index.html:", len(A["items"]), "items, updated", A["updated"])
