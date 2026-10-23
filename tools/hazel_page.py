#!/usr/bin/env python3
"""List the series' reports on the homepage's Hazel page.

  python3 tools/hazel_page.py [~/matthewhammer.github.io/hazel/index.html]

Reads each report's number, date and title from the cards in
series/index.html (newest first, as there) and writes them between the
page's <!-- reports: begin --> and <!-- reports: end --> markers, as links
to reports/NNN/. Idempotent: run it whenever a report is
published, after updating the series index."""
import os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/matthewhammer.github.io/hazel/index.html")
series = open(os.path.join(HERE, "index.html")).read()   # (the series index, the site's root since ^ticket(576))

cards = re.findall(r'<div class="num"><a href="(\d{3})/">.*?</a> · ([\d-]+)</div>\s*'
                   r'<div class="title"><a href="\d{3}/">(.*?)</a></div>', series, re.S)
if not cards:
    sys.exit("no report cards found in the series index (index.html)")
items = []
for nnn, date, title in cards:
    n = int(nnn)
    items.append(f'        <li><a href="reports/{nnn}/"><code class="ref"><b>^report(</b>{n}<b>)</b></code> '
                 f'<span class="t">{title}</span></a><span class="date">{date}</span></li>')
block = ("<!-- reports: begin -->\n      <ol class=\"reports\">\n" + "\n".join(items) +
         "\n      </ol>\n<!-- reports: end -->")

text = open(page).read()
new, k = re.subn(r"<!-- reports: begin -->.*?<!-- reports: end -->", lambda m: block, text, flags=re.S)
if k != 1:
    sys.exit(f"{page}: expected one reports block, found {k}")
if new != text:
    open(page, "w").write(new)
print(f"{page}: {len(items)} reports, ^report({int(cards[0][0])}) first")
