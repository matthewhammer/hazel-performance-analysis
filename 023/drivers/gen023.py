#!/usr/bin/env python3
"""^report(23): ^report(18), followed up. Builds 023/index.html from 023/data/ (collect023.py), with ^report(18)'s styles.

  python3 gen023.py            (from the repository's root)

Then, as for every report: tools/report_refs.py, tools/link_prs.py, tools/add_steps.py and tools/add_theme.py on the page."""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "023", "data")
load = lambda n: json.load(open(os.path.join(D, n)))
runs, newest, prs, facts = load("runs.json"), load("newest-parents.json"), load("prs.json"), load("git-facts.json")
style = re.search(r"<style>(.*?)</style>", open(os.path.join(ROOT, "018", "drivers", "page018.html")).read(), re.S).group(1)
esc = html.escape
num = lambda n: f"{n:,}"
c = lambda sha: f'<a href="https://github.com/hazelgrove/hazel/commit/{sha}"><code>{sha}</code></a>'
run = lambda r: f'<a href="https://github.com/hazelgrove/hazel/actions/runs/{r}">run</a>'
mins = lambda s: f"{int(round(s / 60))} min" if s < 3600 else f"{int(s // 3600)} h {int(round((s % 3600) / 60))} min"

g = [r for r in runs["2635"]["runs"] if r["conclusion"] == "success"]
first, last = g[-1], g[0]          # GitHub lists the newest first
n_cancel = sum(r["conclusion"] == "cancelled" for r in runs["2635"]["runs"])
p97, p69, p87 = newest["2597"], newest["2469"], newest["2687"]
conf = facts["conflicts_2635_with_2597"]

# The five steps of ^report(18)'s What next, then and now
STEPS = [
    ("done", "Bring Andrew's per-member analysis on Modules II into #2635, adapted to Modules II part 3.",
     f"Done through #2699, merged into #2635 on 2026-10-19 (its merge commit {c('90ed4505bf')}): Andrew Blinn's per-member module analysis on Modules II, fitted to #2635's Modules II part 3, and one fix of its own, a livelit definition analyzed whole, not as a module ({c('223357135a')}). The 8 module cases pass."),
    ("half", "Give Editing.TableDecorations 1 an input whose error stays hidden under canonical completion, on #2597 too.",
     f"Done on #2635 ({c('27f100e37c')}: the row gets a wrong label, an error in table syntax that the projector hides, whatever completion does). Not yet on #2597, which still has the old input: it passes there only because #2597's dev predates canonical completion, and it is now {facts['2597_behind_dev']} commits behind dev."),
    ("done", "Find why macro-result.hz elaborates differently per item.",
     f"Found and fixed ({c('1131a457e4')}): a real bug in incremental statics. A livelit use records the livelit it applies as <code>^inc</code> among the names it depends on, but DefStatics named the livelit's own entry plain <code>inc</code>, so a changed livelit marked no use stale, and after an edit the use kept its old expansion. DefStatics is #2469's, so #2597, which has no DefStatics, never had the bug."),
    ("open", "Follow Cyrus's plan for merging into dev: first the PRs that have been waiting, then Andrew's modular editing PRs (#2469, with #2687 in it), then the livelits and performance PRs.",
     'For the meeting: <a href="../020/#merge">item 6 of the agenda for 2026-10-21</a>, ^report(20), with <a href="../020/#gate">item 7</a> (requiring the test jobs for merging into dev).'),
    ("half", "Merge the livelits branch into #2635 instead of cherry-picking, to clear the 25 conflicting files before its next CI run.",
     f"Done ({c('cf325d4f61')}: a merge keeping #2635's side, every one of #2597's commits since the merge base being there already): GitHub showed #2635 mergeable, and its CI ran green twice after. Since then #2597 took two more commits on 2026-10-19 ({c('54e5a66bf2')}, {c('8a03584ef6')}), and #2635 conflicts with it again, now in {len(conf)} file{'s' if len(conf) != 1 else ''} ({', '.join('<code>' + esc(f) + '</code>' for f in conf)})."),
]
MARK = {"done": ("good", "done"), "half": ("warn", "partly"), "open": ("cv2", "open")}


def steps_svg():
    W, h, gap, top = 920, 58, 10, 34
    H = top + len(STEPS) * (h + gap)
    rows = []
    short = ["Per-member analysis on Modules II, into #2635", "The table test's input, on #2635 and #2597", "Why macro-result.hz differs per item",
             "The merge plan for dev", "Merge the livelits branch into #2635"]
    now = ["#2699 merged: the 8 module cases pass", "#2635: done · #2597: still the old input", "a real bug in incremental statics, fixed",
           "for the 2026-10-21 meeting (^report(20), item 6)", f"merged · {len(conf)} file conflicts again since #2597 moved"]
    for i, ((st, _, _), s, n) in enumerate(zip(STEPS, short, now)):
        y = top + i * (h + gap)
        cls = {"done": "good", "half": "warn", "open": "cx"}[st]
        rows.append(f'<rect x="0" y="{y}" width="{W}" height="{h}" rx="8" class="cb" fill="none" stroke="currentColor" stroke-opacity="0.18"/>'
                    f'<rect x="0" y="{y}" width="10" height="{h}" rx="3" class="{cls}"/>'
                    f'<text x="24" y="{y + 24}" class="cl bn">{i + 1}. {esc(s)}</text>'
                    f'<text x="24" y="{y + 44}" class="cv">{esc(n)}</text>'
                    f'<text x="{W - 14}" y="{y + 34}" text-anchor="end" class="bn {cls}">{MARK[st][1]}</text>')
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="Report 18\'s five next steps and where each stands: '
            f'three done or partly done on #2635, one open for the meeting.">'
            f'<text x="0" y="18" class="ct">^report(18)\'s five next steps, as of {esc(facts["collected_at"][:16].replace("T", " "))} UTC</text>{"".join(rows)}</svg>')


def runs_svg():
    W, top = 920, 40
    lanes = [("2635", "#2635 livelits × modular editors"), ("2597", "#2597 the livelits branch"), ("2469", "#2469 modular editors"), ("2687", "#2687 modular editors + stdlib")]
    t0, t1 = "2026-10-19T15:55:00Z", max(r["created"] for k, _ in lanes for r in runs[k]["runs"])
    from datetime import datetime
    ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    a, b = ts(t0), ts(t1) + 1800
    x = lambda s: 250 + (ts(s) - a) / (b - a) * (W - 270)
    out = [f'<text x="0" y="18" class="ct">Every CI run since ^report(18) was written (2026-10-19 15:55 UTC)</text>']
    for i, (k, label) in enumerate(lanes):
        y = top + i * 40
        rs = runs[k]["runs"]
        tally = " · ".join(f"{sum(r['conclusion'] == cc for r in rs)} {nm}" for cc, nm in (("success", "green"), ("failure", "red"), ("cancelled", "cancelled"), ("in_progress", "running")) if any(r['conclusion'] == cc for r in rs))
        out.append(f'<text x="0" y="{y + 14}" class="cl bn">{esc(label)}</text><text x="0" y="{y + 30}" class="cv">{esc(tally)}</text>'
                   f'<line x1="250" x2="{W - 20}" y1="{y + 16}" y2="{y + 16}" class="grid"/>')
        for r in rs:
            cls = {"success": "good", "failure": "bad", "cancelled": "cx"}.get(r["conclusion"], "warn")
            out.append(f'<rect x="{x(r["created"]) - 3:.1f}" y="{y + 4}" width="6" height="24" rx="2" class="{cls}"><title>{esc(r["created"][:16])} {r["head"]} {r["conclusion"]}</title></rect>')
    H = top + len(lanes) * 40 + 4
    return (f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="CI runs on #2635, #2597, #2469 and #2687 since report 18: '
            f'#2635 two green and the rest cancelled by newer pushes; #2597 and #2469 green; #2687 one red, one green, one running.">{"".join(out)}</svg>')


rows35 = "".join(
    f'<tr><td class="n">{esc(r["created"][:16].replace("T", " "))}</td><td>{c(r["head"])}</td><td>{run(r["run"])}</td><td class="{ {"success": "good", "failure": "bad"}.get(r["conclusion"], "cv2") }">{esc(r["conclusion"])}</td>'
    + (f'<td class="n">{num(r["fast"]["tests"])}, {r["fast"]["failures"]} failed, {mins(r["fast"]["seconds"])}</td><td class="n">{num(r["full"]["tests"])}, {r["full"]["failures"]} failed, {mins(r["full"]["seconds"])}</td>'
       if "fast" in r and "full" in r else '<td class="cv2">(a newer push replaced it)</td><td></td>') + "</tr>"
    for r in runs["2635"]["runs"])
step_rows = "".join(f'<tr><td class="n">{i + 1}</td><td>{esc(then)}</td><td class="{MARK[st][0]}"><b>{MARK[st][1]}</b></td><td>{now}</td></tr>' for i, (st, then, now) in enumerate(STEPS))
parent_rows = "".join(
    f'<tr><td>#{k} {esc(lbl)}</td><td>{c(v["head"])}</td><td>{run(v["run"])}</td><td class="{ {"success": "good", "failure": "bad"}.get(v["conclusion"], "cv2") }">{esc(v["conclusion"])}</td>'
    f'<td class="n">{num(v["fast"]["tests"])}, {v["fast"]["failures"]} failed</td><td class="n">{num(v["full"]["tests"])}, {v["full"]["failures"]} failed</td></tr>'
    for k, lbl, v in (("2597", "the livelits branch", p97), ("2469", "modular editors", p69), ("2687", "modular editors + the standard library", p87)))

data = {"report": "^report(23)", "follows": "^report(18), https://matthewhammer.org/hazel/reports/018/", "collected_at": facts["collected_at"],
        "how": "GitHub's Actions API (each branch's CI runs since 2026-10-19T15:55Z; each finished run's Fast checks and Full tests job logs, read for alcotest's summary line) and git on a checkout of hazelgrove/hazel with the four branches fetched",
        "runs": runs, "newest_finished_parents": newest, "prs": prs, "git_facts": facts,
        "steps": [{"step": i + 1, "report18_said": then, "status": st, "now_html": now} for i, (st, then, now) in enumerate(STEPS)],
        "drivers": "023/drivers/collect023.py (collects), 023/drivers/gen023.py (this page)"}

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>#2635 Is Green</title>
<style>{style}
  .card {{ display: inline-block; min-width: 150px; margin: 4px 8px 4px 0; padding: 8px 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--paper); }}
  .card b {{ font-size: 1.5em; display: block; }}
</style>
</head>
<body>
<main>
<p class="series">Hazel reports · ^report(23) · draft, 2026-10-19</p>
<h1>#2635 Is Green</h1>
<p class="sub">^report(18) answered Cyrus's question of 2026-10-16, why CI fails on #2635 (livelits × modular editors), with three causes, and ended with five next steps. What happened to each step, and what is known now? Matthew asked on 2026-10-19, once the agenda for the next meeting with Cyrus, ^report(20), could mark #2635 green.</p>

<div class="headline">
<p><b>Short answers.</b> As of {esc(facts['collected_at'][:16].replace('T', ' '))} UTC (2026-10-19 evening, Mountain time). Every run is linked below, and its numbers are in this page's data.</p>
<ol>
<li><b>#2635 has passed CI twice, its first green runs since it was made on 2026-10-01.</b> First on {c(first['head'])}, the merge of #2699: Fast checks ran {num(first['fast']['tests'])} tests and Full tests {num(first['full']['tests'])}, none failing ({mins(first['full']['seconds'])} for Full tests). Then on {c(last['head'])}, one more commit on top, with the same counts. ^report(18) counted 97 runs and none green; since then 2 green, 0 red, and {n_cancel} cancelled by a newer push.
<div><span class="card"><b class="bad">0 of 97</b>runs green before ^report(18)</span><span class="card"><b class="good">2 of 2</b>finished runs green since</span></div></li>
<li><b>Each of ^report(18)'s three causes is fixed on #2635, and one was a real bug.</b> The 8 module cases pass with Andrew Blinn's per-member analysis on Modules II (through #2699); the table test has an input whose error the table hides whatever completion does ({c('27f100e37c')}); and the corpus mismatch was incremental statics keeping a livelit use's old expansion after the livelit changed ({c('1131a457e4')}).</li>
<li><b>Of its five next steps, two are done, two partly, and one is for the meeting.</b> Left over: #2597 still has the old table-test input (it will fail when #2597 next merges dev, now {facts['2597_behind_dev']} commits ahead of it); #2635 conflicts with its base again in {len(conf)} file, since #2597 took two commits that evening; and the plan for merging into dev is <a href="../020/#merge">item 6</a> of the agenda.</li>
<li><b>Both parents are green too</b>: #2597 at {c(p97['head'])} ({num(p97['fast']['tests'])} + {num(p97['full']['tests'])} tests) and #2469 at {c(p69['head'])} ({num(p69['fast']['tests'])} + {num(p69['full']['tests'])}). #2687's newest finished run failed one test of its own (below), which is Andrew's work in progress, not #2635's.</li>
</ol>
</div>

<figure class="fig">{steps_svg()}
<figcaption>^report(18)'s five next steps, each with where it stands. Green: done; amber: done on #2635 but not everywhere it is needed; grey: open, for the meeting on 2026-10-21.</figcaption></figure>

<h2 id="question">The question, and ^report(18)'s answer</h2>
<p>Cyrus asked, at his meeting with Matthew on 2026-10-16, why CI fails on #2635, the branch that merges modular editors (#2469) into the livelits branch (#2597). <a href="../018/">^report(18)</a> read all 97 of #2635's CI runs and found that it had never passed, failing the same tests every time, for three causes that came from the merge itself, with neither parent broken on its own:</p>
<ul>
<li><b>8 module tests:</b> #2469 analyzes a module one member at a time on dev's module statics, which Modules II (on the livelits branch only) replaced, so the merge analyzed a module literal whole and the tests' counts came out low (<a href="../018/#causes">cause 1</a>);</li>
<li><b>1 table test:</b> dev's canonical completion (#2374) closes the stray bracket the test relied on, so its error no longer landed in a hidden row (cause 2);</li>
<li><b>1 corpus test:</b> one livelits document elaborated differently per item than as a whole program, cause unknown when the report was first written (cause 3).</li>
</ul>
<p>Its update at 12:45 MDT the same day had a fix for each, and its <a href="../018/#next">What next</a> listed five steps. This report takes them one by one.</p>

<h2 id="steps">The five steps, then and now</h2>
<div class="scroll"><table>
<tr><th>Step</th><th>^report(18) said</th><th>Now</th><th>What happened</th></tr>
{step_rows}
</table></div>

<h2 id="runs">#2635's CI since then</h2>
<figure class="fig">{runs_svg()}
<figcaption>Every CI run on #2635, its two parents and #2687 from 15:55 UTC on 2026-10-19, when ^report(18)'s data was read, to {esc(facts['collected_at'][:16].replace('T', ' '))} UTC: one tick each, green passed, red failed, grey cancelled (a newer push replaced it), amber running. #2635's cancelled runs are four commits of its afternoon, among them the merge of the livelits branch, the table test's input and the statics fix, each replaced by the next push before its tests finished.</figcaption></figure>
<div class="scroll"><table>
<tr><th>Started (UTC)</th><th>Head</th><th>Run</th><th>Verdict</th><th>Fast checks</th><th>Full tests</th></tr>
{rows35}
</table></div>
<p>The two green runs are the first in #2635's history. Fast checks ran one test more than at {c('1131a457e4')} in ^report(18)'s update (5,552 then, 5,553 now). The times are the test suite's own, as alcotest reports them.</p>

<h2 id="parents">The parents and #2687</h2>
<div class="scroll"><table>
<tr><th>Branch</th><th>Head</th><th>Run</th><th>Verdict</th><th>Fast checks</th><th>Full tests</th></tr>
{parent_rows}
</table></div>
<p>#2597 took two commits on 2026-10-19 after ^report(18): a revealed livelit model selects whole tiles and no longer blanks the editor ({c('54e5a66bf2')}), and Γ outlines a type too large to show ({c('8a03584ef6')}). Both answer items of the agenda (<a href="../020/#model">item 2</a> and <a href="../020/#gamma">item 4</a>). #2687's newest finished run, on {c(p87['head'])}, passed Fast checks and failed one of {num(p87['full']['tests'])} Full tests: <code>WorldTree 3</code>, "the corpus in one document", which raised <code>Not_found</code>. That is #2687's own test on its own work, which goes red and back within hours, as ^report(18) found for #2469; a newer run of it was still going when this was collected.</p>

<h2 id="still">What is still open</h2>
<ul>
<li><b>#2597's table test.</b> Its input is still the stray bracket, and it passes only because #2597's dev ({c(facts['2597_dev_base'])}) is from before canonical completion. #2597 is {facts['2597_behind_dev']} commits behind dev (484 when ^report(18) counted), so this test will fail at its next merge of dev unless {c('27f100e37c')}'s input goes there first.</li>
<li><b>#2635's conflict with its base.</b> GitHub shows #2635 conflicting with #2597's branch again, in {len(conf)} file: {', '.join('<code>' + esc(f) + '</code>' for f in conf)}, from #2597's two commits of that evening. Like the 25 files of ^report(18), it is how #2635 is kept up to date (by taking #2597's work across), not a failure; a merge clears it before #2635's next run.</li>
<li><b>The merge plan for dev,</b> for the meeting (<a href="../020/#merge">^report(20), item 6</a>). #2635 is now {facts['2635_behind_dev']} commits behind dev, through #2469's own merges of dev; #2597 is {facts['2597_behind_dev']}.</li>
</ul>

<h2 id="next">What next</h2>
<ol>
<li>Give #2597 the table test's new input ({c('27f100e37c')}) before it next merges dev.</li>
<li>Merge #2597's two commits of 2026-10-19 into #2635, to clear the conflict in <code>test/Test_ContextInspector.re</code> before #2635's next CI run.</li>
<li>Settle the order of merging into dev at the meeting on 2026-10-21 (^report(20), item 6), and whether the test jobs are required for it (item 7).</li>
</ol>

<h2 id="method">How this was put together</h2>
<ul>
<li><b>The runs:</b> every CI run on the four branches created since 2026-10-19 15:55 UTC (when ^report(18)'s runs were listed), from GitHub's Actions API at {esc(facts['collected_at'])}. A run counts as green, red or cancelled as GitHub gives its conclusion.</li>
<li><b>The test counts:</b> each finished run's Fast checks and Full tests job logs, read for alcotest's summary line (tests run, failures, seconds), as ^report(18) read them.</li>
<li><b>The steps:</b> each fix's commit checked with git for being on #2635 and on #2597 (<code>merge-base --is-ancestor</code>), the conflict with <code>git merge-tree</code> between the two branches' heads, and how far behind dev each branch is from its merge base with dev.</li>
<li><b>Not done:</b> no tests were run for this report; every number is from CI's own runs.</li>
<li><b>The data:</b> in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/023/data">023/data/</a> (the runs, the parents' newest runs, the PRs, the git facts). The collector and this page's generator are in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/023/drivers">023/drivers/</a>.</li>
<li>#2635 is Matthew Hammer's branch, made and kept with Claude. #2469 and #2687 are Andrew Blinn's, and the per-member analysis on Modules II is his ({c('00bc805ca1')} on #2687). Modules II is Alexander's.</li>
</ul>
</main>
<script type="application/json" id="report-data">{json.dumps(data, ensure_ascii=False).replace('</', '<\\/')}</script>
</body>
</html>
"""
# (our syntax: written "report 018" in the prose, made a ^report chip by tools/report_refs.py; in a drawing, "report 18")
parts = re.split(r"(<svg.*?</svg>|<script.*?</script>|<title>.*?</title>)", page, flags=re.S)
page = "".join(re.sub(r"\^report\((\d+)\)", lambda m: "report %03d" % int(m.group(1)), x) if not re.match(r"<(svg|script|title)", x)
               else re.sub(r"\^report\((\d+)\)", lambda m: "report %d" % int(m.group(1)), x) if x.startswith("<svg") else x for x in parts)
open(os.path.join(ROOT, "023", "index.html"), "w").write(page)
print("wrote 023/index.html", len(page))
