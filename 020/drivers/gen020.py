#!/usr/bin/env python3
"""^report(20)'s page, an agenda: reads 020/data/agenda.json and writes 020/index.html. Kept as a work in
progress until the meeting: edit the JSON (an item, its status and as_of, the updated line), run this from the
repository's root, then the series tools (report_refs, link_prs, add_theme).
  python3 020/drivers/gen020.py"""
import json, html

A = json.load(open("020/data/agenda.json"))
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
<p class="series"><a href="../">Hazel performance analysis</a> · <code class="ref"><b>^report(</b>{A["report"]}<b>)</b></code> · agenda <span class="wip">work in progress</span> · started {A["started"]}, updated {esc(A["updated"])}</p>
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
open("020/index.html", "w").write(page)
print("wrote 020/index.html:", len(A["items"]), "items, updated", A["updated"])
