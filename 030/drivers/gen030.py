#!/usr/bin/env python3
"""^report(30): two days of game scripts in Hazel, for Messed Up Dress Up (MUDU), since the 2026-10-21 meeting with Cyrus:
where the goal stands. Numbers from GitHub runs whose rows are in 030/data/ (map_vs_shipped, map_vs_fumola, map_setup,
map_setup_walks, fast_path), and from earlier reports, cited by link."""
import os, json, glob, statistics, html

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
D = os.path.join(R, "data")
fmt = lambda v: "–" if v is None else (f"{v:.2g}" if v < 0.1 else f"{v:.3g}" if v < 100 else f"{v:,.0f}")


def jobs(run):
    return sorted(glob.glob(os.path.join(D, run, "job-*")))


def rows(job, side):
    acc = {}
    for f in sorted(glob.glob(os.path.join(job, f"{side}_*.json"))):
        for r in json.load(open(f)):
            acc.setdefault((r.get("k"), r["n"]), []).append(r)
    return acc


def med(run, side, n, k, key=None):
    """the median over a run's jobs of each job's better round"""
    vals = []
    for j in jobs(run):
        rs = rows(j, side).get((key, n))
        if rs:
            vals.append(min(r[k] for r in rs))
    return statistics.median(vals) if vals else None


def runners(run):
    return "; ".join(sorted({" ".join(open(f).read().split()[3:-1]) for f in glob.glob(os.path.join(D, run, "job-*", "runner.txt"))}))


# ---- Figure 1: one World move at 64x64, on the same runners (map_vs_fumola), against a 60 fps frame
N = 64
F1 = [
    ("Hazel, the world passed in (the rule as shipped)", med("map_vs_fumola", "hazel", N, "passed"), "bad"),
    ("Hazel, passed as a handle (Hazel.value)", med("map_vs_fumola", "hazel", N, "passed_handle"), "bad"),
    ("Fumola, the world passed in as text", med("map_vs_fumola", "fumola", N, "passed"), "bad"),
    ("Fumola, held as a list", med("map_vs_fumola", "fumola", N, "held_list"), "warn"),
    ("Hazel, held in the game's map (Common.squares)", med("map_vs_fumola", "hazel", N, "map"), "good"),
    ("Fumola, held in a HashMap", med("map_vs_fumola", "fumola", N, "held_map"), "good"),
]
FRAME = 1000 / 60


def hbars(items, w=760, lo=0.1, hi=1000, line=None, line_label=""):
    import math
    rowh, left, right = 30, 330, 70
    h = rowh * len(items) + 34
    X = lambda v: left + (w - left - right) * (math.log10(max(v, lo)) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    o = [f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="horizontal bars, log scale">']
    for t in (0.1, 1, 10, 100, 1000):
        if lo <= t <= hi:
            o.append(f'<line x1="{X(t):.1f}" x2="{X(t):.1f}" y1="4" y2="{h - 22}" class="g"/><text x="{X(t):.1f}" y="{h - 6}" text-anchor="middle" class="t">{fmt(t)} ms</text>')
    if line:
        o.append(f'<line x1="{X(line):.1f}" x2="{X(line):.1f}" y1="0" y2="{h - 22}" class="lim"/><text x="{X(line) + 4:.1f}" y="12" class="lt">{html.escape(line_label)}</text>')
    for i, (label, v, cls) in enumerate(items):
        y = 18 + i * rowh
        o.append(f'<text x="{left - 8}" y="{y + 12}" text-anchor="end" class="t">{html.escape(label)}</text>')
        if v is not None:
            o.append(f'<rect x="{left}" y="{y}" width="{max(1, X(v) - left):.1f}" height="16" rx="3" class="bar {cls}"><title>{html.escape(label)}: {fmt(v)} ms</title></rect>')
            o.append(f'<text x="{X(v) + 5:.1f}" y="{y + 12}" class="t">{fmt(v)} ms</text>')
    o.append("</svg>")
    return "".join(o)


FIG1 = hbars(F1, line=FRAME, line_label="one frame at 60 fps (16.7 ms)")

# ---- Figure 2: what each fix bought, Hazel at 64x64 (map_vs_shipped: trial/r25-best against trial/r25-553, same runners)
F2 = [
    ("passed in, report 27's build (r25-best)", med("map_vs_shipped", "best", N, "passed"), "bad"),
    ("held in the map, r25-best (no 547: re-walked)", med("map_vs_shipped", "best", N, "map"), "bad"),
    ("passed in, with 547, 548, 551 (r25-553)", med("map_vs_shipped", "553", N, "passed"), "bad"),
    ("passed as a handle (551)", med("map_vs_shipped", "553", N, "passed_handle"), "bad"),
    ("held in the map, with 547, 548, 551", med("map_vs_shipped", "553", N, "map"), "good"),
]
FIG2 = hbars(F2, line=FRAME, line_label="60 fps frame")

# ---- tables
SIZES = [3, 8, 16, 32, 64]
T_MAP = "".join(
    f"<tr><td class=n>{n}x{n} ({n*n:,})</td><td class=n>{fmt(med('map_vs_fumola', 'hazel', n, 'passed'))}</td><td class=n>{fmt(med('map_vs_fumola', 'hazel', n, 'map'))}</td>"
    f"<td class=n>{fmt(med('map_vs_fumola', 'fumola', n, 'passed'))}</td><td class=n>{fmt(med('map_vs_fumola', 'fumola', n, 'held_map'))}</td>"
    f"<td class=n>{fmt(med('map_vs_fumola', 'hazel', n, 'map_setup'))}</td><td class=n>{fmt(med('map_vs_fumola', 'fumola', n, 'setup_ms'))}</td></tr>"
    for n in [3, 4, 6, 8, 12, 16, 24, 32, 48, 64])
FP = {}
for j in jobs("fast_path"):
    st, fp = rows(j, "stats"), rows(j, "fastpath")
    for key in st:
        if key in fp and key not in FP:
            FP[key] = (st[key][0]["by_kind"].get("evaluate", 0), fp[key][0]["by_kind"].get("evaluate", 0))
fp_ratio = lambda k, n: statistics.median(
    min(r["ms"] for r in rows(j, "fastbest")[(k, n)]) / min(r["ms"] for r in rows(j, "best")[(k, n)]) for j in jobs("fast_path"))
T_FP = "".join(
    f"<tr><td><code>{k}</code></td><td class=n>{n:,}</td><td class=n>{FP[(k, n)][0]:,}</td><td class=n>{FP[(k, n)][1]:,}</td><td class=n>{fp_ratio(k, n):.2f}</td></tr>"
    for k, n in [("count", 1000), ("fib", 16), ("h_walk", 3000), ("h_ref", 3000), ("sumbuild", 3000)])
c1000 = FP[("count", 1000)]
hm64, fm64 = med("map_vs_fumola", "hazel", 64, "map"), med("map_vs_fumola", "fumola", 64, "held_map")
hs64, fs64 = med("map_vs_fumola", "hazel", 64, "map_setup"), med("map_vs_fumola", "fumola", 64, "setup_ms")
hp64 = med("map_vs_fumola", "hazel", 64, "passed")
S3 = lambda k: med("map_setup", "setup", 64, k)
W3, W2 = med("map_setup_walks", "three", 64, "map_setup"), med("map_setup_walks", "two", 64, "map_setup")

chip = lambda cls, t: f'<span class="tag {cls}">{t}</span>'
DONE, PART, PLAN, BLOCK = chip("ans", "built"), chip("block", "in part"), chip("", "planned"), chip("block", "waits")
STATUS = f"""<div class="scroll"><table><tr><th>the goal, piece by piece</th><th>where it is</th><th></th></tr>
<tr><td>Hazel code in the game, one module per room plus 📚 Common</td><td>The 🧩 Scripting panel (matthewhammer/kids-choice-games#1: the trap room's levers through <code>Hazel.runProgram</code>, the program shown in Hazel's tiles), then the five rooms' rules in Hazel (matthewhammer/kids-choice-games#2), each under <code>?logic=hazel</code>, checked against the JS.</td><td>{DONE}</td></tr>
<tr><td>Fumola code in the game</td><td>The same rules in Fumola, wasm, pinned build (matthewhammer/kids-choice-games#4), 20,653 cases agreeing with the Hazel rules in a node check.</td><td>{DONE}</td></tr>
<tr><td>A JS / Hazel / Fumola chip on each code box; the JS read-only, the game's own code; a master chip, JS by default</td><td>Today a page-wide <code>?logic=</code> switch, Hazel and Fumola on separate PRs. <code class="ref"><b>^ticket(</b>566<b>)</b></code>.</td><td>{PLAN}</td></tr>
<tr><td>The three equivalent, held by tests as the code changes</td><td>Node checks, Hazel against JS and Fumola against Hazel, in the two PRs; not all three in CI. <code class="ref"><b>^ticket(</b>567<b>)</b></code>.</td><td>{PART}</td></tr>
<tr><td>A tool measuring each script's overhead over JS</td><td>The game records Hazel's compile time; the speed probes time rules. <code class="ref"><b>^ticket(</b>568<b>)</b></code>.</td><td>{PLAN}</td></tr>
<tr><td>Speed-run standards: each setting a minimum fps where its scripts run</td><td><code class="ref"><b>^ticket(</b>569<b>)</b></code>.</td><td>{PLAN}</td></tr>
<tr><td>Hazel fast enough for every room at 60 fps</td><td>Levers, trap doors, the castle: yes. The world's ways: not as the game calls them today, the world passed in at every move (a call walks the whole world: {fmt(hp64)} ms at 64x64 even on the trial build); yes with this week's library fixes and the map held ({fmt(hm64)} ms). The fixes are on trial branches, not in the library build the game loads, and the game does not hold the map yet.</td><td>{BLOCK}</td></tr>
<tr><td>Fumola fast enough</td><td>Yes: about a millisecond a call, flat with its HashMap ({fmt(fm64)} ms at 64x64).</td><td>{DONE}</td></tr>
</table></div>"""

# ---- the game's rules three ways (data/rules.json, from drivers/rules.mjs): a box per room, as the game's 🧩 panel has them
RULES = json.load(open(os.path.join(D, "rules.json")))
ENG = [("js", "JS"), ("hazel", "🧩 Hazel"), ("fumola", "🍄 Fumola")]
def rule_box(key, title, texts, note=""):
    chips = "".join(f'<button type="button" data-eng="{e}" aria-pressed="{str(e == "hazel").lower()}">{lab}</button>' for e, lab in ENG if e in texts)
    pres = "".join(f'<pre class="code rule" data-eng="{e}"{"" if e == "hazel" else " hidden"}>{html.escape(texts[e])}</pre>' for e, _ in ENG if e in texts)
    return f'<div class="rulebox" id="rule-{key}"><div class="rb-head"><b>{title}</b><span class="chips">{chips}</span></div>{note}{pres}</div>'
def js_text(parts):
    return "\n\n".join(f"// {p['file'] or '?'}: {p['name']}\n{p['text']}" for p in parts)
RULE_BOXES = rule_box("preamble", "The program's start (Hazel): the sum types", {"hazel": RULES["preamble"]},
    '<p class="note">Fumola needs none of this: its variants (<code>#N</code>, <code>#Waterfall</code>) are not declared. The kinds are generated from the game\'s own lists (<code>PLACES</code>, <code>ROOM_KINDS</code>).</p>') + \
  rule_box("common", "📚 Common", {"js": "// The game's JS has no common module: each room's functions carry what they need.", "hazel": RULES["common"]["hazel"], "fumola": RULES["common"]["fumola"]}) + \
  "".join(rule_box(r["name"], html.escape(r["label"]), {"js": js_text(r["js"]), "hazel": r["hazel"], "fumola": r["fumola"]}) for r in RULES["rooms"])
RULES_SECTION = f"""<h2 id="rules">The rules, three ways</h2>
<p>Each room's rule as the game's 🧩 Scripting panel shows it (<code class="ref"><b>^ticket(</b>566<b>)</b></code>): the game's own JS (read only, the functions that run), and the same rule in Hazel and in Fumola, the ones a player can edit. A chip on each box picks the language; the one at the top picks for every box. All three answer the same for every case the game can give them: tools/hazelrules531.mjs (32,761 cases) and tools/fumola_rules_check.mjs (20,649) check it on every push (<code class="ref"><b>^ticket(</b>567<b>)</b></code>). Their vocabulary is sums, not text, as Languages of Play prescribes: directions, sides, wirings, square and room kinds. From {html.escape(RULES['source'])}.</p>
<div class="rulebox master"><div class="rb-head"><b>every box</b><span class="chips">{"".join(f'<button type="button" data-eng="{e}" aria-pressed="{str(e == "hazel").lower()}">{lab}</button>' for e, lab in ENG)}</span></div></div>
{RULE_BOXES}
<script>
document.addEventListener("DOMContentLoaded", () => {{
  const show = (box, eng) => {{
    if (!box.querySelector(`pre.rule[data-eng="${{eng}}"]`)) return;
    box.querySelectorAll("pre.rule").forEach(p => p.hidden = p.dataset.eng !== eng);
    box.querySelectorAll(".chips button").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.eng === eng)));
  }};
  document.querySelectorAll(".rulebox:not(.master)").forEach(box => box.querySelectorAll(".chips button").forEach(b => b.onclick = () => show(box, b.dataset.eng)));
  document.querySelectorAll(".rulebox.master .chips button").forEach(b => b.onclick = () => {{
    document.querySelectorAll(".rulebox:not(.master)").forEach(box => show(box, b.dataset.eng));
    document.querySelectorAll(".rulebox.master .chips button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
  }});
}});
</script>
"""
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Game Scripts in Hazel, Two Days In</title>
<meta name="description" content="Since the 2026-10-21 meeting: Hazel as Messed Up Dress Up's script system. The rules run in Hazel and in Fumola beside the game's JS; a World move with the game's own map takes about a millisecond at every size, but only with library fixes the game's build does not have yet. Where the goal stands, and the plan.">
<style>{STYLE}
svg.chart {{ width: 100%; height: auto; font: 12px system-ui, sans-serif; }} svg .g {{ stroke: var(--line); }} svg .t {{ fill: var(--muted); }}
svg .lim {{ stroke: var(--accent); stroke-dasharray: 4 3; stroke-width: 1.5; }} svg .lt {{ fill: var(--accent); font-size: 11px; }}
svg .bar.good {{ fill: var(--good); }} svg .bar.warn {{ fill: var(--warn); }} svg .bar.bad {{ fill: var(--bad); opacity: 0.8; }}
.rulebox {{ border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; margin: 10px 0; background: var(--paper); }}
.rulebox.master {{ background: transparent; }}
.rulebox .rb-head {{ display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: center; justify-content: space-between; }}
.rulebox .chips {{ display: inline-flex; gap: 4px; }}
.rulebox .chips button {{ font: inherit; font-size: 0.85em; padding: 1px 10px; border-radius: 999px; border: 1px solid var(--line); background: var(--bg, transparent); color: var(--ink); cursor: pointer; }}
.rulebox .chips button[aria-pressed="true"] {{ border-color: var(--accent); color: var(--accent); font-weight: 600; }}
.rulebox pre.rule {{ white-space: pre; overflow: auto; max-height: 30em; font-size: 0.8em; margin: 6px 0 2px; }}
.tag {{ display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 0 8px; font-size: 0.8em; white-space: nowrap; }}
</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>30<b>)</b></code> · game scripts · 2026-10-23 · <span class="wip">work in progress</span> · about 8 minutes to read</p>
<h1>Game Scripts in Hazel, Two Days In</h1>
<p class="sub">Matthew: <q>a report about the last 2 days -- with an idea of where we are with our goals of game scripts in hazel, for MUDU.</q> The goal came out of his 2026-10-21 meeting with Cyrus Omar, who encouraged following the excitement: Hazel as a game script system, starting with Messed Up Dress Up (MUDU), as a general way to put Hazel code into a JS/HTML app's behavior. The two days since found some gaps in what the scripts can say, and mostly gaps in speed.</p>

<div class="headline">
<p><b>Short answers.</b></p>
<ol class="ans">
<li><b>The game's rules run in Hazel and in Fumola, beside its JS.</b> Five rooms (the trap room, the tree houses, placed levers, the world's ways, the castle) and a 📚 Common module, written in both languages, each checked against the game's own JS: on three open pull requests to the game, behind a page-wide switch.</li>
<li><b>Fumola is fast enough now; Hazel is, on trial branches.</b> One World move at 64x64 (4,096 squares), on the same machines: Fumola with its HashMap {fmt(fm64)} ms; Hazel with the game's own map {fmt(hm64)} ms ({hm64 / fm64:.1f}x). Both well inside a 60 fps frame (16.7 ms), and both flat from 3x3 to 64x64. Hazel's number needs this week's library fixes, which the library the game loads does not have, and the game holding the map. With the world passed in at every move, as the game calls its rules today, the move walks the whole world: {fmt(hp64)} ms on the same build (Figure 1).</li>
<li><b>Most of the two days went to Hazel's speed, and it paid.</b> Functions keep their closures across the JS boundary; list loops no longer re-type the whole list each time; a big value can cross once, as a handle; values skip the evaluator's five stages ({c1000[0]:,} passes for <code>count(1000)</code> become {c1000[1]:,}). Together, with a map, a World move went from {fmt(med('map_vs_shipped', 'best', 64, 'passed'))} ms to {fmt(med('map_vs_shipped', '553', 64, 'map'))} ms (Figure 2). All on trial branches, measured on GitHub, none in the game yet.</li>
<li><b>What is left for Hazel is the cost of each pass.</b> Making the map, once a world, takes 1.5 to 2.1 s at 64x64 on GitHub's runners ({fmt(hs64)} ms against Fumola's {fmt(fs64)} on the same ones): three walks of a list (two now) at Hazel's cost per evaluator pass, which pays for the editor's live features on every term (^report(29)).</li>
<li><b>Next: the three-way script boxes.</b> Each room's box a JS, Hazel or Fumola chip (the JS shown read-only, the game's own code; Hazel and Fumola to edit), a master chip, tests that keep the three equivalent, a tool for each script's overhead, and speed runs that hold each setting to a frame rate.</li>
</ol>
</div>

<figure class="fig" id="fig-move">{FIG1}<figcaption><b>Figure 1.</b> One World move (a way out walked through, mid-map, going east) on a 64x64 world, ms, log scale, against one 60 fps frame. Hazel on <code>trial/r25-553</code> (the best build with this week's fixes 547, 548 and 551), the rule texts from the game's branch <code>hazel-map-553</code>; Fumola's wasm from <code>667a34d</code>, ^report(27)'s driver. The same four GitHub runners for both, alternating, each side's better round, the median over the runners (run 39887272978).</figcaption></figure>

<h2 id="goal">The goal, and where each piece is</h2>
{STATUS}

<h2 id="built">What was built</h2>
<ul>
<li><b>The 🧩 Scripting panel</b> (matthewhammer/kids-choice-games#1): one editor per room that has logic, and 📚 Common, the bodies of the modules of one Hazel program; Hazel builds the program (<code>Hazel.runProgram</code>) and shows it in its own tiles, in a frame, with its error marks. A rule says what to do as data (<code>Cmd</code>: <code>Flip("lever_L", Done)</code>, <code>GoSquare(c, r, side, Done)</code>), and the game does it.</li>
<li><b>The rooms' rules in Hazel</b> (matthewhammer/kids-choice-games#2): the trap room's red and blue levers, the tree houses' trap doors, placed levers and trap doors, the world's ways, the castle's pits and ladders, under <code>?logic=hazel</code>, every decision checked against the JS in the game's browser checks. Its speed runs (^report(25)): levers add 0.8 to 3.6 ms, a world way about 5.6 ms on the test map, a fall or a ladder hides behind the walk, and the program compiles in about 1.2 s at load.</li>
<li><b>The same rules in Fumola</b> (matthewhammer/kids-choice-games#4): wasm, a pinned build, a node check of 20,653 cases against the Hazel rules; a rule call about 1.1 to 1.4 ms against Hazel's 2.9 on one runner, and Fumola sets up in 4 ms where Hazel compiles in 514 (^report(27)).</li>
<li><b>The game's own map</b> (<code class="ref"><b>^ticket(</b>553<b>)</b></code>, branch <code>hazel-map-553</code>): 📚 Common gains a balanced search tree of the world's squares (<code>squares</code>, <code>square</code>, <code>set_square</code>; put in order first when the game sends them in another), and 🗺️ World a rule that looks one square up (<code>with_squares</code>) beside the shipped one that walks the list. Checked in every run: on a world of random kinds and ways, its cells shuffled, the two agree for every square and all eight directions (392 cases).</li>
</ul>

{RULES_SECTION}
<h2 id="lop">Languages of Play</h2>
<p><i>Languages of Play: Towards semantic foundations for game interfaces</i> (Chris Martens and Matthew A. Hammer, 2017, <a href="https://arxiv.org/abs/1703.05410">arXiv:1703.05410</a>) treats what a player can say to a game as a language of its own, a <i>player intent language</i>, and reads a game through programming-language theory, in the slogan "games as programming languages". Its running example is a small game of moving between rooms and taking things, under five interfaces (point-and-click, bird's-eye, WASD, command line, hypertext), and its Table 1 pairs each part of a language definition with a part of a game. The game's rules, written three ways, line up with that table closely:</p>
<div class="scroll"><table><tr><th>the paper</th><th>its game concept</th><th>in Messed Up Dress Up's rules</th></tr>
<tr><td>syntax</td><td>recognized player intents: <code>direction ::= north | south | east | west</code>, <code>intent ::= move⟨direction⟩ | collect</code></td><td>the <code>Event</code> sum: <code>Pull(Side)</code>, <code>PullBoulder(Side)</code>, <code>PullHatch(Int)</code>, <code>PullThing(Int)</code>, <code>FallPit(Int)</code>, <code>WayOut(Int)</code>, <code>Way(Dir)</code>, with <code>Dir = + N + NE + E + SE + S + SW + W + NW</code>. Taking a way out of a square, by whichever control, goes through one door handler (<code>worldWalk</code>) and reaches the rule as the one intent <code>Way(d)</code>, as the paper's five interfaces all end in <code>move⟨direction⟩</code>.</td></tr>
<tr><td>operational semantics</td><td>game mechanics: a game step ⟨G₁; intent⟩ ⟶ ⟨G₂; resp⟩</td><td>a room's rule, <code>on_event : (Globals, Event) -> Cmd</code>: the state it is told (<code>Globals</code>) and the intent give a response as data, which the game then carries out (its new state). <code>Done</code> alone is the paper's failure, a way that leads nowhere; <code>GoSquare(c, r, side, Done)</code> its success.</td></tr>
<tr><td>type system</td><td>contextual interface: only the intents that make sense in this state</td><td>the sums themselves: before them, a direction was any text, and a rule could be asked about <code>"up"</code> (the Fumola check had a case for it); now it cannot be said. The paper calls this the subtractive side of an interface's syntax. What is offered in a given state (a lever only where there is one) is still the game's JS, not a type.</td></tr>
<tr><td>a completeness conjecture: every state and intent has a next state and a response</td><td>proved, in a PL, by cases</td><td>checked, not proved: on every push, every case the game can give each room (32,761 for Hazel, 20,649 for Fumola) has an answer, and the same answer in all three languages (<code class="ref"><b>^ticket(</b>567<b>)</b></code>).</td></tr>
<tr><td>play traces as straight-line programs</td><td>a log of intents and responses, as structured terms</td><td>a response is already a little straight-line program, each command with the rest after it (<code>Flip(L, SetPit(0, true, Done))</code>), which the game runs in order; a log of <code>Event</code>s and <code>Cmd</code>s would be the paper's trace, not kept yet.</td></tr>
<tr><td>player skills as general programs</td><td>players composing actions into their own programs (BOTS, Cube Composer)</td><td>the editable Hazel and Fumola boxes: a player (or M and N) can rewrite a room's rule in the game and play it at once, so the mechanics, not only the intents, become a language players write in.</td></tr>
</table></div>
<p><b>Where the game goes beyond the paper.</b> The paper's languages are mathematical definitions. Here the mechanics are programs in two real languages beside the JS that defines them, held equal by tests, so one game has three semantics for the same intent language, and the 🧩 panel lets a player see and change which one runs. It also gives the paper's link to Hazelnut (an editor whose edits keep a program meaningful, cited there as the model for editing languages) a concrete place: the Hazel boxes are shown in Hazel's own tiles.</p>
<p><b>Where it does not yet.</b> The game's interfaces (keys, the on-screen controller, clicks) are not themselves written as languages, as the paper's five are; the game's state crosses into the rules as a record of text and numbers made by its JS, not as typed terms from the start; and Hazel's sums could not yet live in the 📚 Common module, where the game's vocabulary belongs, until hazelgrove/hazel#2729 (a module's sum types usable after it), which came out of this.</p>
<h2 id="speed">Speed: what was found, and fixed</h2>
<p>Why a Hazel rule cost about 40 ms on a 16x16 world when the JS took 0.003 (^report(25)), why Fumola runs the same rule 2.4 to 10 times faster (^report(29)), and the fixes, each on a trial branch built by GitHub:</p>
<ul>
<li><b>The boundary's floor</b> (<code class="ref"><b>^ticket(</b>539<b>)</b></code>, branch <code>lib-floor</code>): a call's argument bound in the environment, not written into the call and stepped back into a value node by node.</li>
<li><b>Closures kept whole</b> (<code class="ref"><b>^ticket(</b>547<b>)</b></code>, real branch <code>lib-closures</code>, <code class="ref"><b>^ticket(</b>558<b>)</b></code>): a function the library returns keeps its environment; it used to have its captured values written into its body, so a held list was evaluated again, part by part, at every call. One reference to a held list of 3,000: 77x faster. A CI test now holds it (<code class="ref"><b>^ticket(</b>552<b>)</b></code>: a call's evaluator passes are the same for a held list of 100 and of 10,000; without 547 the test fails).</li>
<li><b>List loops linear</b> (<code class="ref"><b>^ticket(</b>548<b>)</b></code>): a loop passing a growing list on pushed its type over every element each time, with a fresh id for each; building and summing 3,000 numbers, 8.9x faster.</li>
<li><b>Handles</b> (<code class="ref"><b>^ticket(</b>551<b>)</b></code>): <code>Hazel.value(x)</code> converts a JS value once; a call given the handle takes it as it is.</li>
<li><b>A fast path for values</b> (<code class="ref"><b>^ticket(</b>559<b>)</b></code>): with nothing probed, reused or published (the library's calls, a game's rules), a term already a value comes back at once instead of passing through the evaluator's five stages; the step count reads the same and the evaluator's tests pass unchanged. A third fewer passes on loops, about a tenth of their time:</li>
</ul>
<div class="scroll"><table><tr><th>program</th><th>n</th><th>passes</th><th>passes, fast path</th><th>time, fast path / without</th></tr>{T_FP}</table></div>
<p class="note">Passes from the counter build and the fast path on it, exact; times from <code>trial/r25-best</code> and the same fast path on it, four GitHub runners, alternating, the median (run 39885788957). <code>h_ref</code> is a reference to a held list, on a build without 547: skipped whole now.</p>
<figure class="fig" id="fig-fixes">{FIG2}<figcaption><b>Figure 2.</b> Hazel's World move at 64x64, ms, log scale, as the fixes stack: report 27's build (<code>trial/r25-best</code>) and the same with 547, 548 and 551 (<code>trial/r25-553</code>), the world passed in, as a handle, and held in the game's map. Holding the map pays only with 547; without it, the map is re-walked at every call and is slower than the list. Four GitHub runners, alternating (run 39886598556).</figcaption></figure>

<h3 id="vs-fumola">The map against Fumola's, by size</h3>
<div class="scroll"><table><tr><th>world (squares)</th><th>Hazel, passed</th><th>Hazel, map</th><th>Fumola, passed</th><th>Fumola, HashMap</th><th>Hazel, map's set-up</th><th>Fumola, set-up</th></tr>{T_MAP}</table></div>
<p class="note">ms, the same runners for both (run 39887272978: {runners('map_vs_fumola')}).</p>
<h3 id="setup">The map's set-up</h3>
<p>Once a world, {fmt(S3('annotated_squares'))} ms at 64x64 on the trial build, measured in parts: putting the squares in order and checking it ({fmt(S3('annotated_in_order'))}), counting them ({fmt(S3('annotated_count'))}), building the tree ({fmt(S3('annotated_take'))}); bringing the cells over from JS is {fmt(S3('annotated_id'))}. Taking the type annotations off the map's helpers changes nothing ({fmt(S3('unannotated_squares'))}). Each part is a walk of the list at Hazel's cost per pass, about 60 to 70 µs a square even for the count; doing the count in the same walk as the order check saved {100 * (1 - W2 / W3):.0f}% ({fmt(W3)} to {fmt(W2)} ms; runs 39888318843, 39890490518).</p>

<h2 id="say">What the scripts can say</h2>
<ul>
<li><b>Ordering strings:</b> a map keyed by a lever's id (a string) needs strings in order. Hazel has <code>string_compare</code>, returning <code>Ord</code> (<code>Lt</code>, <code>Eq</code>, <code>Gt</code>), since May (Alexander Bandukwala, <code>d5cd0a07a3</code>, beside <code>int_compare</code> and <code>float_compare</code>). Corrected here: our ticket had said Hazel had none, from a search of one list of builtins.</li>
<li><b>Fumola's values from JS:</b> JSON read straight into Fumola values (Adapton/fumola#148, merged), so a map passed in is no longer written out and parsed; and an answer more than about a thousand values deep no longer traps the wasm instance (Adapton/fumola#150, open). Fumola has no float comparison the rules can use yet (the game's draws are passed as whole millionths).</li>
</ul>

<h2 id="next">What next</h2>
<ol>
<li><b>The three-way script boxes</b> (<code class="ref"><b>^ticket(</b>566<b>)</b></code>): one branch with the Hazel and the Fumola rules, a JS / Hazel / Fumola chip on each room's box (JS read-only: the source of the function that runs), editable Hazel and Fumola boxes, and a master chip at the top, JS by default.</li>
<li><b>Equivalence in CI</b> (<code class="ref"><b>^ticket(</b>567<b>)</b></code>): for every handler and event, the shipped Hazel and Fumola texts answer as the JS does, on generated worlds.</li>
<li><b>A 🔬 tool for each script's overhead over JS</b> (<code class="ref"><b>^ticket(</b>568<b>)</b></code>), per handler and per engine, live in the game.</li>
<li><b>Speed standards per setting</b> (<code class="ref"><b>^ticket(</b>569<b>)</b></code>): speed runs for JS, Hazel and Fumola that hold the rooms each controls to a minimum frame rate.</li>
<li><b>The library fixes into the build the game loads:</b> 547 for real (<code class="ref"><b>^ticket(</b>558<b>)</b></code>), then 548, 551 and the fast path; until then Hazel's world ways miss the frame on big maps, and the game cannot hold the map.</li>
<li><b>Hold the map in the game:</b> call <code>with_squares</code> once a world, not the list rule every way; then the placed levers' rule with its things in maps (by place, and by id with <code>string_compare</code>).</li>
<li><b>Hazel's cost per pass</b> (<code class="ref"><b>^ticket(</b>554<b>)</b></code>, for Cyrus and Matthew): what to do about a step paying for the editor around it; it is what the map's set-up, and every loop, still pays.</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>From the work tickets of 2026-10-21 11:00 to 2026-10-23 07:00 and the reports they produced (^report(25), ^report(27), ^report(28), ^report(29)). The new measurements ran on GitHub's runners, never the laptop: library builds deployed by hazelgrove/hazel's own workflow (no compiling), timed in node 22 by drivers on orphan branches (<code>timing/553-map</code>, <code>timing/559-fastpath</code> in hazelgrove/hazel), four jobs each, the builds compared alternating on one runner, each side's better round, the median over the jobs. Every map run first checks the map rule against the shipped rule on a shuffled random world. Their rows are in <code>030/data/</code> (one folder per run, a folder per job), and are embedded in this page.</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE)
print("030/index.html", len(PAGE))
