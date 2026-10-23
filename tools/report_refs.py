"""Our own numbers in our own syntax (Matthew's, 2026-10-14): the series is
made of REPORTS ("issue" is GitHub's word, for its issues), and a report is
^report(13), not "report 013", so a number needs no leading zeros and can
grow past 999; a ticket on the work dashboard is ^ticket(45). Shown in
monospace, with "^report(" and ")" in bold.

Turns each "report 013", "Report 013", "reports 009–012" and "reports 011
and 012" in a page's text into ^report chips, each a link to its report,
unless it is already inside a link or names the page it is on; and an
older chip, ^issue(N), into ^report(N). Every chip a generator wrote itself
is linked too (Matthew, 2026-10-22: "scan all reports and hyperlink:
reports, tickets, PRs"): a ^report(N) to its report, a ^ticket(N) to its
row on the public work dashboard (DASHBOARD#ticket-N, which the dashboard
forwards to its closed pages once the ticket closes), and "ticket 540" in
the text becomes a linked chip, as "report 013" does. Leaves <head>,
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
SKIP = {"head", "script", "style", "svg", "title", "pre", "code"}

DASHBOARD = "https://matthewhammer.org/hazel/dashboard/"

def chip(kind, n):
    return f'<code class="ref"><b>^{kind}(</b>{int(n)}<b>)</b></code>'

# a chip already in the page, as one token while the page is walked (it spans tags)
CHIP = re.compile(r'<code class="ref"><b>\^(ticket|report|issue)\(</b>(\d+)<b>\)</b></code>')
MARK = "\x00{}:{}\x00"

def rewrite(text, linked, here, prefix):
    def one(n):
        c = chip("report", n)
        return c if linked or int(n) == here else f'<a href="{prefix}{int(n):03d}/">{c}</a>'
    text = re.sub(r"(?<![\w^])[Rr]eports\s+(\d{1,3})\s*([–-])\s*(\d{1,3})\b",
                  lambda m: one(m.group(1)) + m.group(2) + one(m.group(3)), text)
    text = re.sub(r"(?<![\w^])[Rr]eports\s+(\d{3})\s+to\s+(\d{3})\b",
                  lambda m: one(m.group(1)) + " to " + one(m.group(2)), text)
    text = re.sub(r"(?<![\w^])[Rr]eports?\s+(\d{1,3})\s*,?\s+and\s+(?:[Rr]eport\s+)?(\d{1,3})\b",
                  lambda m: one(m.group(1)) + " and " + one(m.group(2)), text)
    text = re.sub(r"(?<![\w^])[Rr]eport\s+(\d{1,3})\b", lambda m: one(m.group(1)), text)
    # ^report(27) or ^ticket(540) written as plain text: a chip, linked
    text = re.sub(r"(?<![\w])\^(ticket|report)\((\d+)\)", lambda m: "\x00" + m.group(1) + ":" + m.group(2) + "\x00", text)
    # "ticket 540", "Ticket 540": a linked chip
    text = re.sub(r"(?<![\w^])([Tt]icket)\s+(\d+)\b", lambda m: "\x00ticket:" + m.group(2) + "\x00", text)
    # the chips taken out before the walk, and the ones just made from "ticket N": linked here unless already in a link
    def back(m):
        kind, n = m.group(1), int(m.group(2))
        kind = "report" if kind == "issue" else kind
        c = chip(kind, n)
        if linked or (kind == "report" and n == here):
            return c
        return f'<a href="{prefix}{n:03d}/">{c}</a>' if kind == "report" else f'<a href="{DASHBOARD}#ticket-{n}">{c}</a>'
    return re.sub("\x00(ticket|report|issue):(\\d+)\x00", back, text)

def run(path):
    src = open(path, encoding="utf-8").read()
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    at_root = os.path.dirname(path) in ("", ".")
    here = int(d) if d.isdigit() else None
    # the series index sits beside the reports: the site's root here (since ^ticket(576); ^report(1) is 001/), reports/ on
    # the homepage, and series/ redirects
    prefix = "" if at_root or d in ("series", "reports") else "../"
    # chips become one text token each for the walk (see rewrite's back), except in <head>, scripts, styles and svg,
    # which the walk leaves alone: there they stay as they are
    body = CHIP.sub(lambda m: MARK.format(m.group(1), m.group(2)), src)
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", body, flags=re.S)
    depth, a = {t: 0 for t in SKIP}, 0
    out = []
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name == "body": depth["head"] = 0       # a page that never closes <head> (019's) ends it here
            if name in SKIP and not p.endswith("/>"):
                depth[name] += -1 if m.group(1) else 1
            if name == "a":
                a += -1 if m.group(1) else 1
            out.append(p)
        elif p.startswith("<") or any(depth.values()):
            out.append(re.sub("\x00(ticket|report|issue):(\\d+)\x00", lambda m: chip(m.group(1), m.group(2)), p))
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
    linked = lambda t, kind: len(re.findall(r'<a [^>]*><code class="ref"><b>\^' + kind + r'\(</b>', t))
    print(f"{path}: ^report chips {src.count('<b>^report(</b>')} -> {new.count('<b>^report(</b>')} ({linked(new, 'report')} linked), "
          f"^ticket chips {src.count('<b>^ticket(</b>')} -> {new.count('<b>^ticket(</b>')} ({linked(new, 'ticket')} linked)")

for path in sys.argv[1:]:
    run(path)
