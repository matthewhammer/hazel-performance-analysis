#!/usr/bin/env python3
"""^report(22)'s page: reads 022/data/credits.json and writes 022/index.html. Run from the repository's root,
then the series tools (report_refs, link_prs, add_theme).
  python3 022/drivers/gen022.py"""
import json, html

D = json.load(open("022/data/credits.json"))
esc = html.escape
W = "https://andrewblinn.com/hazel/weekly/issues/"
rows = "\n".join(
    f'  <tr><td class="n"><a href="{W}{c["issue"]}/">{c["issue"]}</a></td><td>{esc(c["where"])}</td>'
    f'<td>{esc(c["says"])}</td><td>{c["fact"]}</td></tr>' for c in D["corrections"])
lis = lambda xs: "".join(f"  <li>{x}</li>\n" for x in xs)
data_js = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(D["page_title"])}</title>
<style>
  :root {{ --bg: #fbfaf7; --paper: #ffffff; --ink: #1f2328; --muted: #5b6470; --line: #e3e0d8; --accent: #6d28d9; --link: #1d4ed8; }}
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d; --accent: #c4b5fd; --link: #93c5fd; }} }}
  :root[data-theme="dark"] {{ --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d; --accent: #c4b5fd; --link: #93c5fd; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 system-ui, "Segoe UI", Roboto, sans-serif; }}
  main {{ max-width: 980px; margin: 0 auto; padding: 32px 16px 80px; }}
  h1 {{ font-size: 2em; line-height: 1.2; margin: 0 0 6px; }}
  h2 {{ font-size: 1.35em; margin: 48px 0 10px; padding-top: 8px; border-top: 2px solid var(--line); }}
  p, li {{ max-width: 72ch; }}
  .sub {{ color: var(--muted); margin: 0 0 24px; }}
  .series {{ color: var(--muted); margin: 0 0 6px; font-size: 0.92em; }}
  .headline {{ background: var(--paper); border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; }}
  .headline ol > li {{ margin: 8px 0; }}
  a {{ color: var(--link); text-decoration: underline; text-underline-offset: 2px; }}
  code {{ font-size: 0.9em; background: color-mix(in srgb, var(--line) 50%, transparent); padding: 0 4px; border-radius: 4px; overflow-wrap: anywhere; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.92em; }}
  th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; }}
  .scroll {{ overflow-x: auto; }}
</style>
</head>
<body>
<main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>{D["report"]}<b>)</b></code> · {D["date"]}</p>
<h1>{D["title"]}</h1>
<p class="sub">{D["sub"]}</p>
<div class="headline">
<p><b>Short answers.</b> {D["as_of"]}</p>
<ol>
{lis(D["answers"])}</ol>
</div>
<h2 id="corrections">Corrections</h2>
<p>Each passage that credits the wrong person, by issue, with where it is, what it says (in short) and the author on GitHub.</p>
<div class="scroll"><table>
  <tr><th>Issue</th><th>Where</th><th>Says</th><th>On GitHub</th></tr>
{rows}
</table></div>
<h2 id="method">How this was put together</h2>
<ul>
{lis(D["method"])}  <li><b>The data:</b> in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <code>022/data/credits.json</code>; the page is made by <code>022/drivers/gen022.py</code>.</li>
</ul>
</main>
<script type="application/json" id="report-data">{data_js}</script>
</body>
</html>
"""
open("022/index.html", "w").write(page)
print("wrote 022/index.html:", len(D["corrections"]), "corrections")
