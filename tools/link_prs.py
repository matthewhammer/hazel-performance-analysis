"""Every PR or issue number in a report is a link (Matthew's rule,
2026-10-14). Links each bare `#N` (hazelgrove/hazel) or `owner/repo#N` in
the page's text to GitHub, as /pull/N or /issues/N by what the number is
(asked of GitHub once, remembered in tools/pr_kinds.json). Leaves alone
what is already in a link, and <head>, <script>, <style> and <svg>, and
HTML entities (&#8212;). Idempotent, like add_steps.py: run it again after
regenerating.

Each such link also gets a card on hover or focus, as chat apps show one:
the title, its state (open, draft, merged, closed), who opened it, when,
when last updated, how many comments. The card asks GitHub live, once per
number per page load (GitHub's API answers pages from any site, up to 60
times an hour per network without signing in); if GitHub does not answer,
it shows what GitHub said when the page was built, saying so. The card's
script and that fallback go in one block before </body>, between
"pr-cards" markers, replaced on every run.

  python3 tools/link_prs.py NNN/index.html [more.html ...]"""
import json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = os.path.join(HERE, "pr_kinds.json")
kinds = json.load(open(KINDS)) if os.path.exists(KINDS) else {}

def kind(repo, n):
    key = f"{repo}#{n}"
    if key not in kinds:
        out = subprocess.run(["gh", "api", f"repos/{repo}/issues/{n}", "--jq",
                              'if .pull_request then "pull" else "issues" end'],
                             capture_output=True, text=True)
        k = out.stdout.strip()
        if k not in ("pull", "issues"):
            raise SystemExit(f"cannot tell what {key} is: {out.stderr.strip()[:200]}")
        kinds[key] = k
    return kinds[key]

REF = re.compile(r"(?<![\w&/#])(?:([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+))?#(\d{1,6})\b")
SKIP = {"a", "head", "script", "style", "svg", "title"}

def link_text(text):
    def sub(m):
        repo, n = m.group(1) or "hazelgrove/hazel", m.group(2)
        if not m.group(1) and len(n) < 4:
            return m.group(0)   # a bare short number (#3) is not a hazel PR
        return f'<a href="https://github.com/{repo}/{kind(repo, n)}/{n}">{m.group(0)}</a>'
    return REF.sub(sub, text)

LINK = re.compile(r'href="https://github\.com/([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)/(?:pull|issues)/(\d+)"')
info_cache = {}

def info(repo, n):
    key = f"{repo}#{n}"
    if key not in info_cache:
        out = subprocess.run(["gh", "api", f"repos/{repo}/issues/{n}", "--jq",
            '{title, state: (if .pull_request.merged_at then "merged" elif .draft then "draft" else .state end), '
            'author: .user.login, created: .created_at, updated: .updated_at, comments, '
            'kind: (if .pull_request then "pull" else "issues" end)}'], capture_output=True, text=True)
        try:
            info_cache[key] = json.loads(out.stdout)
        except ValueError:
            raise SystemExit(f"cannot read {key}: {out.stderr.strip()[:200]}")
    return info_cache[key]

CARDS = open(os.path.join(HERE, "pr_cards.html"), encoding="utf-8").read()

def add_cards(page):
    page = re.sub(r"\s*<!-- pr-cards: begin -->.*?<!-- pr-cards: end -->", "", page, flags=re.S)
    keys = sorted({(r, n) for r, n in LINK.findall(page)}, key=lambda k: (k[0], int(k[1])))
    if not keys:
        return page
    cached = {f"{r}#{n}": info(r, n) for r, n in keys}
    block = CARDS.replace("__CACHED__", json.dumps(cached, ensure_ascii=False).replace("</", "<\\/")) \
                 .replace("__BUILT__", time.strftime("%Y-%m-%d"))
    i = page.rfind("</body>")
    return page[:i].rstrip() + "\n" + block + "\n" + page[i:] if i >= 0 else page + block

def run(path):
    src = open(path, encoding="utf-8").read()
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", src, flags=re.S)
    depth = {t: 0 for t in SKIP}
    out = []
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name in SKIP and not p.endswith("/>"):
                depth[name] += -1 if m.group(1) else 1
            out.append(p)
        elif p.startswith("<") or any(depth.values()):
            out.append(p)
        else:
            out.append(link_text(p))
    new = add_cards("".join(out))
    if new != src:
        open(path, "w", encoding="utf-8").write(new)
    return src.count('href="https://github.com/'), new.count('href="https://github.com/')

for path in sys.argv[1:]:
    before, after = run(path)
    print(f"{path}: GitHub links {before} -> {after}")
json.dump(kinds, open(KINDS, "w"), indent=1, sort_keys=True)
