#!/usr/bin/env python3
"""Split a theme-aware SVG into a light and a dark copy.

  python3 tools/theme_variants.py NNN/img/thumb.svg

An SVG shown with <img> follows the reader's system theme, never the page's
theme switch, so a page forced to light on a dark system shows a dark
drawing's pale text on a light card. The fix is two drawings and a page that
shows the one its theme asks for (see .thumb img.light / img.dark in
series/index.html).

The SVG keeps its light colours in plain rules and its dark ones in one
@media (prefers-color-scheme: dark) { ... } block. thumb-light.svg drops that
block; thumb-dark.svg unwraps it, so its rules come last and win. The original
file is left as it is, for anyone who opens it directly."""
import os, re, sys

for path in sys.argv[1:]:
    src = open(path).read()
    m = re.search(r"@media \(prefers-color-scheme: dark\) \{", src)
    if not m:
        sys.exit(f"{path}: no dark block")
    # the block's closing brace: count braces from its opening one
    depth, i = 0, m.end() - 1
    while True:
        depth += {"{": 1, "}": -1}.get(src[i], 0)
        if depth == 0:
            break
        i += 1
    inner = src[m.end():i]
    stem, ext = os.path.splitext(path)
    open(stem + "-light" + ext, "w").write(src[:m.start()].rstrip(" ") + src[i + 1:].lstrip("\n"))
    open(stem + "-dark" + ext, "w").write(src[:m.start()].rstrip(" ") + inner.strip("\n") + "\n" + src[i + 1:].lstrip("\n"))
    print(f"{path}: wrote {os.path.basename(stem)}-light{ext} and -dark{ext}")
