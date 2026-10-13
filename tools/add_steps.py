"""Give each issue's "What next" steps a link and a "copy for a ticket"
button: the copied text names the issue, the step and its URL, so pasted to
Claude it asks for a ticket for that step. Idempotent (between markers)."""
import sys, re
BEGIN, END = "<!-- steps: begin -->", "<!-- steps: end -->"
SNIPPET = BEGIN + r'''
<style>
  button.mint { margin-left: 4px; font: inherit; font-size: 0.75em; padding: 0 6px; border: 1px solid var(--line, #ccc);
    border-radius: 4px; background: transparent; color: var(--muted, #666); cursor: pointer; vertical-align: 1px; }
  button.mint:hover { color: inherit; }
  button.mint.done { color: var(--good, #15803d); border-color: var(--good, #15803d); }
  a.step-link { color: var(--muted, #666); text-decoration: none; font-size: 0.85em; margin-left: 4px; }
  a.step-link:hover { text-decoration: underline; }
  li:target { background: color-mix(in srgb, var(--good, #15803d) 12%, transparent); border-radius: 6px; }
</style>
<script>
/* Each "What next" step: a link to it, and a button copying a request to
   mint a ticket for it (to paste to Claude): the issue, the step, its URL. */
(() => {
  const h = document.getElementById("next");
  if (!h) return;
  let list = h.nextElementSibling;
  while (list && !/^(OL|UL)$/.test(list.tagName)) {
    if (list.tagName === "H2") return;
    list = list.nextElementSibling;
  }
  if (!list) return;
  const m = (document.querySelector(".series") || document.body).textContent.match(/Issue (\d{3})/);
  const issue = m ? m[1] : "?";
  const base = "http://matthewhammer.org/hazel/performance-analysis/" + issue + "/";
  [...list.children].filter(li => li.tagName === "LI").forEach((li, i) => {
    const n = i + 1;
    if (!li.id) li.id = "step-" + n;
    const b = li.querySelector("b, strong");
    const title = (b ? b.textContent : li.textContent).replace(/\s+/g, " ").trim().replace(/[:.,;]$/, "").slice(0, 160);
    const url = base + "#" + li.id;
    const text = "Mint a ticket for this step: Hazel performance analysis, issue " + issue +
      ", What next, step " + n + ': "' + title + '". ' + url;
    const a = document.createElement("a");
    a.href = "#" + li.id; a.className = "step-link"; a.textContent = "#" + n; a.title = "A link to this step";
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "mint"; btn.textContent = "copy for a ticket";
    btn.title = "Copies a request to mint a ticket for this step, to paste to Claude";
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(text); }
      catch (_) {
        const t = document.createElement("textarea"); t.value = text; document.body.append(t);
        t.select(); document.execCommand("copy"); t.remove();
      }
      btn.textContent = "copied"; btn.classList.add("done");
      setTimeout(() => { btn.textContent = "copy for a ticket"; btn.classList.remove("done"); }, 1500);
    });
    li.append(" ", a, " ", btn);
  });
  if (location.hash) { const t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
})();
</script>
''' + END
for path in sys.argv[1:]:
    s = open(path).read()
    if BEGIN in s:
        s = s[:s.index(BEGIN)] + SNIPPET + s[s.index(END) + len(END):]
    else:
        assert s.count("</body>") == 1, path
        s = s.replace("</body>", SNIPPET + "\n</body>")
    open(path, "w").write(s)
    print("steps added:", path)
