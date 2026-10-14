"""Our own numbers in our own syntax (Matthew's, 2026-10-14): the series is
made of REPORTS ("issue" is GitHub's word, for its issues), and a report is
^report(13), not "report 013", so a number needs no leading zeros and can
grow past 999; a ticket on the work dashboard is ^ticket(45). Shown in
monospace, with "^report(" and ")" in bold.

Turns each "report 013", "Report 013", "reports 009–012" and "reports 011
and 012" in a page's text into ^report chips, each a link to its report,
unless it is already inside a link or names the page it is on; and an
older chip, ^issue(N), into ^report(N). Leaves <head>,
<script>, <style> and <svg> alone. Adds the chips' style once (between
"refs" markers). Idempotent: run it on every new or changed page, like
add_steps.py, add_theme.py and link_prs.py. Each chip's link gets a hover
card, read live (ref_cards.html).

  python3 tools/report_refs.py NNN/index.html [index.html series/index.html ...]"""
import os, re, sys

BEGIN, END = "<!-- refs: begin -->", "<!-- refs: end -->"
STYLE = BEGIN + """
<style>
  code.ref { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; white-space: nowrap; }
  code.ref b { font-weight: 800; }
</style>
""" + END
SKIP = {"head", "script", "style", "svg", "title"}

def chip(kind, n):
    return f'<code class="ref"><b>^{kind}(</b>{int(n)}<b>)</b></code>'

def rewrite(text, linked, here, prefix):
    def one(n):
        c = chip("report", n)
        return c if linked or int(n) == here else f'<a href="{prefix}{int(n):03d}/">{c}</a>'
    text = re.sub(r"(?<![\w^])[Rr]eports\s+(\d{3})\s*([–-])\s*(\d{3})\b",
                  lambda m: one(m.group(1)) + m.group(2) + one(m.group(3)), text)
    text = re.sub(r"(?<![\w^])[Rr]eports?\s+(\d{3})\s*,?\s+and\s+(?:[Rr]eport\s+)?(\d{3})\b",
                  lambda m: one(m.group(1)) + " and " + one(m.group(2)), text)
    return re.sub(r"(?<![\w^])[Rr]eport\s+(\d{3})\b", lambda m: one(m.group(1)), text)

def run(path):
    src = open(path, encoding="utf-8").read()
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    here = int(d) if d.isdigit() else (1 if os.path.dirname(path) in ("", ".") else None)
    prefix = "" if d == "series" else "../"      # as published: the index sits beside the reports
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", src, flags=re.S)
    depth, a = {t: 0 for t in SKIP}, 0
    out = []
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name in SKIP and not p.endswith("/>"):
                depth[name] += -1 if m.group(1) else 1
            if name == "a":
                a += -1 if m.group(1) else 1
            out.append(p)
        elif p.startswith("<") or any(depth.values()):
            out.append(p)
        else:
            out.append(rewrite(p, a > 0, here, prefix))
    new = "".join(out).replace("<b>^issue(</b>", "<b>^report(</b>")
    if BEGIN in new:
        new = new[:new.index(BEGIN)] + STYLE + new[new.index(END) + len(END):]
    elif 'class="ref"' in new:
        new = new.replace("</body>", STYLE + "\n</body>", 1)
    # each chip's link gets a hover card, read live (ref_cards.html; a
    # report's card reads the report's page)
    new = re.sub(r"\s*<!-- ref-cards: begin -->.*?<!-- ref-cards: end -->", "", new, flags=re.S)
    if 'class="ref"' in new:
        cards = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref_cards.html"), encoding="utf-8").read()
        i = new.rfind("</body>")
        new = new[:i].rstrip() + "\n" + cards.replace("__TICKETS__", "null") + "\n" + new[i:]
    if new != src:
        open(path, "w", encoding="utf-8").write(new)
    print(f"{path}: ^report chips {src.count('<b>^report(</b>')} -> {new.count('<b>^report(</b>')}")

for path in sys.argv[1:]:
    run(path)
