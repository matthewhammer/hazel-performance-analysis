#!/usr/bin/env python3
"""Draft cards on the series index, for the local preview only.

A report whose folder is not on the published site yet (no
~/matthewhammer.github.io/hazel/reports/NNN/) is a draft. It gets a card
like a published one, marked "draft", between the drafts markers at the
top of index.html. The block is hidden unless the page is served from
localhost, so publishing the index never shows a link that 404s.
(Matthew, 2026-10-23: "localhost:8131 -- should list the drafts, with
draft thumbnails and links now, and going forward.")

Run after making or publishing a report:  python3 tools/draft_cards.py
"""
import html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.expanduser("~/matthewhammer.github.io/hazel/reports")
BEGIN, END = "<!-- drafts: begin -->", "<!-- drafts: end -->"

def meta(n):
    s = open(os.path.join(ROOT, n, "index.html"), encoding="utf8").read()
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', s)
    return (t.group(1).strip() if t else f"Report {int(n)}"), (d.group(1) if d else "")

def thumb(n, alt):
    a = html.escape(alt, quote=True)
    if os.path.exists(os.path.join(ROOT, n, "img", "thumb-light.svg")):
        return (f'<a class="thumb" href="{n}/"><img class="light" src="{n}/img/thumb-light.svg" alt="{a}">'
                f'<img class="dark" src="{n}/img/thumb-dark.svg" alt="{a}"></a>')
    return f'<a class="thumb" href="{n}/"><span class="nothumb">no thumbnail yet</span></a>'

def card(n):
    title, desc = meta(n)
    return f"""    <li class="draft-card">
      {thumb(n, title)}
      <div>
      <div class="num"><a href="{n}/"><code class="ref"><b>^report(</b>{int(n)}<b>)</b></code></a> · <span class="draft">draft, not published</span></div>
      <div class="title"><a href="{n}/">{title}</a></div>
      <p class="blurb">{desc}</p>
      </div>
    </li>
"""

def main():
    drafts = sorted((n for n in os.listdir(ROOT) if re.fullmatch(r"\d{3}", n)
                     and os.path.exists(os.path.join(ROOT, n, "index.html"))
                     and not os.path.isdir(os.path.join(SITE, n))), reverse=True)
    block = (f'{BEGIN}\n  <ol class="issues drafts" hidden>\n' + "".join(map(card, drafts)) + "  </ol>\n"
             '  <script>if (/^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname)) document.querySelector("ol.drafts").hidden = false;</script>\n'
             f"  {END}")
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf8").read()
    if BEGIN in s:
        s = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda _: block, s, flags=re.S)
    else:
        s = s.replace('  <ol class="issues" reversed>', block + '\n  <ol class="issues" reversed>', 1)
    if ".draft {" not in s:
        s = s.replace("</style>", "  ol.drafts { margin-bottom: 0; }\n  .draft { color: #b45309; font-weight: 600; }\n  @media (prefers-color-scheme: dark) { :root:not([data-theme=\"light\"]) .draft { color: #fbbf24; } }\n  :root[data-theme=\"dark\"] .draft { color: #fbbf24; }\n  .draft-card .thumb img { border-style: dashed; }\n  .nothumb { display: block; padding: 40px 8px; text-align: center; border: 1px dashed var(--line); border-radius: 8px; color: GrayText; font-size: 12px; }\n</style>", 1)
    open(p, "w", encoding="utf8").write(s)
    print("drafts:", ", ".join(drafts) or "none")

if __name__ == "__main__":
    main()
