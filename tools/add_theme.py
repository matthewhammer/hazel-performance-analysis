"""A theme switch on a page: Auto (the system's choice), Light or Dark (and, since ticket 296, the nav bar
Matthew's pages share, whose top carries the same choice),
remembered per site in localStorage ("theme") and applied before the page
paints. The page's CSS must honour :root[data-theme="light"|"dark"].
Idempotent (between markers).  python3 tools/add_theme.py page.html ..."""
import sys
HB, HE = "<!-- theme: head begin -->", "<!-- theme: head end -->"
BB, BE = "<!-- theme: begin -->", "<!-- theme: end -->"
# (ticket 296) the nav bar Matthew's pages share, with the theme: ~/matthewhammer.github.io/nav/agent-instructions.md
NB, NE = "<!-- nav: begin -->", "<!-- nav: end -->"
NAV = NB + '<meta name="theme-support" content="data-theme"><script src="https://matthewhammer.org/nav/nav.js"></script>' + NE
HEAD = HB + '''
<script>try { var t = localStorage.getItem("theme"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); } catch (e) {}</script>
''' + HE
BODY = BB + '''
<style>
  .theme-toggle { position: fixed; top: 10px; right: 10px; z-index: 30; font: 13px system-ui, sans-serif; padding: 3px 10px;
    border-radius: 999px; border: 1px solid var(--line, #ccc); background: var(--paper, Canvas); color: var(--muted, GrayText);
    cursor: pointer; opacity: 0.85; }
  .theme-toggle:hover { opacity: 1; color: var(--ink, CanvasText); }
  @media print { .theme-toggle { display: none; } }
</style>
<script>
/* The theme switch: Auto (the system's choice), Light, Dark; remembered for this site. */
(() => {
  const order = ["auto", "light", "dark"], label = { auto: "◐ auto", light: "☀ light", dark: "☾ dark" };
  const get = () => { try { return localStorage.getItem("theme") || "auto"; } catch (_) { return "auto"; } };
  const apply = m => m === "auto" ? document.documentElement.removeAttribute("data-theme")
                                  : document.documentElement.setAttribute("data-theme", m);
  const b = document.createElement("button");
  b.type = "button"; b.className = "theme-toggle";
  const show = () => { const m = get(); b.textContent = label[m] || label.auto;
    b.title = "Theme: " + m + ". Click for " + order[(order.indexOf(m) + 1) % 3] + "; remembered on this site."; };
  b.addEventListener("click", () => {
    const m = order[(order.indexOf(get()) + 1) % 3];
    try { m === "auto" ? localStorage.removeItem("theme") : localStorage.setItem("theme", m); } catch (_) {}
    apply(m); show();
  });
  window.addEventListener("storage", e => { if (e.key === "theme") { apply(get()); show(); } });
  show(); document.body.append(b);
})();
</script>
''' + BE
def put(s, begin, end, block, anchor, after):
    if begin in s:
        return s[:s.index(begin)] + block + s[s.index(end) + len(end):]
    assert s.count(anchor) >= 1, anchor
    return s.replace(anchor, anchor + "\n" + block, 1) if after else s.replace(anchor, block + "\n" + anchor, 1)
for path in sys.argv[1:]:
    s = open(path).read()
    s = put(s, NB, NE, NAV, '<meta charset="utf-8">', True)
    s = put(s, HB, HE, HEAD, '<meta charset="utf-8">', True)
    s = put(s, BB, BE, BODY, "</body>", False)
    open(path, "w").write(s)
    print("theme switch:", path)
