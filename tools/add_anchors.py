#!/usr/bin/env python3
"""An anchor for every section of a report, to name it in chat (Matthew, 2026-10-22: "anchors for each section, to make
referencing in chat easier"). Each <h2> and <h3> in <main> gets an id (kept if it has one, else made from its words, unique),
a "#" link to itself, and a "copy link" button that copies the section's public address,
https://matthewhammer.org/hazel/reports/NNN/#id, whichever copy of the page it is on. Figures and listings with ids keep them.
Run after the report's generator; running it twice changes nothing.
  python3 tools/add_anchors.py NNN/index.html"""
import re, sys, html as H

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
MARK = "<!-- anchors (tools/add_anchors.py) -->"
s = s.replace(MARK, "")
s = re.sub(r'<a class="anchor"[^>]*>#</a><button type="button" class="copyanchor"[^>]*>copy link</button>', "", s)
s = re.sub(r'<script id="anchors-js">.*?</script>', "", s, flags=re.S)
s = re.sub(r'<style id="anchors-css">.*?</style>', "", s, flags=re.S)

used = set(re.findall(r'\sid="([^"]+)"', s))
def slug(text):
    t = H.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:48].strip("-") or "section"
    base, k = t, 2
    while t in used: t, k = f"{base}-{k}", k + 1
    used.add(t); return t

def head(m):
    tag, attrs, inner = m.group(1), m.group(2), m.group(3)
    idm = re.search(r'\sid="([^"]+)"', attrs)
    hid = idm.group(1) if idm else slug(inner)
    if not idm: attrs += f' id="{hid}"'
    return (f'<{tag}{attrs}>{inner}<a class="anchor" href="#{hid}" aria-label="a link to this section">#</a>'
            f'<button type="button" class="copyanchor" data-id="{hid}" title="copy this section\'s address">copy link</button></{tag}>')

a, b = s.index("<main>"), s.index("</main>")
s = s[:a] + re.sub(r"<(h[23])([^>]*)>(.*?)</\1>", head, s[a:b], flags=re.S) + s[b:]

CSS = """<style id="anchors-css">
h2 .anchor, h3 .anchor { margin-left: 8px; color: var(--muted); text-decoration: none; font-weight: 400; opacity: 0.35; }
h2:hover .anchor, h3:hover .anchor, .anchor:focus { opacity: 1; }
.copyanchor { margin-left: 6px; font: 400 0.62em system-ui, sans-serif; vertical-align: middle; padding: 1px 6px; border-radius: 6px;
  border: 1px solid var(--line); background: var(--paper); color: var(--muted); cursor: pointer; opacity: 0.45; }
h2:hover .copyanchor, h3:hover .copyanchor, .copyanchor:focus { opacity: 1; }
.copyanchor.done { color: var(--good); border-color: var(--good); opacity: 1; }
:target { scroll-margin-top: 12px; }
</style>"""
JS = """<script id="anchors-js">
/* each section's "copy link": its public address, whichever copy of the page this is (tools/add_anchors.py) */
(() => {
  const n = (location.pathname.match(/(\\d{3})\\/?(index\\.html)?$/) || [])[1];
  const base = n ? "https://matthewhammer.org/hazel/reports/" + n + "/" : location.origin + location.pathname;
  document.querySelectorAll(".copyanchor").forEach(b => b.addEventListener("click", async () => {
    const url = base + "#" + b.dataset.id;
    try { await navigator.clipboard.writeText(url); b.textContent = "copied"; b.classList.add("done"); }
    catch (e) { prompt("this section's address", url); }
    setTimeout(() => { b.textContent = "copy link"; b.classList.remove("done"); }, 1500);
  }));
})();
</script>"""
s = s.replace("</head>", CSS + "\n</head>", 1)
s = s.replace("</body>", MARK + "\n" + JS + "\n</body>", 1)
open(p, "w", encoding="utf-8").write(s)
count = s.count('class="anchor"')
print(f"anchors: {p}: {count} sections")
