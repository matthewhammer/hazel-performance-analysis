#!/usr/bin/env python3
"""^ticket(127): ^report(17)'s page (a draft): the performance PRs to dev, what each buys, and a merge plan.

  python3 gen017.py   # writes ~/hazel-perf-report/017/index.html from 017/data/
"""
import json, os, re, html, math

R = os.path.expanduser("~/hazel-perf-report")
D = os.path.join(R, "017", "data")
esc = html.escape
css = re.search(r"<style>(.*?)</style>", open(os.path.join(R, "014", "index.html")).read(), re.S).group(1)
files = json.load(open(os.path.join(D, "files.json")))
prj = {int(os.path.basename(f)[2:6]): json.load(open(os.path.join(D, f))) for f in os.listdir(D) if re.match(r"pr\d+\.json$", f)}
fig005 = re.search(r"<figure>(.*?)<figcaption>", open(os.path.join(R, "005", "index.html")).read(), re.S).group(1)
DEV = "e12145c69b"
GH = "https://github.com/hazelgrove/hazel"
pr = lambda n: f'<a href="{GH}/pull/{n}">#{n}</a>'
c10 = lambda c: f'<a href="{GH}/commit/{c}"><code>{c}</code></a>'

# ---------- what each PR is, and what it buys (numbers from the PR's own measurement unless a report is named) ----------
AREA = {"editor": "the editor", "load": "loading text", "statics": "statics", "eval": "the evaluator", "worker": "the worker and the page", "ci": "CI"}
P = {
 2672: dict(area="editor", short="font re-measure keeps the scroll", what="Measuring the font no longer scrolls the editor to the caret.",
            why="A correctness fix with a responsiveness cost: a font re-measure after the reader scrolled jumped the editor back, and a click aimed at what was there landed on something else. On the livelits branch the first click on a slide's picture was lost 7 or 8 times in 8; with this, 8 of 8 land (report 001).",
            wait="None found. One line.", look="That startup still reveals the caret once (<code>scroll_to_caret</code> starts true)."),
 2652: dict(area="worker", short="Firefox: worker starts at load", what="The eval worker starts at load, and a late timer no longer kills a worker whose answer is already queued.",
            why="In Firefox a busy main thread could keep the worker from loading, and a late deadline then killed it: the slide showed “Evaluation timed out” and drew nothing. With this those slides draw (#2609's finding 8).",
            wait="Firefox-only behaviour, so it rests on the tests in the PR and on manual checks; the 250 ms lateness threshold is a judgement call.", look="<code>WorkerClient.set_deadline</code>'s lateness rule, and creating the worker before IndexedDB loads."),
 2651: dict(area="statics", short="module definition analyzed once", what="A module binding's definition is analyzed once, not twice.",
            why="Statics analyzed <code>module M = def</code>'s definition a second time only to read back an elaboration it had already recorded. On one slide, 1.8 s of its 4.2 s of statics (report 001, on the livelits branch); <code>hazel analyze -W</code> output is the same on all 73 programs, but for warnings' random ids.",
            wait="None found. 18 lines; it touches <code>Statics.re</code>, as #2603 and #2675 do, but merges cleanly with both.", look="The fallback to the direct analysis when no info was recorded."),
 2610: dict(area="load", short="load fallback, segmented parser", what="Text the fast parser rejects is parsed by the segmented parser, which keeps projectors.",
            why="The fallback inserted text one character at a time, re-molding the whole sibling run each time: quadratic. Over 128 inputs (every program and tutorial section) the fallback takes 63 s instead of 182 s; 8 KB of prose, 1.3 s instead of 64 s.",
            wait="It conflicts with #2614 in <code>MarkerParse.re</code> (both change how the fallback is called): merge one, then rebase the other.", look="<code>to_segment_with_manuals</code> keeping each piece's projectors."),
 2614: dict(area="load", short="text loads ~2.5× faster", what="The recovering parser inserts whole tokens and re-grouts once, instead of per character.",
            why="Parsing the 72 programs takes 87 s instead of about 220 s, and the parse-heavy test groups 142 s instead of 267 s: CI time for everyone, and load time for slides and share links.",
            wait="It conflicts with #2610 (above) and with #2469 in <code>Segment.re</code> and <code>Zipper.re</code>. Eight commits, each checked on its own.", look="<code>Siblings.rescan</code> returning its argument unchanged, which the identity checks downstream now rely on."),
 2603: dict(area="statics", short="a let analyzed once", what="A let is analyzed once unless it refers to itself, plus three smaller statics speedups.",
            why="Every let-bound function took the recursive path, and passes multiplied with nesting, up to 4<sup>depth</sup>: eight nested functions took 5.3 s of statics, now 13 ms. On real programs statics is 20 to 30% faster. Output is byte-identical on all 72 programs.",
            wait="The largest statics change here (563 lines, four fixes in their own commits), and it conflicts with #2469 in <code>Builtins.re</code>. It deserves the closest review.", look="When a function-shaped definition skips the recursive probe: it must not mention its own binders, and they must shadow nothing in scope."),
 2675: dict(area="statics", short="reuse around a recursive let", what="Statics reports a recursive let's free variables correctly, so the evaluator reuses what is around it.",
            why="A module with a recursive member, or a function with a recursive helper, was never reused by incremental evaluation, nor was anything reading it: every edit re-ran them. The PR has no timing of its own; on the livelits branch the same fix lets the woods slide reuse its code after a figure move (report 005, report 006).",
            wait="It changes what statics reports (a let's <code>co_ctx</code>), which reuse trusts: a mistake there would reuse a stale value. Only when a fixpoint binds the pattern.", look="The <code>requires_fixf</code> case taking <code>CoCtx.mk(ctx, p_ana.ctx, def.co_ctx)</code>, as <code>fun_id</code> already does."),
 2671: dict(area="editor", short="unchanged pieces kept as the same objects", what="<code>MapPiece</code> returns the same object for any piece with nothing changed beneath it.",
            why="A projector update copied the whole program, and looked to anything keyed on identity like a new program. On dev, 3.1 ms to 1.9 ms per update in a 2,000-let program; on the livelits branch, where items are re-parsed by identity, a Kids' Choice slider release went from 1.5–1.7 s to 0.7–0.9 s.",
            wait="On dev itself the gain is small: the copy only. Its value is for what keys on identity, as #2469 and the livelits branches do.", look="That every <code>of_*</code> returns its argument when its children came back physically equal."),
 2661: dict(area="eval", short="types hashed; is_consistent once per pair", what="Types get a Merkle hash, and the evaluator asks <code>is_consistent</code> once per pair of types.",
            why="Ascribing a constructor application compared two copies of the same sum type in full, every time. On dev's benchmark 75 ms to 60 ms; on the livelits branch, where a view is a tree of <code>Html</code> constructors, a click on the Polygons editor went from 15–17 s to 2 s (profiled), and the ascription step from 88% of the click to under 6%.",
            wait="It conflicts with #2679 in <code>Ascriptions.re</code>; #2681 carries the resolution (merge commit <code>a032bd5c6a</code>). The hash lives in a JS <code>WeakMap</code>: a 60-bit key, and types holding an expression get no hash.", look="<code>TypHash</code>'s key and what it refuses to hash."),
 2679: dict(area="eval", short="ascription gives the value back", what="An ascription pushed through a value gives the value back when nothing in it changed.",
            why="A well-typed list crossing a typed parameter was copied whole on every call. A list of 2,000 tuples passed 30 times: 382 ms to 268 ms; ordinary code unchanged. On the livelits branch the Scenes picture's view is 20 to 25% faster, and its values keep their ids, so identity memos hit.",
            wait="It conflicts with #2661 (see #2681). The copy was invisible to step counts, so the gain shows only in time.", look="Each case building a node only when a part came back different."),
 2681: dict(area="eval", short="a value known to have a type is not walked again", what="A value already known to have a type is not walked again for it.",
            why="A recursive function with an annotated list parameter walked its whole argument at every call: quadratic. At 400 elements 205 ms to 33 ms; a parameter annotated at the let is unchanged.",
            wait="It contains #2661 and #2679 (merged into its branch): review only its last commit, <code>8546bde64e</code>, and merge it after both. It conflicts with #2673 in <code>Util.re</code>.", look="The memo's key, and that it costs nothing measurable when there is nothing to save."),
 2673: dict(area="eval", short="reuse check by Merkle hash", what="Incremental evaluation recognizes an unchanged expression by its Merkle hash, and remembers each comparison.",
            why="The reuse check compared expressions structurally, and statics makes fresh objects every run, so every check walked its whole subterm: O(n²) along a program's lets. Re-evaluating after an edit in a 400-definition program: 2.7 s to 0.41 s. On the livelits branch, about 410 to 145 ms per release (report 005).",
            wait="It adds <code>Util.ValueHash</code>, which hashes any immutable value by its runtime structure: the most general new mechanism here, and the one to read carefully for soundness (functions and unforced lazies are refused). It conflicts with #2681 in <code>Util.re</code>.", look="What <code>ValueHash</code> refuses to hash, and <code>ValueHash.Pairs</code>' memory."),
 2606: dict(area="worker", short="incremental cache kept in the worker", what="The incremental cache stays in the eval worker instead of crossing to the page and back on every run.",
            why="An answer carried its whole evaluator state, almost all cache, and the page sent it straight back: answers 86 to 98% smaller (report 001); on the livelits branch, an answer of 332 KB became 0.9 KB (report 005).",
            wait="It conflicts with #2469 in four files (<code>EvalResult.re</code>, <code>WorkerServer.re</code>, <code>ScratchMode.re</code> and its test), which change the same request and answer: merging both needs a plan with Andrew.", look="What happens after a failed run or a restarted worker: both keep nothing, so the next run is a full one."),
 2678: dict(area="ci", short="CI fails on an over-budget evaluation", what="CI fails when an evaluation takes more steps than its budget; the two broken benchmark workflows stop running on comments.",
            why="Nothing in CI catches a performance regression today. Times can't be held to a budget on shared runners; step counts can (report 006). Two budgets, in the quick suite, under a second.",
            wait="A budget can fail someone's legitimate change: the budgets are about 10% over today's counts. Merge it after the evaluator PRs, so its counts are theirs. Turning off <code>/perf</code> and <code>/bench-compare</code> on comments is the maintainers' call.", look="<code>evaluate_counting_work</code> counting a reused result as one step."),
}
WAVES = [("1. Small and independent", [2672, 2652, 2651, 2610], "Each is small, touches nothing the others do, and merges cleanly onto dev; any order. #2608 (below the table) belongs here too."),
         ("2. Loading and statics", [2614, 2603], "#2614 after #2610, resolving <code>MarkerParse.re</code>. #2603 is independent of both but is the biggest statics change: give it its own review."),
         ("3. The evaluator", [2675, 2671, 2661, 2679, 2681, 2673], "#2681 contains #2661 and #2679 with their conflict resolved: merge it in their place (GitHub then shows both as merged), or merge them first, #2679 with the same resolution. #2673 last, resolving <code>Util.re</code> with #2681."),
         ("4. Coordinated", [2606, 2678], "#2606 when #2469's plan is known (they change the same request and answer). #2678 last, so its budgets count the evaluator as merged.")]

# ---------- numbers for the figure: before, after (same unit), what, where, source ----------
GAIN = [
 (2603, 5341, 13, "ms", "statics, 8 nested let-bound functions", "dev"),
 (2603, 73, 49, "ms", "statics, b2t2/example-tables.hz", "dev"),
 (2610, 182, 63, "s", "load fallback, all 128 programs and sections", "dev"),
 (2614, 220, 87, "s", "parsing the 72 programs", "dev"),
 (2614, 267, 142, "s", "the parse-heavy test groups", "dev"),
 (2673, 2743, 410, "ms", "re-evaluation after an edit, 400 definitions", "dev"),
 (2661, 74.5, 60.5, "ms", "benchmark: a 20-constructor sum builder", "dev"),
 (2661, 16.2, 2.1, "s", "a click on Polygons (profiled)", "livelits"),
 (2671, 3.12, 1.92, "ms", "one projector update, 2,000 lets", "dev"),
 (2671, 1.6, 0.8, "s", "a Kids' Choice slider release", "livelits"),
 (2679, 382, 268, "ms", "2,000 tuples through a typed parameter, 30 times", "dev"),
 (2679, 778, 585, "ms", "the Scenes picture's view", "livelits"),
 (2681, 205, 33, "ms", "recursive function, annotated list of 400", "dev"),
 (2606, 332, 0.9, "KB", "one answer from the worker (report 005)", "livelits"),
]

def gain_chart(w=900):
    x0, x1 = 430, w - 90
    lmax = math.log10(1000)
    sc = lambda r: x0 + (x1 - x0) * math.log10(max(1, r)) / lmax
    rh = 30; h = 60 + rh * len(GAIN) + 46
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc("Each PR measurement as how many times faster or smaller, on a log scale from 1 to 1000. The 8-nested-lets statics case is about 410 times faster and the worker answer about 370 times smaller; re-evaluation in a 400-definition program and the Polygons click are 6.7 and 7.7 times faster; the rest are 1.2 to 3 times.")}">',
         f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">What each PR buys, on its own measurement: times faster (or smaller), log scale</text>']
    for t in (1, 2, 5, 10, 30, 100, 300, 1000):
        o.append(f'<line x1="{sc(t):.1f}" y1="34" x2="{sc(t):.1f}" y2="{h - 40}" class="grid"/><text x="{sc(t):.1f}" y="{h - 24}" text-anchor="middle" class="cv">{t}×</text>')
    for i, (n, b, a, u, what, where) in enumerate(GAIN):
        y = 44 + rh * i; r = b / a
        cls = "good" if where == "dev" else "accent"
        o.append(f'<text x="14" y="{y + 13}" class="cl" font-weight="700">#{n}</text>'
                 f'<text x="{x0 - 10}" y="{y + 13}" text-anchor="end" class="cl">{esc(what)}{" · livelits" if where != "dev" else ""}</text>'
                 f'<rect x="{x0}" y="{y}" width="{max(2, sc(r) - x0):.1f}" height="18" rx="3" style="fill: var(--{cls})"/>'
                 f'<text x="{sc(r) + 6:.1f}" y="{y + 13}" class="cl"><tspan font-weight="700">{r:.3g}×</tspan> {b:g} → {a:g} {u}</text>')
    o.append(f'<text x="{w / 2}" y="{h - 6}" text-anchor="middle" class="cv">green: measured on dev, as the PR is; purple: the same change measured on the livelits branch (#2635), where it matters more</text></svg>')
    return "".join(o)

# ---------- the dependency graph ----------
POS = {2672: (90, 90), 2652: (90, 165), 2651: (90, 240), 2610: (90, 330),
       2614: (300, 330), 2603: (300, 200),
       2675: (520, 110), 2671: (520, 185), 2661: (520, 260), 2679: (520, 335), 2681: (700, 300), 2673: (700, 185),
       2606: (880, 150), 2678: (880, 300),
       2469: (470, 440), 2490: (860, 440)}
NODE = {2672: "scroll kept", 2652: "Firefox worker start", 2651: "module def. once", 2610: "fallback, segmented", 2614: "text loads 2.5\u00d7", 2603: "a let analyzed once",
        2675: "recursive-let reuse", 2671: "pieces kept", 2661: "types hashed", 2679: "ascription, no copy", 2681: "typed value, no re-walk", 2673: "reuse check by hash",
        2606: "cache stays in worker", 2678: "CI step budgets"}
COL = {"editor": "#2563eb", "load": "#0891b2", "statics": "#7c3aed", "eval": "#059669", "worker": "#d97706", "ci": "#6b7280"}

def dep_graph(w=980, h=540):
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" style="min-width:760px" aria-label="{esc("A graph of the fourteen PRs in four columns, the merge waves. Solid arrows: #2681 builds on #2661 and #2679. Red dashed lines: textual conflicts, #2610 with #2614, #2661 with #2679, #2673 with #2681. Thin grey lines: files shared without a conflict, #2603, #2651 and #2675 in Statics.re. Orange lines to #2469, Andrew Blinns modular editors PR: conflicts with #2603, #2606 and #2614. #2490, the wasm spike, stands apart.")}">',
         '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--ink)"/></marker></defs>']
    for i, (title, _, _) in enumerate(WAVES):
        x = [90, 300, 610, 880][i]
        o.append(f'<text x="{x}" y="30" text-anchor="middle" class="cl" font-weight="700">wave {esc(title)}</text>')
    box = lambda n: POS[n]
    def line(a, b, cls, dash="", arrow=False, label=""):
        (ax, ay), (bx, by) = box(a), box(b)
        s = f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" style="stroke: var(--{cls})" stroke-width="{2.5 if cls != "muted" else 1.5}"{f" stroke-dasharray=\"{dash}\"" if dash else ""}{" marker-end=\"url(#arr)\"" if arrow else ""} opacity="0.9"/>'
        if label:
            vert = abs(bx - ax) < abs(by - ay)
            s += (f'<text x="{(ax + bx) / 2 + 8:.0f}" y="{(ay + by) / 2 + 4:.0f}" class="cv" font-size="11">{esc(label)}</text>' if vert
                  else f'<text x="{(ax + bx) / 2:.0f}" y="{(ay + by) / 2 - 7:.0f}" text-anchor="middle" class="cv" font-size="11">{esc(label)}</text>')
        return s
    # shared files, no conflict
    for a, b in [(2603, 2651), (2603, 2675), (2673, 2675)]:
        o.append(line(a, b, "muted", "2 4"))
    # conflicts
    for a, b, lab in [(2610, 2614, "MarkerParse.re"), (2661, 2679, "Ascriptions.re"), (2673, 2681, "Util.re")]:
        o.append(line(a, b, "bad", "7 5", label=lab))
    for a in (2603, 2606, 2614):
        o.append(line(a, 2469, "accent2", "7 5"))
    # builds on
    for a in (2661, 2679):
        (ax, ay), (bx, by) = box(a), box(2681)
        # stop the arrow at the box's edge
        dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy); bx2, by2 = bx - dx / L * 62, by - dy / L * 22
        o.append(f'<line x1="{ax + 60}" y1="{ay}" x2="{bx2:.0f}" y2="{by2:.0f}" style="stroke: var(--ink)" stroke-width="2.2" marker-end="url(#arr)"/>')
    for n, (x, y) in POS.items():
        if n in P:
            c = COL[P[n]["area"]]
            o.append(f'<a href="{GH}/pull/{n}" style="text-decoration: none"><rect x="{x - 66}" y="{y - 21}" width="132" height="42" rx="8" style="fill: var(--panel)"/><rect x="{x - 66}" y="{y - 21}" width="132" height="42" rx="8" fill="{c}" fill-opacity="0.16" stroke="{c}" stroke-width="2"/>'
                     f'<text x="{x}" y="{y - 4}" text-anchor="middle" class="cl" font-weight="700">#{n}</text>'
                     f'<text x="{x}" y="{y + 12}" text-anchor="middle" class="cv" font-size="10.5">{esc(NODE[n])}</text></a>')
        else:
            lab = "#2469 modular editors (Andrew)" if n == 2469 else "#2490 wasm spike: not for merging"
            o.append(f'<a href="{GH}/pull/{n}" style="text-decoration: none"><rect x="{x - 105}" y="{y - 18}" width="210" height="36" rx="8" style="fill: var(--panel); stroke: var(--muted)" stroke-width="1.5" stroke-dasharray="{"" if n == 2469 else "4 3"}"/>'
                     f'<text x="{x}" y="{y + 5}" text-anchor="middle" class="cl">{esc(lab)}</text></a>')
    leg = [("ink", "", "builds on (merged into its branch)"), ("bad", "7 5", "textual conflict"), ("accent2", "7 5", "conflicts with #2469"), ("muted", "2 4", "same file, merges cleanly")]
    for i, (cls, dash, lab) in enumerate(leg):
        lx, yy = 30 + 240 * i, h - 52
        o.append(f'<line x1="{lx}" y1="{yy}" x2="{lx + 34}" y2="{yy}" style="stroke: var(--{cls})" stroke-width="2.2"{f" stroke-dasharray=\"{dash}\"" if dash else ""}/><text x="{lx + 42}" y="{yy + 4}" class="cv" font-size="11.5">{esc(lab)}</text>')
    for i, (k, c) in enumerate(COL.items()):
        lx, yy = 30 + 160 * i, h - 24
        o.append(f'<rect x="{lx}" y="{yy - 9}" width="12" height="12" rx="3" fill="{c}" fill-opacity="0.3" stroke="{c}"/><text x="{lx + 18}" y="{yy + 1}" class="cv" font-size="11.5">{esc(AREA[k])}</text>')
    o.append("</svg>")
    return "".join(x for x in o if x)

# ---------- the per-PR table ----------
def pr_rows():
    rows = []
    for title, ns, _ in WAVES:
        for n in ns:
            p, j = P[n], prj[n]
            rows.append(f'<tr id="pr{n}"><td>{pr(n)}<br><span class="note">{esc(AREA[p["area"]])} · +{j["additions"]} −{j["deletions"]}, {j["changedFiles"]} file{"s" if j["changedFiles"] != 1 else ""}</span></td>'
                        f'<td data-h="What it does, and why it matters"><b>{p["what"]}</b> {p["why"]}</td><td data-h="Reasons to wait">{p["wait"]}</td><td data-h="What a reviewer should look at">{p["look"]}</td></tr>')
    return '<div class="scroll"><table class="prs"><tr><th>PR</th><th>What it does, and why it matters</th><th>Reasons to wait</th><th>What a reviewer should look at</th></tr>' + "".join(rows) + "</table></div>"

trial = files["plan_trial"]
conf_steps = [t for t in trial if t["conflicts"]]
plan_html = "".join(f'<li><b>Wave {esc(t)}:</b> {", ".join(pr(n) for n in ns)}. {why}</li>' for t, ns, why in WAVES)
trial_html = "".join(f'<li>{pr(t["pr"])}: {", ".join("<code>" + esc(c) + "</code>" for c in t["conflicts"])}</li>' for t in conf_steps)

data = {"report": 17, "title": "Fourteen performance PRs to dev, and a plan to merge them", "date": "2026-10-15", "published": "2026-10-16",
        "question": "For Cyrus, Alexander, Andrew or Matt K: for each of the open performance PRs to dev, why it matters and what reasons there are not to merge it yet, and a merge plan (^ticket(127)).",
        "dev": DEV, "fetched": "2026-10-15T21:40-06:00 (PR states, checks, reviews); trial merges 22:55",
        "prs": {n: {"title": prj[n]["title"], "branch": prj[n]["headRefName"], "head": prj[n]["headRefOid"], "additions": prj[n]["additions"], "deletions": prj[n]["deletions"],
                    "files": prj[n]["changedFiles"], "commits": len(prj[n]["commits"]), "mergeable": prj[n]["mergeable"], "merge_state": prj[n]["mergeStateStatus"],
                    "checks": [(c.get("name"), c.get("conclusion") or c.get("state")) for c in (prj[n].get("statusCheckRollup") or [])],
                    "reviews": len(prj[n]["reviews"]), "draft": prj[n]["isDraft"], "area": P.get(n, {}).get("area")} for n in sorted(prj)},
        "gains": [{"pr": n, "before": b, "after": a, "unit": u, "what": w, "where": wh} for n, b, a, u, w, wh in GAIN],
        "files_changed": {k: v["files"] for k, v in files["prs"].items()},
        "pairwise_conflicts": files["pairwise_conflicts"], "vs_2469": files["vs_2469"],
        "plan_order": files["plan_order"], "plan_trial": files["plan_trial"],
        "together": {"prs": 15, "base": DEV, "resolutions": "MarkerParse.re: #2610's call; Ascriptions.re: #2681 merged in place of #2661 and #2679; Util.re and test/haz3ltest.re: both sides", "build": "dune, dev profile, no errors, no formatting changes", "suite": {"tests": 4756, "failures": 0, "seconds": 411.5, "runner": "test/run_node.sh (full)"}, "date": "2026-10-15"},
        "method": "PR states from gh pr view (json); files from git diff of each branch against its merge base with dev; conflicts from git merge-tree --write-tree, pairwise and in the plan's order (a conflicted step continued with a union resolution, to find the next conflict; not built)."}

n_clean = sum(1 for t in trial if not t["conflicts"])
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Merging the Performance PRs</title>
<style>{css}
table.prs td {{ vertical-align: top; }} table.prs td:first-child {{ min-width: 6.5em; }}
@media (max-width: 760px) {{ table.prs, table.prs tbody, table.prs tr, table.prs td {{ display: block; }} table.prs tr:first-child {{ display: none; }} table.prs tr {{ border-top: 1px solid var(--muted); padding: 0.6em 0; }} table.prs td {{ border: 0; padding: 0.25em 0; }} table.prs td[data-h]::before {{ content: attr(data-h); display: block; font-weight: 700; font-size: 0.85em; color: var(--muted); }} }}
:root {{ --accent2: #ea580c; --panel: #ffffff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --accent2: #fb923c; --panel: #1b1d21; }} }}
:root[data-theme="dark"] {{ --accent2: #fb923c; --panel: #1b1d21; }}
</style>
</head>
<body>
<main>
<p class="series"><a href="../">Hazel performance analysis</a> · report 017 · 2026-10-15</p>
<h1>Fourteen performance PRs to dev, and a plan to merge them</h1>
<p class="sub">Since late September, the profiling behind this series has produced fourteen pull requests to <code>dev</code>: statics, loading text, the evaluator, the worker, the editor, and CI. Each is small, measured and tested, and none has been reviewed. This report is for whoever reviews them (Cyrus, Alexander, Andrew, Matt K): for each PR, what it buys and where that was measured, the honest reasons not to merge it yet, and what to look at; then the order to merge them in, which ones depend on or conflict with which, and what each needs first.</p>

<div class="headline">
<p><b>Short answers.</b> The PRs as of 2026-10-15 evening, against dev at <code>{DEV}</code>. Every number below was measured in its PR (or in the report named), each against dev or the livelits branch as it says.</p>
<ol>
  <li><b>All fourteen are green and merge cleanly onto today's dev, one at a time.</b> Every one passes CI (five checks pass and one is skipped, on each; dev requires none to merge, report 006) and GitHub calls each mergeable. None has a review or a comment from a person. A fifteenth, #2608, is open too, and was missing from the list this report began from (<a href="#pr2608">below</a>).</li>
  <li><b>What they buy, on dev:</b> statics of nested functions from exponential to linear (5.3 s to 13 ms at eight levels; real programs 20 to 30% faster, #2603); loading text 2.5× faster and the parse test groups 267 s to 142 s (#2614, with #2610 for the fallback, 182 s to 63 s); re-evaluation after an edit 2.7 s to 0.41 s in a 400-definition program (#2673); and typed code that no longer copies or re-walks its values (#2661, #2679, #2681). On the livelits branches the same changes are larger: a Polygons click 15 s to 2 s, a Kids' Choice release 1.6 s to 0.8 s (<a href="#gains">Figure 1</a>).</li>
  <li><b>The reasons to wait are few and specific.</b> Three pairs conflict textually (#2610 with #2614, #2661 with #2679, #2673 with #2681), and three PRs conflict with Andrew's #2469 (#2603, #2606, #2614). #2681 contains #2661 and #2679. #2603 and #2673 are the two to review most carefully: the largest statics change, and a new general hashing mechanism. #2490 is a spike, not a merge candidate (<a href="#deps">Figure 2</a>).</li>
  <li><b>The merge plan: four waves</b>, small and independent first, the evaluator together, and the two that need coordination last. Merged in that order, {n_clean} of the fourteen go in with no conflict; {len(conf_steps)} need a hand resolution, two of them only the test list. With those resolutions all fifteen together build and pass the full test suite, 4,756 tests (<a href="#plan">the plan</a>).</li>
</ol>
</div>

<figure class="fig" id="gains">{gain_chart()}<figcaption><b>Figure 1.</b> Each PR's own measurement, as how many times faster (or smaller) it made the thing measured, on a log scale; before and after beside each bar. Green rows were measured on dev, as the PR will run there; purple rows are the same change measured on the livelits branch (#2635), where it was found. Sources: each PR's description, and report 005 for the worker's answer size; the runs and conditions are in the PRs. Not every PR is here: #2652 and #2672 fix wrong behaviour, #2651 was measured on one slide, #2675 has no timing of its own, and #2678 adds a check.</figcaption></figure>

<h2 id="deps">What depends on what</h2>
<figure class="fig"><div class="scroll">{dep_graph()}</div><figcaption><b>Figure 2.</b> The PRs in their merge waves, coloured by what they change. Only #2681 builds on others (#2661 and #2679 are merged into its branch). Red: the three textual conflicts between PRs. Orange: the three PRs that conflict with #2469, Andrew Blinn's modular editors. Grey: PRs that change the same file but merge cleanly. Not drawn: conflicts in <code>test/haz3ltest.re</code>, the test list, where each PR adds its tests' line; they resolve by keeping both lines.</figcaption></figure>

<h2 id="prs">Each PR</h2>
{pr_rows()}

<p id="pr2608"><b>A fifteenth: #2608</b>, “Leave the source's whitespace and comments out of elaborations” (+83 −3, 4 files; the program half of the worker's request). Every elaborated node kept its source's whitespace and comment runs, which nothing reads: a request's program and its info map are 12 to 49% smaller without them (on five programs, marshaled bytes; probes.hz 48.0 to 24.5 KB), statics time unchanged. It is independent of #2606, which shrinks the other half. Green and unreviewed, like the others, it merges cleanly onto dev and with #2469, and conflicts only with #2610 in the test list. It belongs in wave 1. Reasons to wait: none found; a reviewer should check that nothing reads an elaboration's <code>secondary</code> (the PR says only <code>ExpToSegment</code>'s exact mode does, on parsed source).</p>

<h2 id="where">Where they act</h2>
<figure class="fig">{fig005}<figcaption><b>Figure 3</b> (from report 005, on the livelits branch). One change, in eight steps. The dev PRs act at these steps: the edit (#2671, and #2672's scroll), statics (#2603, #2651, #2675), the boundary (#2606, and #2652's start-up), the worker's evaluation with reuse (#2673, #2675), and the evaluator wherever it runs, in the worker or the page (#2661, #2679, #2681). #2610 and #2614 act before any of this, when a program's text is loaded.</figcaption></figure>

<h2 id="plan">A merge plan</h2>
<ol>
{plan_html}
</ol>
<p>Checked by merging the PRs' branches into dev at <code>{DEV}</code> in this order, without building: {n_clean} merge with no conflict, and these need a hand resolution:</p>
<ul>
{trial_html}
</ul>
<p><code>MarkerParse.re</code>: the same line, the load fallback's call to the parser. #2610 calls the segmented parser (<code>to_zipper_segmented</code>); #2614 calls the old one in its new whole-token mode (<code>to_zipper(~by_run=true)</code>). Take #2610's, and measure whether passing <code>~by_run</code> through to the pieces gains more; #2614's speedup still applies everywhere else <code>to_zipper</code> runs. <code>Ascriptions.re</code>: #2661 and #2679 each add a helper in the same place; #2681's merge commit <code>a032bd5c6a</code> keeps both. Merging #2681 in their place avoids this step entirely: it merges cleanly onto dev, and brings both. <code>Util.re</code>: #2673 and #2681 each add a module; keep both. The test list: keep both lines.</p>
<p><b>With #2469.</b> #2603, #2606 and #2614 conflict with Andrew's modular editors: in <code>Builtins.re</code> (#2603), in the worker's request and answer and the code around them (#2606: <code>EvalResult.re</code>, <code>WorkerServer.re</code>, <code>ScratchMode.re</code> and its test), and in <code>Segment.re</code> and <code>Zipper.re</code> (#2614). Whichever lands second rebases; #2606 most of all needs agreeing with Andrew, as both change what crosses to the worker. The other eleven merge cleanly with #2469.</p>
<p><b>Built and tested together.</b> All fifteen (#2608 included), merged into dev at <code>{DEV}</code> in this order with the resolutions above and #2681 in place of #2661 and #2679, build with no errors and no formatting changes, and pass the full test suite: 4,756 tests in 411 s, in node, on 2026-10-15 (a local branch, not pushed).</p>

<h2 id="next">What next</h2>
<ol>
  <li>Ask for reviews, a wave at a time: wave 1 can go to anyone; #2603 and #2673 to someone who knows statics and incremental evaluation.</li>
  <li>Agree with Andrew the order of #2606 and #2469.</li>
  <li>Measure dev with all fifteen against dev today, parsing and analyzing hazel-programs and running the test suite, for one before-and-after number (the merged branch is ready).</li>
</ol>

<h2 id="method">How this was put together</h2>
<ul>
  <li><b>Together:</b> the fifteen branches merged into dev in the plan's order on a local branch (the conflicts resolved as the plan says), built with the dev profile, and the full suite run under node.</li>
  <li><b>The PRs:</b> their titles, descriptions, checks, reviews and comments, read from GitHub on 2026-10-15 at 21:40 MDT (<code>gh pr view --json</code>). The numbers are the PRs' own, from their descriptions, which say how each was measured and on what; a few come from earlier reports, named where they are used.</li>
  <li><b>Conflicts:</b> each branch's files against its merge base with dev; each pair of branches merged with <code>git merge-tree --write-tree</code>; and all fourteen merged into dev in the plan's order, a conflicted step continued with both sides kept, to find the next conflict. The trial merges themselves were not built; the merged branch below was.</li>
  <li><b>The data:</b> in this page's <code>&lt;script type="application/json" id="report-data"&gt;</code> element and in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/017/data"><code>017/data/</code></a> (each PR's JSON as GitHub gave it, and the file and conflict analysis); this page's generator is in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/017/drivers"><code>017/drivers/</code></a>.</li>
  <li>All fourteen PRs are Matthew Hammer's, written with Claude; several began as fixes on the livelits branches, and #2681's base merges are noted in it.</li>
</ul>
</main>
<script type="application/json" id="report-data">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>
</body>
</html>
"""
open(os.path.join(R, "017", "index.html"), "w").write(page)
print("wrote", len(page))
