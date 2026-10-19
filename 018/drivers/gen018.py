#!/usr/bin/env python3
"""^report(18)'s page: reads 018/data/ (written by collect018.py) and writes 018/index.html and 018/img/thumb.svg.
Run from the repository's root, then the series tools (report_refs, link_prs, add_steps, add_theme) and
tools/theme_variants.py 018/img/thumb.svg.
  python3 018/drivers/gen018.py"""
import json, html
from datetime import datetime, timezone

D = "018/data/"
runs = json.load(open(D + "runs-2635.json"))
sampled = json.load(open(D + "sampled-runs.json"))
parents = json.load(open(D + "parents.json"))
lanes = json.load(open(D + "parent-runs.json"))
files = json.load(open(D + "test-files.json"))
facts = json.load(open(D + "git-facts.json"))

esc = html.escape
T0 = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
T1 = datetime(2026, 10, 19, 18, tzinfo=timezone.utc).timestamp()


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def count(rs, c):
    return sum(r["conclusion"] == c for r in rs)


def n(x):
    return f"{x:,}"


# ---- Figure 1: every CI run on the three branches since 10-01 ----
X0, X1 = 250, 885


def xat(s):
    return X0 + (ts(s) - T0) / (T1 - T0) * (X1 - X0)


COL = {"success": "good", "failure": "bad", "cancelled": "cx", "in_progress": "warn"}


def lane(rs, y):
    out = []
    for r in sorted(rs, key=lambda r: r["conclusion"] == "cancelled", reverse=True):  # cancelled drawn first, under the rest
        out.append(f'<rect class="tk {COL.get(r["conclusion"], "cx")}" x="{xat(r["created"]) - 1.2:.1f}" y="{y - 13}" width="2.4" height="26"/>')
    return "".join(out)


L35, L97, L69, L87 = 70, 178, 238, 298  # lane centres: #2635, #2597, #2469, #2687
fig1 = [f'<svg viewBox="0 0 900 360" role="img" class="chart" aria-label="Three rows of tick marks, one per CI run from 1 to 19 October 2026. '
        f'#2635, livelits by modular editors: {len(runs)} runs, every one red or cancelled, none green. #2597, the livelits branch: '
        f'{count(lanes["2597"]["runs"], "success")} green runs. #2469, modular editors: {count(lanes["2469"]["runs"], "success")} green runs. '
        f'#2687, Andrew\'s branch with Modules II and the port: green since 18 October. '
        f'Dots on #2635 mark the ten failing runs read: 8 failures on each through the morning of 17 October, 10 on the last.">']
for d in range(1, 20):
    x = xat(f"2026-10-{d:02d}T00:00:00Z")
    fig1.append(f'<line class="grid" x1="{x:.1f}" y1="34" x2="{x:.1f}" y2="322"/>')
    if d % 2 == 1:
        fig1.append(f'<text class="cv" x="{x:.1f}" y="342" text-anchor="middle">10-{d:02d}</text>')
for y, title, rs in [(L35, "#2635", runs), (L97, "#2597", lanes["2597"]["runs"]), (L69, "#2469", lanes["2469"]["runs"]), (L87, "#2687", lanes["2687"]["runs"])]:
    sub = {"#2635": "livelits × modular editors", "#2597": "the livelits branch", "#2469": "modular editors", "#2687": "modular editors + Modules II"}[title]
    fig1.append(f'<text class="cl" x="8" y="{y - 4}" font-weight="700">{title} <tspan class="cv" font-weight="400">{sub}</tspan></text>')
    fig1.append(f'<text class="cv" x="8" y="{y + 13}"><tspan class="good">{count(rs, "success")} green</tspan> · '
                f'<tspan class="bad">{count(rs, "failure")} red</tspan> · {count(rs, "cancelled")} cancelled</text>')
    fig1.append(lane(rs, y))
# the runs read, with their failure counts
last_x = -99
for i, s in enumerate(sampled):
    x = xat(s["created"])
    fig1.append(f'<circle class="rd" cx="{x:.1f}" cy="{L35 - 22}" r="3.2"/>')
    lab = str(s["fast"]["failures"])
    if i == len(sampled) - 1:
        fig1.append(f'<text class="bn bad" x="{x + 7:.1f}" y="{L35 - 26}">{lab}</text>')
    elif x - last_x > 16 and xat(sampled[-1]["created"]) - x > 16:
        fig1.append(f'<text class="bn bad" x="{x:.1f}" y="{L35 - 30}" text-anchor="middle">{lab}</text>')
        last_x = x
fig1.append(f'<text class="cv" x="{X0}" y="18">● a failing run read, with its number of failed tests (dates in UTC)</text>')
# the parents' commits that matter
p97, p69, p87 = parents["2597"], parents["2469_merged"], parents["2687"]
for p, y, lab in [(p97, L97, f'{p97["head"]}: {n(p97["fast"]["tests"])} + {n(p97["full"]["tests"])} tests pass'),
                  (p69, L69, f'{p69["head"]}, with what #2635 took on 10-17: {n(p69["fast"]["tests"])} + {n(p69["full"]["tests"])} pass'),
                  (p87, L87, f'{p87["head"]}, the port on Modules II: {n(p87["fast"]["tests"])} + {n(p87["full"]["tests"])} pass')]:
    x = xat(p["created"])
    fig1.append(f'<circle class="ring" cx="{x:.1f}" cy="{y}" r="9"/>')
    fig1.append(f'<text class="cl" x="{x - 13:.1f}" y="{y - 18}" text-anchor="end">{esc(lab)}</text>')
fig1.append('</svg>')
FIG1 = "".join(fig1)

# ---- Figure 2: the ten failures, by cause ----
last = sampled[-1]["fast"]["failing"]
order = [("DefStaticsParity", k) for k in (1, 4, 33, 38, 39, 40, 41, 42)] + [("Editing.TableDecorations", 1), ("DefStaticsParity", 2)]
byk = {(f["group"], f["n"]): f for f in last}
CAUSE = {("Editing.TableDecorations", 1): "b", ("DefStaticsParity", 2): "c"}
W, G = 66, 8
fig2 = ['<svg viewBox="0 0 900 230" role="img" class="chart" aria-label="Ten boxes, one per failing test on #2635\'s last run, in three groups. '
        'Eight DefStaticsParity tests that count how many units are re-analyzed after an edit in a module: each expected 2, 3, 4 or 6 and received 1 or 2. '
        'One table test, Editing.TableDecorations 1, expected true and received false. One corpus test, DefStaticsParity 2, a mismatch on one livelits document.">']
x = 20
groups = {"a": [], "b": [], "c": []}
for key in order:
    c = CAUSE.get(key, "a")
    f = byk[key]
    groups[c].append(x)
    short = ("DSP " if key[0] == "DefStaticsParity" else "Table ") + str(key[1])
    val = f'{f["expected"]} → {f["received"]}' if f.get("expected") else "mismatch"
    fig2.append(f'<rect class="cb {c}" x="{x}" y="96" width="{W}" height="62" rx="8"/>')
    fig2.append(f'<text class="cl" x="{x + W / 2}" y="120" text-anchor="middle" font-weight="700">{short}</text>')
    fig2.append(f'<text class="cl" x="{x + W / 2}" y="142" text-anchor="middle">{esc(val)}</text>')
    x += W + G + (22 if key == ("DefStaticsParity", 42) or key == ("Editing.TableDecorations", 1) else 0)
for c, title, sub in [("a", "8 · per-member module analysis meets Modules II", "#2469's tests: units re-analyzed after an edit, expected → received"),
                      ("b", "1 · dev's completion", "a livelits table test"),
                      ("c", "1 · not found", "a livelits document")]:
    xs = groups[c]
    x0, x1 = xs[0], xs[-1] + W
    fig2.append(f'<path class="br {c}" d="M{x0},86 v-8 H{x1} v8"/>')
    anchor_x, anchor = {"a": (x0, "start"), "b": (x1, "end"), "c": (x0, "start")}[c]
    fig2.append(f'<text class="ct" x="{anchor_x}" y="40" text-anchor="{anchor}">{esc(title)}</text>')
    fig2.append(f'<text class="cv" x="{anchor_x}" y="60" text-anchor="{anchor}">{esc(sub)}</text>')
fig2.append(f'<text class="cv" x="20" y="190">#2635\'s last run, {sampled[-1]["head"]} (2026-10-17): the same ten fail in Fast checks ({n(sampled[-1]["fast"]["tests"])} tests) '
            f'and Full tests ({n(sampled[-1]["full"]["tests"])}).</text>')
fig2.append('<text class="cv" x="20" y="210">All three have been known since the merge: 43089b065d and 11fbc4480d on 2026-10-01, and cefa5c2c5c on 2026-10-10.</text>')
fig2.append('</svg>')
FIG2 = "".join(fig2)


# ---- Tables ----
def gh_run(r):
    return f'https://github.com/hazelgrove/hazel/actions/runs/{r}'


rows = []
for s in sampled:
    f = s["fast"]
    names = ", ".join(esc(x["group"] + " " + str(x["n"])) for x in f["failing"])
    rows.append(f'<tr><td class="n">{s["created"][:16].replace("T", " ")}</td><td class="n"><code>{s["head"]}</code></td>'
                f'<td class="n"><a href="{gh_run(s["run"])}">{s["run"]}</a></td><td class="n bad">{f["failures"]}</td>'
                f'<td class="n">{n(f["tests"])}</td><td>{names}</td></tr>')
SAMPLED = "".join(rows)


def assert_rows(keys):
    out = []
    for key in keys:
        f = byk[key]
        exp = esc(f["expected"] or "")
        rec = esc(f["received"] or "")
        out.append(f'<tr><td><code>{esc(key[0])} {key[1]}</code></td><td>{esc(f["name"])}</td><td>{esc(f["check"][:120])}</td>'
                   f'<td class="n">{exp}</td><td class="n bad">{rec}</td></tr>')
    return "".join(out)


A_ROWS = assert_rows(order[:8])
first = {(f["group"], f["n"]): f for f in sampled[0]["fast"]["failing"]}
OLD_ROWS = "".join(f'<tr><td><code>{esc(k[0])} {k[1]}</code></td><td>{esc(f["name"])}</td><td>{esc(f["check"][:80])}</td>'
                   f'<td class="n">{esc(f["expected"] or "")}</td><td class="n bad">{esc(f["received"] or "")}</td></tr>'
                   for k, f in first.items() if k[0] in ("ModRoot", "TypeDeps", "LabelBench"))


def yes(b):
    return '<span class="good">yes</span>' if b else '<span class="cv2">no</span>'


FILE_ROWS = "".join(f'<tr><td>{esc(label)}</td><td>{", ".join("<code>" + esc(x.replace("test/", "")) + "</code>" for x in v["defstatics_tests"]) or yes(False)}</td>'
                    f'<td>{yes(v["table_decorations_test"])}</td></tr>' for label, v in files.items())

p_today = parents["2469_today"]
today_fails = ", ".join(f'{x["group"]} {x["n"]}' for x in p_today["fast"]["failing"])

# ---- Embedded data ----
report_data = {
    "report": 18, "title": None, "date": "2026-10-19",
    "question": "For Cyrus, from Matthew: why does CI fail on #2635, the branch that merges modular editors (#2469) into the livelits branch (#2597)? (^ticket(385); the 10-17 trial merge was ^ticket(156))",
    "fetched": "2026-10-19, 09:40 to 09:55 MDT, from GitHub's Actions API and a git checkout (018/drivers/collect018.py)",
    "runs_2635": {"what": "every CI run on integration/livelits-modular-editors (#2635), newest first; conclusion as GitHub gives it (cancelled: superseded by a newer push)", "runs": runs},
    "sampled_runs": {"what": "the failing runs read: each Fast checks job's alcotest summary (failures, tests run, seconds) and each failing test with its first failed check, expected and received; Full tests too for the last run", "runs": sampled},
    "parents": {"what": "the parents' runs that matter: #2597 at its head, #2469 at the head that contains what #2635 merged, and #2469 today", **parents},
    "parent_runs": {"what": "every CI run on each parent branch since 2026-10-01, for the timeline", **lanes},
    "test_files": {"what": "which failing tests' files exist on each ref: the DefStatics tests (DefStaticsParity, ModRoot, TypeDeps, LabelBench) and whether test/ mentions TableDecorations", **files},
    "git": {"what": "ancestry and merge facts from git (merge-base, cherry, merge-tree)", **facts},
}

TITLE = "#2635 has failed CI on every run since the merge, for three known reasons"
report_data["title"] = TITLE

PAGE = open("018/drivers/page018.html").read()
for k, v in {"{{TITLE}}": TITLE, "{{FIG1}}": FIG1, "{{FIG2}}": FIG2, "{{SAMPLED}}": SAMPLED, "{{A_ROWS}}": A_ROWS, "{{OLD_ROWS}}": OLD_ROWS,
             "{{FILE_ROWS}}": FILE_ROWS, "{{RUNS}}": str(len(runs)), "{{RED}}": str(count(runs, "failure")), "{{CANCELLED}}": str(count(runs, "cancelled")),
             "{{G97}}": str(count(lanes["2597"]["runs"], "success")), "{{R97}}": str(count(lanes["2597"]["runs"], "failure")),
             "{{G69}}": str(count(lanes["2469"]["runs"], "success")), "{{R69}}": str(count(lanes["2469"]["runs"], "failure")),
             "{{NSAMPLED}}": str(len(sampled)), "{{T87F}}": n(p87["fast"]["tests"]), "{{T87U}}": n(p87["full"]["tests"]), "{{TODAY_FAILS}}": esc(today_fails), "{{TODAY_TESTS}}": n(p_today["fast"]["tests"]),
             "{{CHERRY}}": str(facts["full_commits_cherry_picked"]), "{{FULL_SINCE}}": str(facts["full_commits_since_merge"]),
             "{{CONFLICTS}}": str(len(facts["conflicted_files_2635_with_full"])), "{{BEHIND}}": str(facts["full_behind_dev"]),
             "{{DATA}}": json.dumps(report_data, ensure_ascii=False).replace("</", "<\\/")}.items():
    PAGE = PAGE.replace(k, v)
assert "{{" not in PAGE, PAGE[PAGE.index("{{"):PAGE.index("{{") + 40]
open("018/index.html", "w").write(PAGE)

# ---- The series card's thumbnail: three rows of ticks ----
th = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 300" width="450" height="300" font-family="system-ui, \'DejaVu Sans\', sans-serif" font-size="15">',
      '<style>.ink { fill: #1f2328; } .muted { fill: #5b6470; } .good { fill: #15803d; } .bad { fill: #b91c1c; } .cx { fill: #c9c4b8; }',
      '@media (prefers-color-scheme: dark) { .ink { fill: #e8e6e3; } .muted { fill: #a2a9b3; } .good { fill: #4ade80; } .bad { fill: #f87171; } .cx { fill: #5a6068; } }</style>']
tx0, tx1 = 24, 426


def tx(s):
    return tx0 + (ts(s) - T0) / (T1 - T0) * (tx1 - tx0)


for y, title, rs in [(58, "#2635: livelits × modular editors", runs), (128, "#2597: livelits", lanes["2597"]["runs"]),
                     (198, "#2469: modular editors", lanes["2469"]["runs"]), (268, "#2687: modular editors + Modules II", lanes["2687"]["runs"])]:
    th.append(f'<text class="ink" x="{tx0}" y="{y - 22}" font-weight="700">{esc(title)}</text>')
    for r in sorted(rs, key=lambda r: r["conclusion"] == "cancelled", reverse=True):
        th.append(f'<rect class="{COL.get(r["conclusion"], "cx")}" x="{tx(r["created"]) - 1.5:.1f}" y="{y - 14}" width="3" height="28"/>')
th.append('</svg>')
open("018/img/thumb.svg", "w").write("\n".join(th))
print("wrote 018/index.html and 018/img/thumb.svg")
