#!/usr/bin/env python3
"""What is left unlinked in a page (Matthew, 2026-10-22: every report, ticket and PR a link, "as per our protocol"): chips
not inside a link (a report's chip of itself excepted), ^report(N) / ^ticket(N) / "ticket N" / "report NNN" in plain text,
and PR or issue numbers (#2681, owner/repo#4) not inside a link. Skips <head>, scripts, styles, svg, <pre> and <code>.
Prints each with a little context; exit status 1 if any.
  python3 tools/scan_refs.py PAGE..."""
import os, re, sys, html
SKIP = {"head", "script", "style", "svg", "title", "pre", "code"}
CHIP = re.compile(r'<code class="ref"><b>\^(ticket|report|issue)\(</b>(\d+)<b>\)</b></code>')
found = 0
for path in sys.argv[1:]:
    src = open(path, encoding="utf-8").read()
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    # report 1 is the series' first page: index.html here, 001/ on the homepage
    here = int(d) if d.isdigit() else (1 if os.path.dirname(path) in ("", ".") else None)
    body = CHIP.sub(lambda m: f"\x00{m.group(1)}:{m.group(2)}\x00", src)
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", body, flags=re.S)
    depth, a, ctx = {t: 0 for t in SKIP}, 0, ""
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name == "body": depth["head"] = 0       # a page that never closes <head> (019's) ends it here
            if name in SKIP and not p.endswith("/>"): depth[name] += -1 if m.group(1) else 1
            if name == "a": a += -1 if m.group(1) else 1
            continue
        if p.startswith("<"): continue
        t = p
        bad = []
        for c in re.finditer("\x00(ticket|report|issue):(\\d+)\x00", t):
            if a <= 0 and not any(depth[k] for k in ("head", "script", "style", "svg", "title")) and not (c.group(1) == "report" and int(c.group(2)) == here):
                bad.append(f"chip ^{c.group(1)}({c.group(2)})")
        if a <= 0 and not any(depth.values()):
            plain = CHIP.sub("", t.replace("\x00", " "))
            for c in re.finditer(r"(?<![\w])\^(ticket|report)\((\d+)\)", plain): bad.append(f"plain ^{c.group(1)}({c.group(2)})")
            for c in re.finditer(r"(?<![\w^])[Tt]ickets?\s+(\d+)\b", plain): bad.append(f"plain ticket {c.group(1)}")
            for c in re.finditer(r"(?<![\w^])[Rr]eports?\s+(\d{1,3})\b(?!\.\d|%)", plain):
                if int(c.group(1)) != here: bad.append(f"plain report {c.group(1)}")
            for c in re.finditer(r"(?<![\w/&])((?:[\w.-]+/[\w.-]+)?#\d{2,5})\b", plain): bad.append(f"PR/issue {c.group(1)}")
        for b in bad:
            found += 1
            print(f"{path}: {b}   ...{html.unescape(re.sub(chr(0) + '[^' + chr(0) + ']*' + chr(0), '[chip]', t)).strip()[:90]}")
sys.exit(1 if found else 0)
