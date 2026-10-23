#!/usr/bin/env python3
"""^report(31): what reviewers have said on our open hazelgrove/hazel PRs that we have not acted on yet (^ticket(572)).
Reads data/pr-reviews.json: per PR, every piece of feedback from someone other than Matthew (reviews, review comments on
lines, comments), each judged open, answered or unclear, with the evidence."""
import os, json, html
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
D = json.load(open(os.path.join(R, "data", "pr-reviews.json")))
prs = D["prs"] if isinstance(D, dict) else D
none = D.get("no_feedback", []) if isinstance(D, dict) else []
esc = lambda s: html.escape(str(s or ""))
def quote(t, n=700):
    t = str(t or "").strip()
    return esc(t if len(t) <= n else t[:n] + " …")
KIND = {"review": "review", "review_comment": "on a line", "comment": "comment"}
def items_of(p, st): return [i for i in p.get("items", []) if i.get("status") == st]
order = sorted(prs, key=lambda p: (-len(items_of(p, "open")), -len(items_of(p, "unclear")), -int(p["number"])))
n_open = sum(len(items_of(p, "open")) for p in prs); n_unclear = sum(len(items_of(p, "unclear")) for p in prs)
with_open = [p for p in order if items_of(p, "open")]
def item_row(i):
    where = f" · <code>{esc(i.get('path'))}</code>{(':' + str(i.get('line'))) if i.get('line') else ''}" if i.get("path") else ""
    state = f" · {esc(i.get('state'))}" if i.get("state") else ""
    left = f"<p class=\"left\"><b>Left to do:</b> {esc(i.get('what_is_left'))}</p>" if i.get("what_is_left") and i.get("status") != "answered" else ""
    return (f"<div class=\"item {esc(i.get('status'))}\"><p class=\"meta\"><b>{esc(i.get('who'))}</b>, {KIND.get(i.get('kind'), esc(i.get('kind')))}{state}, "
            f"{esc((i.get('date') or '')[:10])}{where} · <a href=\"{esc(i.get('url'))}\">on GitHub</a></p>"
            f"<blockquote>{quote(i.get('text'))}</blockquote><p class=\"ev\"><b>{esc(i.get('status'))}:</b> {esc(i.get('evidence'))}</p>{left}</div>")
secs = []
for p in order:
    o, u, a = items_of(p, "open"), items_of(p, "unclear"), items_of(p, "answered")
    head = (f"<h2 id=\"pr-{p['number']}\">#{p['number']}: {esc(p['title'])}</h2>"
            f"<p class=\"note\"><code>{esc(p.get('head'))}</code> into <code>{esc(p.get('base'))}</code>{' · draft' if p.get('draft') else ''} · "
            f"last commit {esc((p.get('last_commit_date') or '')[:10])} · reviewers: {esc(', '.join(p.get('reviewers', [])))} · "
            f"<b>{len(o)} open</b>, {len(u)} unclear, {len(a)} answered</p>")
    body = "".join(item_row(i) for i in o + u)
    if a: body += f"<details><summary>{len(a)} answered</summary>{''.join(item_row(i) for i in a)}</details>"
    secs.append(head + body)
summary_rows = "".join(f"<tr><td><a href=\"#pr-{p['number']}\">#{p['number']}</a></td><td>{esc(p['title'])}</td><td>{esc(', '.join(p.get('reviewers', [])))}</td>"
                       f"<td class=n>{len(items_of(p, 'open'))}</td><td class=n>{len(items_of(p, 'unclear'))}</td><td class=n>{len(items_of(p, 'answered'))}</td></tr>" for p in order)
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reviews Still Open</title>
<meta name="description" content="What reviewers have said on Matthew's open hazelgrove/hazel pull requests that has not been acted on yet: each piece of feedback, whether a later commit or reply answered it, and what is left.">
<style>{STYLE}
.item {{ border-left: 4px solid var(--line); padding: 4px 12px; margin: 10px 0; }} .item.open {{ border-left-color: var(--warn); }} .item.unclear {{ border-left-color: var(--accent); }} .item.answered {{ border-left-color: var(--good); }}
.item blockquote {{ margin: 4px 0; padding: 4px 10px; background: var(--paper); border-radius: 6px; white-space: pre-wrap; font-size: 0.92em; }}
.item .meta, .item .ev, .item .left {{ margin: 3px 0; font-size: 0.9em; }}
</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>31<b>)</b></code> · reviews · 2026-10-23 · <span class="wip">work in progress</span></p>
<h1>Reviews Still Open</h1>
<p class="sub">Matthew: <q>look at our open PRs on hazel, find new reviews we haven't integrated yet. Create a report for each one, or a combined one --- with subsections.</q> (<code class="ref"><b>^ticket(</b>572<b>)</b></code>)</p>
<div class="headline"><p><b>Short answers.</b></p><ol class="ans">
<li><b>{n_open} pieces of feedback are open</b> across {len(with_open)} pull request{'s' if len(with_open) != 1 else ''}{(': ' + ', '.join(f'#{p["number"]}' for p in with_open)) if with_open else ''}; {n_unclear} more are unclear (the evidence below says why).</li>
<li><b>{len(prs)} of Matthew's open pull requests have feedback from someone else;</b> {len(none)} have none.</li>
<li><b>#2608 (Elaborations without whitespace): Alexander's "changes requested" of 10-21 has no reply and no commit after it.</b> He measured secondary (whitespace and comments) still surviving in elaborations across the docs corpus, about 13.5% of the marshaled size, mostly through <code>Typ.normalize</code>; he offers two fixes, asks for a test over every node kind in the corpus, and four comments on lines are untouched.</li>
<li><b>#2651 (A module's definition analyzed once): newest, today 11:34.</b> Andrew answered "yes" (a module defined as a function should be an error), and Alexander asks to either make the non-recursive analysis check it is a module, or give modules their own case apart from lets. Also unclear there: the <code>names_itself</code> thread, whose promised prototype is now draft #2717 (a module binding as a non-recursive let), which #2651 does not mention.</li>
<li><b>#2583 (Deep links) and #2613 (Colors): "changes requested" reviews still standing though the work is in.</b> #2583's rework landed in 077a68f9f8 (10-20), unannounced on the PR and not re-reviewed; one question, "Do we want to support tutorial sharing?", has no reply. #2613's blocking point was fixed (28fcabfffc), but its question to Andrew (keep the focused breadcrumb's light green pill?) has no answer.</li>
<li><b>#2681 (A value known to have a type is not walked again): a thought, not a request.</b> Alexander: "I'm still thinking about this. I feel like at a certain point we're getting back towards the cast calculus"; Matthew's later comment does not take it up.</li>
</ol></div>
<h2 id="summary">Pull request by pull request</h2>
<div class="scroll"><table><tr><th>PR</th><th>title</th><th>reviewers</th><th>open</th><th>unclear</th><th>answered</th></tr>{summary_rows}</table></div>
{''.join(secs)}
<h2 id="method">How this was put together</h2>
<p>For each of Matthew's open pull requests on hazelgrove/hazel (2026-10-23), every review (with its body), every comment on a line and every comment, from anyone other than Matthew and the bots, read through GitHub's API; each judged against the commits after it (by committer date) and the replies: <i>answered</i> when a later commit or a reply plainly settles it, <i>open</i> when nothing does or the reply promised work not done, <i>unclear</i> otherwise, with the evidence for each. Pull requests with no feedback from others: {', '.join(f'#{n}' for n in none) or 'none'}. The data is <code>031/data/pr-reviews.json</code>.</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE); print("031/index.html", len(PAGE), "prs", len(prs), "open", n_open)
