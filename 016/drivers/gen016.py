#!/usr/bin/env python3
"""^ticket(91): ^report(16)'s page (a draft), from the interleaved A/B runs in 016/data/.

  python3 gen016.py   # writes ~/hazel-perf-report/016/index.html
"""
import json, os, re, html, statistics

R = os.path.expanduser("~/hazel-perf-report")
D = os.path.join(R, "016", "data")
J = lambda f: json.load(open(os.path.join(D, f)))
runs = {("coalesce", "C"): J("coal_C.json"), ("coalesce", "B"): J("coal_B.json"),
        ("views-in-worker", "C"): J("views_C.json"), ("views-in-worker", "B"): J("views_B.json")}
css = re.search(r"<style>(.*?)</style>", open(os.path.join(R, "014", "index.html")).read(), re.S).group(1)
esc = html.escape
NAME = {"head": "#2635's head", "head-again": "the head again (A/A)", "coalesce": "newest preview only", "views-in-worker": "views in the worker"}
MODE = {"C": "the whole program", "B": "UX mode"}

def meas(run, build): return [x for x in run["drags"] if x["round"] >= 0 and x["build"] == build]
def med(xs): return statistics.median(xs)
def paired(run, build, k):
    out = []
    for r in range(run["rounds"]):
        h = [x for x in run["drags"] if x["round"] == r and x["build"] == "head"]; o = [x for x in run["drags"] if x["round"] == r and x["build"] == build]
        if h and o and h[0][k] is not None and o[0][k] is not None: out.append(o[0][k] - h[0][k])
    return out

def dotstrips(title, k, aria, lo=-3200, hi=1600, step=500, w=860):
    """per mode, per comparison: each round's difference from the head (dots), the median (a bar), zero dashed"""
    rows = []
    for mode in ("C", "B"):
        for proto in ("coalesce", "views-in-worker"):
            run = runs[(proto, mode)]
            rows.append((f"{MODE[mode]}: the head again (A/A)", f"in the {NAME[proto]} run", paired(run, "head-again", k), "muted"))
            rows.append((f"{MODE[mode]}: {NAME[proto]}", "", paired(run, proto, k), "good" if proto == "coalesce" else "accent"))
    x0, x1 = 330, w - 30
    sc = lambda v: x0 + (x1 - x0) * (max(lo, min(hi, v)) - lo) / (hi - lo)
    h = 50 + 38 * len(rows) + 50
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">{esc(title)}</text>']
    for t in range(-(-lo // step) * step, hi + 1, step):
        out.append(f'<line x1="{sc(t):.1f}" y1="34" x2="{sc(t):.1f}" y2="{h - 44}" class="{"diag" if t == 0 else "grid"}"/>'
                   f'<text x="{sc(t):.1f}" y="{h - 28}" text-anchor="middle" class="cv">{t / 1000:+g} s</text>')
    for i, (lab, sub, ds, cls) in enumerate(rows):
        y = 50 + 38 * i
        if i and i % 4 == 0:
            out.append(f'<line x1="20" y1="{y - 10}" x2="{w - 20}" y2="{y - 10}" class="grid"/>')
        out.append(f'<text x="{x0 - 12}" y="{y + 4}" text-anchor="end" class="cl"{" font-weight=\"600\"" if cls != "muted" else ""}>{esc(lab)}</text>'
                   + (f'<text x="{x0 - 12}" y="{y + 18}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>' if sub else ""))
        for v in ds:
            out.append(f'<circle cx="{sc(v):.1f}" cy="{y}" r="5" style="fill: var(--{cls})" opacity="0.75"/>')
        m = med(ds)
        out.append(f'<line x1="{sc(m):.1f}" y1="{y - 11}" x2="{sc(m):.1f}" y2="{y + 11}" style="stroke: var(--ink)" stroke-width="2.5"/>'
                   f'<text x="{sc(m):.1f}" y="{y - 14}" text-anchor="middle" class="cv" font-size="11">{m / 1000:+.2f} s</text>')
    out.append(f'<text x="{w / 2}" y="{h - 8}" text-anchor="middle" class="cv">each dot one round: the build\'s drag minus the head\'s drag in that round; the black bar the median; left of the dashed line is better</text></svg>')
    return "".join(out)

def bars(aria, w=860):
    """frozen per drag, median and range, per build, in each of the four runs (a header row per run)"""
    x0, x1, vmax = 250, w - 70, 5600
    sc = lambda v: x0 + (x1 - x0) * v / vmax
    y, body = 40, []
    for mode in ("C", "B"):
        for proto in ("coalesce", "views-in-worker"):
            run = runs[(proto, mode)]
            body.append(f'<text x="20" y="{y + 14}" class="cl" font-weight="700">{esc(MODE[mode][0].upper() + MODE[mode][1:])}: the run with {esc(NAME[proto])}</text>')
            y += 24
            for b in ("head", "head-again", proto):
                xs = [x["stalled_ms"] for x in meas(run, b)]
                m, lo, hi = med(xs), min(xs), max(xs)
                cls = "bad" if b.startswith("head") else ("good" if b == "coalesce" else "accent")
                body.append(f'<text x="{x0 - 10}" y="{y + 13}" text-anchor="end" class="cl">{esc(NAME[b])}</text>'
                            f'<rect x="{x0}" y="{y}" width="{sc(m) - x0:.1f}" height="18" rx="3" style="fill: var(--{cls})" opacity="{0.5 if b == "head-again" else 1}"/>'
                            f'<line x1="{sc(lo):.1f}" y1="{y + 9}" x2="{sc(hi):.1f}" y2="{y + 9}" class="rng"/>'
                            f'<text x="{sc(hi) + 6:.1f}" y="{y + 14}" class="cl" font-weight="600">{m / 1000:.2f}</text>')
                y += 26
            y += 12
    h = y + 30
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">Frozen during one 1.5-second drag (s): median of 10, with fastest to slowest</text>']
    for t in range(0, 5001, 1000):
        out.append(f'<line x1="{sc(t):.1f}" y1="34" x2="{sc(t):.1f}" y2="{h - 30}" class="grid"/><text x="{sc(t):.1f}" y="{h - 14}" text-anchor="middle" class="cv">{t / 1000:g} s</text>')
    return "".join(out + body) + "</svg>"

# ---------- numbers ----------
cC, cB, vC, vB = runs[("coalesce", "C")], runs[("coalesce", "B")], runs[("views-in-worker", "C")], runs[("views-in-worker", "B")]
def s(run, b, k): return med([x[k] for x in meas(run, b) if x[k] is not None])
def pd(run, b, k): ds = paired(run, b, k); return med(ds), sum(1 for x in ds if x < 0), sum(1 for x in ds if x > 0), min(ds), max(ds)
cs = meas(cC, "coalesce"); sent, coal, inp = med([x["repaints_sent"] for x in cs]), med([x["repaints_coalesced"] for x in cs]), med([x["inputs"] for x in cs])
fig_bars = bars("Frozen time per drag, medians: whole program, head about 4 s, coalescing 2.2 s, views in the worker about 4.1 s; UX mode, all between about 1 and 2 s.")
fig_frozen = dotstrips("Frozen during a drag: each build minus the head, round by round", "stalled_ms",
                       "Dot strips of paired differences in frozen time. Whole program: newest preview only, all ten dots left of zero, median -1.72 s; the A/A pairs scatter around zero. Views in the worker scatter around zero. UX mode: every comparison, A/A included, scatters by up to two seconds.")
fig_release = dotstrips("From letting go to the final picture: each build minus the head", "release_to_redraw_ms",
                        "Dot strips of paired differences in release to redraw: all comparisons scatter near zero, except views in the worker in UX mode, mostly right of zero, median +0.28 s.", lo=-1400, hi=1400, step=500)

def row(mode, run, proto):
    rows = ""
    for b in ("head", "head-again", proto):
        rows += (f'<tr><td>{MODE[mode]}</td><td>{esc(NAME[b])}</td><td class="n">{s(run, b, "stalled_ms") / 1000:.2f}</td><td class="n">{s(run, b, "longest_gap_ms"):.0f}</td>'
                 f'<td class="n">{s(run, b, "release_to_redraw_ms") / 1000:.2f}</td><td class="n">{s(run, b, "inputs"):g}</td>'
                 + (f'<td class="n">{pd(run, b, "stalled_ms")[0] / 1000:+.2f} ({pd(run, b, "stalled_ms")[1]} lower, {pd(run, b, "stalled_ms")[2]} higher)</td>'
                    f'<td class="n">{pd(run, b, "release_to_redraw_ms")[0] / 1000:+.2f} ({pd(run, b, "release_to_redraw_ms")[1]} lower, {pd(run, b, "release_to_redraw_ms")[2]} higher)</td>' if b != "head" else "<td>—</td><td>—</td>") + "</tr>")
    return rows
table = ('<div class="scroll"><table><tr><th>Mode</th><th>Build</th><th>Frozen (s)</th><th>Longest gap (ms)</th><th>Letting go to final picture (s)</th><th>Inputs</th>'
         '<th>Frozen, minus the head, round by round</th><th>Final picture, minus the head</th></tr>' +
         row("C", cC, "coalesce") + row("B", cB, "coalesce") + row("C", vC, "views-in-worker") + row("B", vB, "views-in-worker") + "</table></div>")

data = {"report": 16, "title": "Two fixes for a drag, measured side by side", "date": "2026-10-15", "published": "2026-10-16",
        "question": "On #2635, a 1.5-second drag of Full Body's arm-length slider freezes the page for 3 to 4 seconds. Does keeping only the newest preview while one is on its way, or evaluating the livelit views in the worker, shorten that? (^ticket(91) and ^ticket(18))",
        "builds": {"head": "hazelgrove/hazel#2635 at 032fe3aca6", "coalesce": "3eb4489124 on 032fe3aca6 (local branch perf/2635-coalesce-drag-repaint), with 2db6ee4c30's counters", "views-in-worker": "4c9331d13c on 032fe3aca6 (local branch exp/2635-views-in-worker-032fe: EXPERIMENT 3, whole programs fold livelit views into the worker's run)"},
        "method": "interleaved A/B: one headless Firefox 157, one tab per build, all loaded at once; the head twice, under two host names (two origins, each with its own saved state: an A/A pair); one warm-up drag per tab, then 10 rounds, in each every tab one real drag (WebDriver: down, 15 moves of 100 ms, up) to a value new to it; the tabs' order turned round each round; per drag: frames, longest gap, frozen (gaps over 50 ms), letting go to the final picture (polled every 50 ms), the slider's inputs, repaints sent and coalesced (the coalescing build's counters)",
        "runs": {f"{p} {m}": r for (p, m), r in runs.items()}, "files": "https://github.com/matthewhammer/hazel-performance-analysis/tree/main/016/data"}

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Two Fixes for a Drag</title>
<style>{css}</style>
</head>
<body>
<main>
<p class="series"><a href="../">Hazel performance analysis</a> · report 016 · 2026-10-15</p>
<h1>Two fixes for a drag, measured side by side</h1>
<p class="sub">On <a href="https://github.com/hazelgrove/hazel/pull/2635">#2635</a>, dragging a slider in the Livelit Playground's Full Body slide for a second and a half froze the page for about three seconds in report 015, and longer for a longer drag. Every value a drag passes through makes the page recalculate, and a drag passes through dozens. Two fixes were built on the way: keeping only the newest preview while one is on its way, and evaluating the livelit views in the evaluation worker instead of on the page. Measured one session at a time, earlier the same day, neither could be told apart from the drift between sessions. This report measures them again with the builds side by side, drag by drag, and with the head measured twice as a control.</p>

<div class="headline">
<p><b>Short answers.</b> #2635 at <code>032fe3aca6</code> and two prototypes on it, in one headless Firefox 157, a tab each; ten rounds of one 1.5-second drag per tab, the order turned each round; the head in two tabs, so its difference from itself is the noise floor. The method is <a href="#method">at the end</a>.</p>
<ol>
  <li><b>Keeping only the newest preview cuts the freeze nearly in half, with the whole program.</b> Frozen per drag: the head {s(cC, "head", "stalled_ms") / 1000:.1f} s, the fix {s(cC, "coalesce", "stalled_ms") / 1000:.1f} s; round by round the fix was lower in all {cC["rounds"]} rounds, by {-pd(cC, "coalesce", "stalled_ms")[4] / 1000:.1f} to {-pd(cC, "coalesce", "stalled_ms")[3] / 1000:.1f} s (median {pd(cC, "coalesce", "stalled_ms")[0] / 1000:+.2f} s), where the head against itself differed by {pd(cC, "head-again", "stalled_ms")[0] / 1000:+.2f} s, five rounds each way (<a href="#frozen">Figures 1 and 2</a>).</li>
  <li><b>It does it by sending fewer repaints, not faster ones.</b> Of about {inp:g} inputs in a drag, it sent {sent:g} repaints and folded {coal:g} into one already on its way; each repaint still froze the page about as long (the head {s(cC, "head", "stalled_ms") / s(cC, "head", "inputs"):.0f} ms per input, the fix {s(cC, "coalesce", "stalled_ms") / sent:.0f} ms per repaint, medians). A preview costs much less than a finished change, which report 015 put at about a second. The picture is final as soon after letting go as before ({pd(cC, "coalesce", "release_to_redraw_ms")[0] / 1000:+.2f} s, within the noise; <a href="#release">Figure 3</a>).</li>
  <li><b>In UX mode, the freeze is smaller and the effect hides in the noise.</b> The head froze for about {s(cB, "head", "stalled_ms") / 1000:.1f} s; the fix {pd(cB, "coalesce", "stalled_ms")[0] / 1000:+.2f} s against it, but the head against itself {pd(cB, "head-again", "stalled_ms")[0] / 1000:+.2f} s, with single rounds up to two seconds apart.</li>
  <li><b>Views in the worker do not shorten the freeze, and in UX mode the picture comes later.</b> Frozen: {pd(vC, "views-in-worker", "stalled_ms")[0] / 1000:+.2f} s with the whole program and {pd(vB, "views-in-worker", "stalled_ms")[0] / 1000:+.2f} s in UX mode, both within the noise. Letting go to the final picture in UX mode: {pd(vB, "views-in-worker", "release_to_redraw_ms")[0] / 1000:+.2f} s, later in {pd(vB, "views-in-worker", "release_to_redraw_ms")[2]} of 10 rounds; the head against itself differed by {pd(vB, "head-again", "release_to_redraw_ms")[0] / 1000:+.2f} s in that run and {pd(cB, "head-again", "release_to_redraw_ms")[0] / 1000:+.2f} s in the other UX run. Likely real, but small, and from one run.</li>
  <li><b>Side by side is what made the difference visible.</b> Measured a session at a time earlier in the day, alternating builds between sessions, the head froze 4.1 s and then 3.2 s, and the same coalescing 2.8 s and then 4.2 s: the sessions moved more than the fix did. Alternating drag by drag puts the drift on every build alike.</li>
</ol>
</div>

<figure class="fig" id="fig-bars">{fig_bars}<figcaption><b>Figure 1.</b> Frozen time (frame gaps over 50 ms) in one 1.5-second drag, each build's median of ten with its fastest and slowest, in the two runs per mode. The head appears twice in each run (the second, faded, is the A/A copy). Numbers in <a href="#table">the table</a>.</figcaption></figure>

<h2 id="frozen">The freeze, round by round</h2>
<figure class="fig" id="fig-frozen">{fig_frozen}<figcaption><b>Figure 2.</b> Each dot is one round: that build's frozen time minus the head's in the same round. The A/A rows (the head against itself, faded) show how far two copies of the same build land apart. With the whole program, keeping only the newest preview is left of zero in every round; nothing else is clearly off zero.</figcaption></figure>
<p>A drag's moves arrive faster than Full Body's page can handle them: each preview of a dragged value is a page action, and the page recalculates for every action, which on Full Body checks the whole program for what can be reused. The fix (<code>3eb4489124</code>, local) keeps at most one such repaint on its way: a move that arrives while one is pending only updates the preview that repaint will show, and the next repaint may go once a frame has been painted. Fewer recalculations, so fewer freezes; each recalculation costs what it did.</p>
<p>These drags are longer than report 015's. Each crosses 190 to 250 of the slider's units, from near one end to near the other, where all but one of report 015's crossed 20 to 50; in the same second and a half the slider sends about {s(cC, "head", "inputs"):g} inputs instead of 6 to 15. Report 015 found only 1.5 to 3 of a drag's changes could be folded, and expected the fix to matter only once each change was cheaper. On a long drag, with inputs arriving every 35 ms or so, it folds {coal:g} of {inp:g}, and it matters now.</p>

<h2 id="release">The final picture</h2>
<figure class="fig" id="fig-release">{fig_release}<figcaption><b>Figure 3.</b> Letting go to the final picture, each build minus the head, round by round. Only views in the worker in UX mode lean off zero: later by about a quarter of a second in eight of ten rounds, with one round far each way.</figcaption></figure>
<p>Moving the views to the worker (<code>4c9331d13c</code>, local) takes their evaluation off the page, and report 015 counted about 0.2 to 0.5 s of page time saved per change. In a drag that does not show: the page still recalculates for every preview, and the views' work moves to the worker, which the final picture then waits for.</p>

<h2 id="table">The numbers</h2>
{table}
<p class="note">Medians of ten drags per build after one warm-up each. The differences are round by round, each build against the head's drag in the same round.</p>

<h2 id="next">What next</h2>
<ol>
  <li>Offer keeping only the newest preview (<code>3eb4489124</code>) to #2635, and to #2597, where the same page loop runs.</li>
  <li>Park views in the worker for drags: they do not shorten a drag's freeze, and they make UX mode's final picture later.</li>
  <li>Make each change cheaper, now that there are fewer of them: report 015's first step, skipping the whole-program reuse check for a dragged value's preview.</li>
  <li>Measure UX mode with more rounds, or longer drags, to find out whether coalescing helps there too; ten rounds were not enough against its noise.</li>
</ol>

<h2 id="method">How this was put together</h2>
<ul>
  <li><b>Builds:</b> #2635 at <code>032fe3aca6</code> (a dev build); keeping only the newest preview, <code>3eb4489124</code> on it, with <code>2db6ee4c30</code>'s counters of repaints sent and coalesced; views in the worker, <code>4c9331d13c</code> on it (the prototype's third experiment: whole programs fold the livelit views into the worker's run). Both prototypes are local branches.</li>
  <li><b>Interleaving:</b> one headless Firefox 157 over WebDriver, one tab per build, all three loaded at once on Full Body: the head twice, served under two host names (two origins, so each tab keeps its own saved state), and the prototype from its own server. One warm-up drag per tab, then ten rounds; in each round every tab makes one drag, the order of the tabs turned round from round to round (and reversed every other round), the tab brought to the front before its drag. Two runs per prototype: the whole program on screen (C), and UX mode with only the slider and the picture shown (B).</li>
  <li><b>The drag and its measures:</b> as report 015's: WebDriver pointer actions, down, 15 moves of 100 ms, up, to a value new to that tab, alternately near the top and near the bottom of the slider, so each drag crosses 190 to 250 of its units (all but one of report 015's crossed 20 to 50); a requestAnimationFrame loop records every frame from the press until the picture differs from before the drag, polled every 50 ms after the release; frozen time is the sum of frame gaps over 50 ms.</li>
  <li><b>The numbers, for programs too:</b> every drag's readings are in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/016/data"><code>016/data/</code></a>, with the driver (<code>ab_drag.py</code>) and this page's generator in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/016/drivers"><code>016/drivers/</code></a>.</li>
</ul>
</main>
<script type="application/json" id="report-data">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>
</body>
</html>
"""
open(os.path.join(R, "016", "index.html"), "w").write(page)
print("wrote", len(page))
