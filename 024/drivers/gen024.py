#!/usr/bin/env python3
"""Writes 024/index.html, ^report(24): Hazel's architecture around #2651.

  python3 024/drivers/gen024.py

Then, as for every report: tools/report_refs.py, tools/link_prs.py,
tools/add_steps.py, tools/add_theme.py, and tools/report_data.py 024.
The figures are in figs.py (inline SVG, colours from the page's CSS
variables), the questions for Alexander in questions.py, the code links in
links.py (each a full commit id; gen024.py checks every range exists)."""
import html, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figs, svgkit
from links import *
from questions import QUESTIONS, FOR_CYRUS

OUT = os.path.join(os.path.dirname(HERE), "index.html")
HAZEL = os.path.expanduser("~/hazel")

FIGS = {}      # id -> number (main figures)
MINI = {}


def c(s):
    return f"<code>{s}</code>"


def fig(fid, fn, caption, n=True):
    svg = figs.ALL[fn]()
    if n:
        FIGS[fid] = len(FIGS) + 1
        label = f"<b>Figure {FIGS[fid]}.</b> "
    else:
        label = ""
    wide = ' class="figscroll"' if 'min-width' in svg else ""
    return (f'<figure class="fig" id="{fid}"><div{wide}>{svg}</div>'
            f'<figcaption>{label}{caption}</figcaption></figure>')


def mini(fid, fn, caption):
    svg = figs.ALL[fn]()
    return f'<figure class="mini" id="{fid}">{svg}<figcaption>{caption}</figcaption></figure>'


# ------------------------------------------------------------------ head and style
HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<!-- theme: head begin -->
<script>try { var t = localStorage.getItem("theme"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); } catch (e) {}</script>
<!-- theme: head end -->
<!-- nav: begin --><meta name="theme-support" content="data-theme"><script src="https://matthewhammer.org/nav/nav.js"></script><!-- nav: end -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hazel's Architecture Around #2651</title>
<meta name="description" content="How Hazel is built around #2651, a statics change that reads a module binding's elaboration back from the info map instead of analyzing the definition again: the subsystems, the representations and protocols between them, the PR drawn, what a reviewer checks, and questions for Alexander.">
<style>
  :root {
    --bg: #fbfaf7; --paper: #ffffff; --ink: #1f2328; --muted: #5b6470; --line: #e3e0d8;
    --accent: #6d28d9; --good: #15803d; --warn: #b45309; --bad: #b91c1c; --link: #1d4ed8; --accent2: #0e7490; --cx: #d6d1c6;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d;
      --accent: #c4b5fd; --good: #4ade80; --warn: #fbbf24; --bad: #f87171; --link: #93c5fd; --accent2: #67e8f9; --cx: #5d636b;
    }
  }
  :root[data-theme="dark"] { --bg: #15171a; --paper: #1d2024; --ink: #e8e6e3; --muted: #a2a9b3; --line: #33373d;
    --accent: #c4b5fd; --good: #4ade80; --warn: #fbbf24; --bad: #f87171; --link: #93c5fd; --accent2: #67e8f9; --cx: #5d636b; }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
         font: 16px/1.55 system-ui, "Segoe UI", Roboto, sans-serif; }
  main { max-width: 1020px; margin: 0 auto; padding: 32px 16px 80px; }
  h1 { font-size: 2em; line-height: 1.2; margin: 0 0 6px; }
  h2 { font-size: 1.35em; margin: 48px 0 10px; padding-top: 8px; border-top: 2px solid var(--line); }
  h3 { font-size: 1.05em; margin: 26px 0 6px; }
  p, li { max-width: 76ch; }
  .sub { color: var(--muted); margin: 0 0 24px; }
  .series { color: var(--muted); margin: 0 0 6px; font-size: 0.92em; }
  .headline { background: var(--paper); border-left: 4px solid var(--accent); padding: 10px 14px; border-radius: 6px; }
  .headline > p { margin: 6px 0; }
  ol.ans { padding-left: 1.4em; margin: 8px 0; }
  ol.ans > li { max-width: none; margin: 14px 0; }
  ol.ans > li > .row { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 16px; align-items: center; }
  ol.ans > li p { margin: 0; }
  figure.mini { margin: 0; background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; }
  figure.mini figcaption { font-size: 0.8em; margin-top: 4px; }
  @media (max-width: 760px) { ol.ans > li > .row { grid-template-columns: minmax(0, 1fr); } figure.mini { max-width: 340px; } }
  a { color: var(--link); text-decoration: underline; text-underline-offset: 2px; }
  a code { color: var(--link); }
  a.cl { text-decoration: none; } a.cl:hover code { text-decoration: underline; }
  sup.at { font-size: 0.68em; color: var(--muted); margin-left: 2px; font-weight: 600; }
  .good { color: var(--good); } .warn { color: var(--warn); } .bad { color: var(--bad); }
  figure.fig { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; margin: 18px 0; }
  .figscroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  figcaption { color: var(--muted); font-size: 0.9em; margin-top: 6px; max-width: 80ch; }
  table { border-collapse: collapse; width: 100%; font-size: 0.92em; }
  th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; }
  td.n { font-variant-numeric: tabular-nums; white-space: nowrap; }
  .scroll { overflow-x: auto; }
  code { font-size: 0.9em; background: color-mix(in srgb, var(--line) 50%, transparent); padding: 0 4px; border-radius: 4px; overflow-wrap: anywhere; }
  pre.code { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; overflow-x: auto;
             font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; margin: 6px 0 4px; }
  pre.code .rm { color: var(--bad); } pre.code .ad { color: var(--good); } pre.code .cm { color: var(--muted); }
  .codepair { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 14px; }
  @media (max-width: 760px) { .codepair { grid-template-columns: minmax(0, 1fr); } }
  .codepair h4 { margin: 6px 0 0; font-size: 0.95em; }
  .note { color: var(--muted); font-size: 0.9em; }
  .callout { background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--accent2); border-radius: 6px; padding: 8px 14px; margin: 14px 0; }
  .callout.warn { border-left-color: var(--warn); }
  section.q { background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 8px; padding: 6px 16px 10px; margin: 20px 0; }
  section.q h3 { margin: 10px 0 6px; line-height: 1.4; }
  section.q h3 .qn { color: var(--accent); margin-right: 6px; }
  .tags { margin: 2px 0 8px; }
  .tag { display: inline-block; font-size: 0.78em; font-weight: 600; padding: 1px 9px; border-radius: 999px; margin: 0 6px 4px 0; border: 1px solid; }
  .tag.ans { color: var(--good); border-color: var(--good); background: color-mix(in srgb, var(--good) 10%, transparent); }
  .tag.now { color: var(--accent2); border-color: var(--accent2); background: color-mix(in srgb, var(--accent2) 10%, transparent); }
  .tag.cyrus { color: var(--accent); border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }
  .tag.block { color: var(--warn); border-color: var(--warn); background: color-mix(in srgb, var(--warn) 12%, transparent); }
  .tag.open { color: var(--muted); border-color: var(--line); }
  .answer { background: color-mix(in srgb, var(--good) 9%, var(--paper)); border: 1px solid color-mix(in srgb, var(--good) 45%, var(--line)); border-radius: 6px; padding: 8px 12px; margin: 8px 0; max-width: 80ch; }
  .after { max-width: 80ch; }
  ul.ev { padding-left: 1.2em; } ul.ev li { margin: 5px 0; max-width: 84ch; }
  ul.ev .refs { color: var(--muted); font-size: 0.92em; }
  ol.opts li { margin: 6px 0; max-width: 82ch; }
  .optnote { display: inline-block; font-size: 0.8em; font-weight: 600; color: var(--accent); margin-left: 4px; }
  .optnote.out { color: var(--muted); text-decoration: line-through; text-decoration-thickness: 1px; }
  button.copylink { margin-left: 8px; font: 600 12px system-ui, sans-serif; padding: 1px 8px; border: 1px solid var(--line);
    border-radius: 999px; background: var(--bg); color: var(--muted); cursor: pointer; vertical-align: 2px; }
  button.copylink:hover { color: var(--ink); border-color: var(--muted); }
  button.copylink.done { color: var(--good); border-color: var(--good); }
  input.copyfield { display: block; width: 100%; max-width: 640px; margin: 4px 0; font: 13px ui-monospace, monospace;
    background: var(--paper); color: var(--ink); border: 1px solid var(--line); border-radius: 4px; padding: 3px 6px; }
  .cyrus { background: var(--paper); border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 8px; padding: 4px 16px; }
  .cyrus li { margin: 8px 0; }
  details.ev summary { cursor: pointer; color: var(--link); }
""" + svgkit.CSS + """
</style>
</head>
"""

# ------------------------------------------------------------------ top
TOP = f"""
<body>
{svgkit.MARKERS}
<main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>24<b>)</b></code> · architecture · 2026-10-21</p>
<h1>Hazel's Architecture Around #2651</h1>
<p class="sub">How is Hazel built around {pr(2651, "Statics: a module binding analyzes its definition once, not twice")}, and what does the PR change in that architecture? Matthew Hammer and Alexander Bandukwala, who owns Modules II, reviewed #2651 together on 2026-10-21, aiming to merge it that day. Matthew had tested its behaviour, and asked how Hazel is built around it: the subsystems an edit passes through, the representations they share, the protocols between them, and the PR drawn in those terms. Read at dev {commit(D)} and at the PR's head {commit(P)}.</p>

<div class="headline">
<p><b>Short answers.</b> From reading the code at those two commits; nothing here was timed or run for this report (the measurements quoted are the PR's own). Alexander's answers are his, given in the review on 2026-10-21 and relayed by Matthew.</p>
<ol class="ans">
<li><div class="row"><p><b>On dev a module binding analyzes its definition three times; #2651 makes it two, and with {pr(2603, "a let is analyzed once unless it refers to itself")} one.</b> <code>module M = def in body</code> is checked as <code>let M = def in body</code>. The let runs a recursion probe over <code>def</code> and then its real pass; the ModuleExp case then ran a third, direct pass only to get an elaboration the real pass had already recorded (<a href="#pr">the PR</a>).</p>
{mini("fig-a-passes", "a_passes", "Analyses of a module literal's definition per binding.")}</div></li>
<li><div class="row"><p><b>The architectural change is small and specific: one case of the statics walk now takes another's result from the info map.</b> Statics keeps one record per expression id, the last write winning, and every case writes its node's record, elaboration included. #2651 reads <code>elab_term</code> at the definition's id instead of computing it again, the kind of read-back statics already does elsewhere (<a href="#statics">statics</a>).</p>
{mini("fig-a-infomap", "a_infomap", "The let writes; the ModuleExp case reads back.")}</div></li>
<li><div class="row"><p><b>Nesting multiplies: the innermost definition was analyzed 3<sup>depth</sup> times on dev; it is 2<sup>depth</sup> with #2651, and once with #2603 as well.</b> This holds where a <code>module … in</code> sits inside another binding's definition; a <code>module</code> item inside braces is a plain let, and only #2603 changes it (<a href="#cost">the cost</a>).</p>
{mini("fig-a-nesting", "a_nesting", "Analyses of the innermost definition, by depth.")}</div></li>
<li><div class="row"><p><b>One result changes, and Alexander confirmed it is a fix.</b> <code>module M : {{ let x : Int }} = {{ let x = 1; let y = 2 }} in M.x</code>, a type error that still runs, gave the module's raw source on dev and gives 1 with #2651: dev's result was a bug in the auto-labelling of one-member tuples. The same corner with a plain value, <code>= 5</code>, gives 5 on dev and by our reading gets stuck with #2651; Alexander expects that binding to be a static error, a question for Cyrus (<a href="#lift">the corner</a>).</p>
{mini("fig-a-lift", "a_lift", "M.x before and after, for the extra-member module.")}</div></li>
<li><div class="row"><p><b>A definition that names its own module is still an error, through a guard on the let's fixpoint; Alexander suggests a cleaner signal.</b> When the let wrapped the definition in a fixpoint, #2651 analyzes it directly, as dev did, and reports the name as unbound. Alexander's suggestion: tell the let analysis not to try the recursive case for a module binding; the guard, the fallback and the recursion probe then all go away (<a href="#guard">the guard</a>).</p>
{mini("fig-a-guard", "a_guard", "The second commit's guard.")}</div></li>
<li><div class="row"><p><b>#2651 merges cleanly into today's dev and with #2603; against Modules II it conflicts on one line, in parts 2 to 9.</b> The resolution keeps the read-back and adds <code>~coercible=true</code> to the fallback. Whether to merge ahead of Modules II is the one open question that should be settled before merging (<a href="#q-merge-order-with-modules-ii">question 2</a>).</p>
{mini("fig-a-merge", "a_merge", "Three-way merges, run read-only on 2026-10-21.")}</div></li>
<li><div class="row"><p><b>Of five questions for Alexander, two were answered in today's review and three are open; three design questions go to Cyrus.</b> None of the answers holds up the merge. From here on Alexander gives his feedback as comments on {pr(2651)} itself, so the open questions go there (<a href="#questions-for-alexander">questions</a>).</p>
{mini("fig-a-questions", "a_questions", "The questions and where they stand.")}</div></li>
</ol>
</div>
"""

# ------------------------------------------------------------------ 1. subsystems
SUBSYSTEMS = f"""
<h2 id="subsystems">The subsystems, and what flows between them</h2>
<p>Hazel is a structure editor: the program is always a tree of tiles, and every edit leaves a program that can be typed and run. An edit passes through five subsystems in a fixed order, all on the page's main thread except evaluation ([[fig-subsystems]]).</p>
<ul>
<li><b>The editor.</b> The program is a <i>segment</i>: a list of pieces (tiles, grout, whitespace, projectors), where each tile has an id and child segments ({d(BASE, 3, 28)}). The <i>zipper</i> is the caret's place in that tree ({d(ZB, 13, 20)}). A key press becomes an <code>Action</code>, wrapped as <code>Perform</code> ({d(CE, 343)}), and <code>Perform.go</code> edits the zipper, consulting the <em>previous</em> statics as it does ({d(ED, 146, 184)}).</li>
<li><b>MakeTerm.</b> Turns tiles into a term, <code>Exp.t</code>, and gives each term node the ids of the tiles that make it up ({d(MT, 290, 306)}). For statics it first fills in the pieces missing from the visible segment, its canonical completion ({d(MT, 1997, 2013)}).</li>
<li><b>Statics.</b> One recursive walk over the whole term, from an empty map ({d(S, 4350, 4381)}), that types and elaborates at once. It returns the <i>info map</i>, one record per expression id, and the elaborated program. It runs on the main thread, 225 ms after typing stops, or at once after a projector's commit ({d(CWS, 93, 141)}).</li>
<li><b>Evaluation.</b> The elaborated program goes to the eval worker by <code>postMessage</code>, with a slice of the info map (EvalInfo) and the previous run's cache ({d(ER, 250, 293)}). The worker evaluates in slices and reuses earlier results, keyed by expression id.</li>
<li><b>Results back.</b> The worker's messages come back as actions: values, probe samples and test results. The page updates its model, recalculates without running statics again, and redraws, error marks included.</li>
</ul>
{fig("fig-subsystems", "subsystems", "The five subsystems an edit passes through, on dev at 962a7cb009, and the eight places that read the info map, with the fields each reads. The ModuleExp case is a reader only with #2651.")}
<p>Every reader looks a record up by id. So whichever analysis writes a node's record <em>last</em> decides what the cursor inspector, the error marks, completion, projectors, probes and the worker's reuse check all see ({d(SB, 10, 11)}: <code>add_info</code> is a plain <code>Id.Map.add</code>). That is what gives #2651 its architectural side: it changes which analysis writes last inside a module's definition (<a href="#pr">the PR</a>).</p>
<p class="note">On dev statics is one walk of the whole program per refresh. Andrew Blinn's {pr(2469, "Modular editors")}, not yet on dev, adds DefStatics: statics per top-level definition, with the context passed from one to the next, so that an edit re-analyzes the edited definition and those that read a name it changed ({at(ME, DEFS, 3, 10)}). Inside one definition the walk is the same, so #2651 applies under both.</p>
"""

# ------------------------------------------------------------------ 2. representations
REPS = [
    ("Segment, piece, tile", d(BASE, 3, 28), "the editor's source: tiles with ids and child segments, grout, whitespace, projectors",
     c("Perform.go") + " edits", "MakeTerm (both parses), the layout, printing"),
    ("Zipper", d(ZB, 13, 20), "the caret's place in the segment: selection, relatives, caret, probes",
     c("Perform.go") + " " + d(ED, 173, 174), "CachedStatics (probe ids, the parse), the syntax cache, " + c("Indicated.ci_of") + " " + d(IND, 228, 236)),
    ("Editor model", d(ED, 13, 32), "root sort, the zipper, and the syntax cache (layout, projector shapes)",
     c("Editor.Update.update") + " and " + c("calculate"), "the code views"),
    ("Exp.t", d(IDT, 165, 185), "one tree for user terms and elaborated terms (" + c("DHExp") + " includes " + c("Exp") + ", " + d(DH, 11) + "); its first id is its rep id",
     "MakeTerm " + d(MT, 290, 306) + "; statics' elaboration", "statics, the evaluator, projectors"),
    ("Info map", d(SB, 4, 11), c("Id.Map") + " from id to Info; the last write wins",
     c("add") + " in the walk " + d(S, 204, 269), "the eight readers of " + "[[fig-subsystems]]"),
    ("Info.exp", d(INFO, 35, 53), "one expression's statics: context, expected type, type, marks, co-context, elaboration",
     c("add") + "; the lift " + d(S, 356, 357) + "; the FixF patch " + d(S, 2216, 2228), "the readers above; " + c("elab_term") + " also the ModuleExp case, with #2651 " + p(S, 2775, 2780)),
    ("Ctx", d(CTX, 37, 57), "variables, constructors, type aliases and livelits in scope, newest first",
     "binders: patterns, " + c("TyAlias") + ", the module alias " + d(S, 2124, 2151), "variable lookup " + d(S, 691, 705) + ", completion " + d(TYDI, 192, 201)),
    ("CoCtx", d(CO, 30, 53), "each free variable's uses, with the type each use expects",
     "variables; " + c("union") + " and " + c("mk") + " at binders", "unused-variable warnings, " + c("requires_fixf") + " " + d(S, 2172, 2181) + ", probe targets " + d(SB, 46, 53)),
    ("CachedStatics", d(CS, 4, 13), "term, elaborated program, info map, error and warning ids, probe targets",
     c("CachedStatics.init") + " " + d(CS, 188, 226), "the editor, " + c("EvalResult") + ", " + c("Perform.go")),
    ("EvalInfo", d(EI, 18, 29), "for each expression id: its elaboration, co-context and probe targets",
     c("of_info_map") + " " + d(EI, 56, 74), "the worker's reuse check " + d(IE, 313, 353)),
    ("Worker request and messages", d(WS, 7, 89), c("{expr, eval_info_map, prev}") + "; Ack, ReusePlan, Stream, Result",
     c("EvalResult.calculate") + " " + d(ER, 270, 293), "the worker; the page through " + d(REQ, 6, 41)),
    ("Dynamics", d(DYN, 50, 55), "probe samples, test results and theorems, by id",
     "the worker's evaluator state", "probe views, the test panel, the syntax cache"),
]


def reps_table():
    rows = "\n".join(f"<tr><td><b>{n}</b></td><td>{w}</td><td>{what}</td><td>{mk}</td><td>{rd}</td></tr>"
                     for n, w, what, mk, rd in REPS)
    return ('<div class="scroll"><table id="reps">\n<tr><th>Representation</th><th>Defined at (dev)</th><th>What it holds</th>'
            '<th>Made by</th><th>Read by</th></tr>\n' + rows + "\n</table></div>")


REPRESENTATIONS = f"""
<h2 id="representations">The representations they share</h2>
<p>The subsystems pass five things along: the segment, the term, the info map, the elaborated program and EvalInfo. What ties them together is the id. MakeTerm gives a term node its tile's id, statics files the node's record under that id, EvalInfo keeps the node's elaboration under it, and the worker keys its probe samples and cached results by it ([[fig-ids]]). A term made inside statics can carry an id it borrows: the ModuleExp case builds its <code>let</code> with the ModuleExp's own id ({d(IDT, 175, 183)}, used at {d(S, 2737, 2741)}), so that let's record lands where the binding's would.</p>
{fig("fig-ids", "ids", "One id, a1, across five representations: the tile, the term node, its Info, its EvalInfo entry, and what the worker records for it. Each consumer meets the others at the id.")}
{reps_table()}
<p class="note">Each row's links point to dev at 962a7cb009, except the read-back, which is at #2651's head (marked PR). User terms and elaborated terms share one type, so an elaboration is an ordinary <code>Exp.t</code> whose ids mostly match the source.</p>
"""

# ------------------------------------------------------------------ 3. protocols
PROTOCOLS = f"""
<h2 id="protocols">An edit's round trip, and the worker's messages</h2>
<p>[[fig-roundtrip]] follows one key press. Every action goes through an <i>update</i> phase and then a <i>calculate</i> phase ({d(MAIN, 73, 110)}):</p>
<ol>
<li>The key becomes an action, <code>Perform(Insert(c))</code> ({d(CE, 343)}), and <code>Editor.Update.update</code> runs <code>Perform.go</code> on the zipper with the statics of the previous refresh ({d(ED, 146, 184)}).</li>
<li>The calculate phase asks the debounce whether to run statics. While typing it says <i>Defer</i> and starts a 225 ms timer; when the timer fires it dispatches a refresh that says <i>Force</i> ({d(CWS, 104, 140)}). Statics runs on Force, on an edit that is not deferred, or when the set of probes changed ({d(CWS, 200, 204)}).</li>
<li><code>CachedStatics.init</code> parses the zipper for statics, runs <code>Statics.mk</code> over the whole term, and derives the error ids, warning ids and probe targets ({d(CS, 188, 226)}, {d(CS, 99, 135)}). The time it takes shows in the debug sidebar's Statics timer ({d(CWS, 188)}).</li>
<li><code>Editor.Update.calculate</code> refreshes the completion buffer from the record at the caret, the syntax cache and the probes ({d(ED, 186, 230)}).</li>
<li><code>EvalResult.calculate</code> compares the new elaborated program with the last one, ignoring ids. If it changed, it projects the info map to EvalInfo and queues a request for the worker ({d(ER, 250, 293)}).</li>
<li>The worker answers with messages, [[fig-worker]]; each comes back as an action, which updates the result and recalculates without running statics again.</li>
</ol>
{fig("fig-roundtrip", "roundtrip", "One edit's round trip on dev, as a sequence of calls between the parts of the main thread and the eval worker. Notes on a lifeline are work done there. Statics runs once per refresh, after the debounce, not on every key while typing.")}
<p>The worker's protocol is in {d(WS, 7, 89)}. A request carries, for each editor, the elaborated program, the EvalInfo slice and the previous run's incremental cache, Marshal-encoded. The worker posts an <code>Ack</code> at once; then a <code>ReusePlan</code>, its prediction of what it can reuse, for programs with at least 2,500 EvalInfo entries ({d(WS, 294, 304)}); then a <code>Stream</code> message after each slice of 5,000 steps ({d(WS, 271)}); and last a <code>Result</code>. The page restarts a worker that has not acked in 5 s (15 s from a cold start), up to three times, and gives up on a request after 20 s ({d(WC, 5, 11)}). Its callbacks become result actions ({d(REQ, 6, 41)}).</p>
{fig("fig-worker", "worker", "The eval worker's messages on dev, as a sequence diagram: the page's actions for each message on the left, the worker's scheduling on the right, and the page's timeouts at the bottom.")}
<p>Reuse is where statics and the worker meet. At each expression, the worker's reuse check compares the elaboration EvalInfo recorded at that id with the one the cached result was computed from, then the provenance of the free variables in the record's co-context, then the probe targets ({d(IE, 313, 353)}). So what statics writes at an id matters to the worker as much as to the editor: the same last write is what both see.</p>
"""

# ------------------------------------------------------------------ 4. statics
STATICS = f"""
<h2 id="statics">Inside statics</h2>
<h3 id="walk">The walk</h3>
<p>Statics is one function, <code>uexp_to_info_map</code>, called on every expression ({d(S, 191, 201)}). It takes the context (what is in scope), the expected type, the term and the map, and returns the term's record, its elaboration and the new map. Each case analyzes the children it needs, passing context and expected type down and getting records and elaborations back, and ends by calling <code>add</code> ({d(S, 204, 269)}). <code>add</code> works out the error marks, the inspector's message and the fixed type, builds the record, writes it at every id of the term, and returns the same elaboration it wrote ({d(S, 268)}). So the walk has two outputs at once: the map, and the root's elaboration, which <code>Statics.mk</code> returns for the evaluator ({d(S, 4350, 4381)}).</p>
{fig("fig-walk", "walk", "The statics walk on dev, for a let. What goes down (context, expected type) is solid; what comes up (record, elaboration, map) is dashed. Every case ends in add, which writes the record and returns the elaboration it wrote.")}
<p>Two more facts about the map matter for #2651. Some passes throw their map away: probes such as the let's recursion probe ({d(S, 2070)}) analyze a whole subterm and keep only its type. And statics already reads its own map back in the middle of the walk: the let's fixpoint patch ({d(S, 2216, 2228)}), the ModuleExp case's class override ({d(S, 2743, 2756)}), and a module's type, built from the records of its exported patterns ({d(MH, 413, 439)}). #2651 adds one more read of the same kind.</p>

<h3 id="info">One record: mode and self, context in, co-context out</h3>
{fig("fig-info", "info", "The fields of Info.exp at dev, grouped by colour: context in, mode, self, co-context out, and the terms. The elaboration, elab_term, is the field #2651 reads back.")}
<p>Hazel's statics has long been described in terms of a <i>mode</i> (analyze against a type, or synthesize one) and a <i>self</i> (what a term gives, errors included), and both used to be types of their own; Matt Keenan removed them ({commit("d22a778d6494f7798bfcf1c907c049d572fd976f")}, Mode, 2025; {commit("ae3f3edde3e049bec563ac2831ba8ce0ea750101")}, Self, 2026). Today the mode is just the expected type, <code>ana</code>: <code>Unknown(SynSwitch)</code> means synthesize ({d(SB, 263)}). The self is the synthesized type, <code>elab_syn_ty</code>, with the marks and message <code>add</code> computes, and <code>ty</code> is their meet with the expected type ({d(SB, 268, 277)}).</p>
<p>The context goes down: a list of entries, newest first ({d(CTX, 37, 57)}). A variable looks itself up there and reports itself unbound if it is missing ({d(S, 691, 705)}). The <i>co-context</i> goes up: each free variable with the ids of its uses ({d(CO, 30, 53)}). A binder takes its own names out ({d(CO, 43, 53)}), which is how unused variables are found, how a let decides it needs a fixpoint, and how a probe knows which bindings to capture ({d(SB, 46, 53)}).</p>

<h3 id="elaboration">Elaboration inside statics</h3>
<p>There is no separate elaborator. Matt Keenan's {commit("cc620bbbdc4bddd93e4c61e2ff6116d7c4c5dbb4", "cc620bbbdc")} ("delete elaborator", committed 2026-04-17) folded it into statics: each case builds its node's elaboration from its children's, and <code>add</code> records it. One detail of that port is the subject of #2651. The old elaborator elaborated a module binding's definition by reading the info map, with no second analysis ({at(OLD, ELAB, 518, 524)}); the port turned that into a second call to the walk, <code>def_elab_direct</code> ({d(S, 2757, 2762)}). #2651 returns to reading the map.</p>

<h3 id="let">How a let is analyzed</h3>
{fig("fig-let", "let", "The Let case at dev, pass by pass: dashed passes throw their map away; solid ones write the info map. Right: the analyses of the definition this costs, on dev and with #2603.")}
<p>A let analyzes its definition more than once ({d(S, 2023, 2248)}). It first types its pattern, then runs a <i>recursion probe</i>: a full analysis of the definition in the pattern's context, map thrown away ({d(S, 2070)}). Whether the let is recursive is decided by shape alone: one bound variable and one function of arrow-like type ({d(S, 2024, 2039)}, {d(S, 2076)}). If not, one real pass analyzes the definition in the outer context ({d(S, 2079)}). If so, two more passes are thrown away and a final one runs with the name in scope ({d(S, 2090, 2122)}). The body follows, then the pattern again with the body's co-context, for unused-variable warnings ({d(S, 2152, 2155)}). Last, the let builds its elaboration: the definition aligned to the pattern's labels and given the function's name, or, when the definition uses its own name, wrapped in a fixpoint, <code>FixF</code> ({d(S, 2172, 2230)}).</p>
<p>So on dev every let analyzes a definition that is not a function twice, and a function four times, and these multiply with nesting. {pr(2603, "a let is analyzed once unless it refers to itself")}, open, skips the probe for a definition that is not a function, and keeps the probe as the final analysis for a function that neither uses nor shadows its own name ({at(T2603, S, 2070, 2089)}, {at(T2603, S, 2113, 2162)}).</p>
"""

# ------------------------------------------------------------------ 5. modules
MODULES = f"""
<h2 id="modules">Modules: a module binding is a let</h2>
<p>On dev a module is "a syntactic gloss over labeled tuples" ({d(DOC, 5)}). A module literal <code>{{ … }}</code> is lowered to a chain of lets and type aliases ending in a labeled tuple of its exported names ({d(MH, 286, 337)}, {d(MH, 162, 171)}) and analyzed as that ({d(S, 2693, 2724)}). A signature is a type that <code>desugar_sig</code> turns into a labeled product, dropping its type items ({d(TYP, 615, 657)}). Andrew Blinn built this module system and the <code>module</code> keyword in February 2026 ({commit("b0735de6d65f61b238ea74989b257d2017e0c866")} to {commit("131f508825bf204e5d174169fe4085403f6d5f11", "131f508825")}).</p>

<h3 id="moduleexp">module M = def in body, step by step</h3>
<p><code>module M = def in body</code> is a ModuleExp, and it has no typing rule of its own. Its case on dev ({d(S, 2725, 2772)}) does seven things, [[fig-module-steps]]:</p>
<ol>
<li>Records the name's cursor info, an <code>InfoMPat</code> ({d(S, 2728, 2735)}).</li>
<li>Turns the name pattern into an ordinary pattern, desugaring a signature annotation to a labeled product ({d(MH, 51, 60)}).</li>
<li>Builds <code>Let(pat, def, body)</code> and gives it the ModuleExp's own id ({d(S, 2736, 2741)}).</li>
<li>Analyzes that let ({d(S, 2742)}): the probe and real pass over <code>def</code>, the body, and the pattern, whose record overwrites the name's <code>InfoMPat</code>.</li>
<li>Changes the class in the let's record to ModuleExp ({d(S, 2743, 2756)}), which step 7 overwrites anyway.</li>
<li>Analyzes <code>def</code> again, directly, against the signature or nothing, to get <code>def_elab_direct</code> ({d(S, 2757, 2762)}). This pass's records overwrite the let's for every node inside <code>def</code>.</li>
<li>Builds the binding's elaboration with <code>moduleexp_elab</code> and adds the ModuleExp's record ({d(S, 2763, 2772)}).</li>
</ol>
{fig("fig-module-steps", "module_steps", "The ModuleExp case's steps at dev, and which ids each writes in the info map. Step 6 is the one #2651 replaces with a lookup.")}

<h3 id="swap">What moduleexp_elab builds, and what it drops</h3>
<p><code>moduleexp_elab</code> takes the let's elaboration and swaps its definition for <code>def_elab_direct</code>, and strips the signature from the pattern ({d(MH, 447, 456)}, {d(MH, 364, 371)}). That drops everything the let put around the definition: the label alignment, the function's name ({d(EXP, 544, 551)}) and a fixpoint. The alignment is the one that matters on dev. Against a one-member signature, alignment would wrap a module's let-chain as <code>(x = whole module)</code> ({d(LTH, 49, 75)}), and dev's test <code>module M : {{ let x : Int }} = {{ let x = 42 }} in M.x</code> gives 42 only because of the swap ({d(TEM, 123, 129)}). Stripping the signature means a module is not sealed at run time on dev: its value keeps every member.</p>
{fig("fig-moduleexp-elab", "moduleexp_elab", "Left, the let's elaboration of a module binding at dev; right, what moduleexp_elab makes of it. The four things it drops are below.")}

<h3 id="members">How members enter the context</h3>
<p>The name enters the body's context twice ([[fig-members]]). As a value, the pattern binds a variable whose type is the module's labeled product ({d(S, 3164, 3193)}). As a type, the let adds an alias under the module's name for its type members ({d(S, 2124, 2151)}). A capitalized <code>M</code> parses as a constructor, and the Constructor case turns it into the variable when a variable is its newest binding ({d(S, 1561, 1597)}). <code>M.x</code> is then a labeled-tuple projection ({d(S, 1278, 1420)}; at run time {d(TR, 1024, 1058)}), and <code>M.T</code> a type projection through the alias ({d(TYP, 481, 500)}).</p>
{fig("fig-members", "members", "A module's members at dev: the body is lowered to a type alias and let chain ending in a labeled tuple; the binding adds a variable and a type alias to the context; member access is projection.")}

<h3 id="modules-ii">Modules II</h3>
<p>Alexander Bandukwala's Modules II stack replaces "modules are labeled tuples" with modules of their own: {pr(2493, "part 1: first-class signature types and module values")}, {pr(2494, "part 2: sealing at explicit coercion sites")} and {pr(2495, "part 3: abstract type members, sealing, path types")}, then parts 4 to 9, {pr(2498)}, {pr(2500)}, {pr(2501)}, {pr(2503)}, {pr(2508)} and {pr(2510)}, the last of them the standard library as modules. A signature stays a signature type, a module literal elaborates to a module value, and a binder's signature seals the value at run time. Two things on his stack touch #2651's code. Parts 2 to 9 keep the direct pass, now with <code>~coercible=true</code> ({at(M2, S, 2833, 2834)}, {at(M9, S, 2973, 2974)}), and their <code>moduleexp_elab</code> keeps the signature, because it is what seals ({at(M2, MH, 617, 627)}). His docs already say a module binding "elaborates to that Let" ({at(M9, DOC, 496, 497)}). Questions <a href="#q-merge-order-with-modules-ii">2</a> and <a href="#q-def-elab-direct-on-modules-ii">4</a> ask what that means for #2651.</p>
"""

# ------------------------------------------------------------------ 6. the PR
BEFORE = """<span class="cm">(* Statics.re:2757-2762 at dev *)</span>
let def_ana =
  switch (pat.term) {
  | Asc(_, typ) => typ
  | _ => syn
  };
<span class="rm">let (_, def_elab_direct, m) = go(~ana=def_ana, def, m);</span>"""
AFTER = """<span class="cm">(* Statics.re:2770-2789 at 29c08fd8fa, comments cut *)</span>
<span class="ad">let names_itself =
  switch (expanded_elab.term) {
  | Let(_, {term: FixF(_), _}, _) =&gt; true
  | _ =&gt; false
  };
let (def_elab_direct, m) =
  switch (Id.Map.find_opt(Exp.rep_id(def), m)) {
  | Some(Info.InfoExp({elab_term, _})) when !names_itself =&gt;
    (elab_term, m)</span>
  | _ =&gt;
    let def_ana = ... ;                <span class="cm">(* as on dev *)</span>
    let (_, elab, m) = go(~ana=def_ana, def, m);
    (elab, m);
  };"""

COUNTS = [("a module literal, <code>module M = { … } in body</code>", 3, 2, 2, 1,
           "probe " + d(S, 2070) + ", real " + d(S, 2079) + ", direct " + d(S, 2762)),
          ("a function that does not name the module, <code>module F = fun x -&gt; x + 1 in F(2)</code>", 5, 4, 2, 1,
           "probe, two dropped and a final pass " + d(S, 2090, 2122) + ", direct"),
          ("a function that names it, <code>module F = fun x -&gt; F(x) in 1</code>", 5, 5, 4, 4,
           "as above; #2651 falls back " + p(S, 2781, 2788) + "; #2603 reuses the probe as the first dropped pass " + at(T2603, S, 2135, 2139))]


def counts_table():
    rows = "\n".join(f"<tr><td>{a}</td><td class=\"n\">{b}</td><td class=\"n\">{c_}</td><td class=\"n\">{d_}</td>"
                     f"<td class=\"n\">{e}</td><td>{f}</td></tr>" for a, b, c_, d_, e, f in COUNTS)
    return ('<div class="scroll"><table id="counts">\n<tr><th>Definition</th><th>dev</th><th>#2651</th><th>#2603 alone</th>'
            '<th>both</th><th>Where the passes are</th></tr>\n' + rows + "\n</table></div>")


PR_SECTION = f"""
<h2 id="pr">The pull request, drawn</h2>
<p>{pr(2651)} is two commits by Matthew Hammer, +55 and &minus;5 lines in three files: {commit(E1)} reads the definition's elaboration back, and {commit(P)} brings back the error for a definition that names its own module and adds two tests. It is part of {issue(2609, "Performance Challenges (Fall 2026)")}, finding 7, statics re-analyzing whole subterms, the same kind of problem as #2603.</p>
<p>The idea in one sentence: the let already recorded the definition's elaboration at the definition's id, before wrapping it, so the ModuleExp case can look it up instead of analyzing the whole definition again ([[fig-pr-flow]]). The lookup is safe because the map is passed along explicitly and started empty for this run ({d(S, 4354, 4362)}), and because passes that throw their map away never reach it: the record found is the one the let's real pass wrote in this very call.</p>
{fig("fig-pr-flow", "pr_flow", "The ModuleExp case before (dev at 962a7cb009) and after (#2651 at 29c08fd8fa). Both share the let's analysis; before, a direct pass overwrites the definition's records; after, they are read back, and the direct pass runs only as the fallback. Below, the writes at the definition's ids in order.")}

<h3 id="code">The code, before and after</h3>
<div class="codepair">
<div><h4>Before, at dev: {d(S, 2757, 2762)}</h4><pre class="code">{BEFORE}</pre></div>
<div><h4>After, at #2651: {p(S, 2770, 2789)}</h4><pre class="code">{AFTER}</pre></div>
</div>
<p>Both feed the same call, <code>ModuleHelpers.moduleexp_elab(~def_elab_direct, expanded_elab)</code> ({d(S, 2763, 2764)}; {p(S, 2790, 2791)}). The PR's comment says the read-back works because "add records exactly the elab_term it returns" ({p(S, 2757, 2763)}). That is true of <code>add</code> ({d(S, 268)}) but not of one path of the walk, the one-member-signature lift (<a href="#lift">below</a>).</p>

<h3 id="guard">The second commit: a definition that names its own module</h3>
{fig("fig-selfnaming", "selfnaming", "How module F = fun x -> F(x) in 1 is handled: the let analyzes it recursively and records no error; the first commit read that back and lost dev's error; the second sees the let's fixpoint and runs the direct pass, which reports F, as dev did. Right: Alexander's suggested follow-up.")}
<p>The first commit lost an error. <code>module F = fun x -&gt; F(x) in 1</code> is one variable bound to one function, so the let takes its recursive path and analyzes the definition with F in scope: no error. On dev the direct pass then analyzed it again in the outer context, where F is not a variable, and marked it a free constructor ({d(S, 1598, 1606)}, {d(CSH, 61, 64)}), overwriting the let's records. With the read-back, nothing overwrote them, so the error was gone; the correctness review in {rep(21, "#pr-2651")} found it by running both commits.</p>
<p>{commit(P)} adds <code>names_itself</code>: if the let's elaboration is <code>Let(_, FixF(_), _)</code>, the let saw the definition use its own name, and the direct pass runs as before ({p(S, 2764, 2774)}). The fixpoint is the signal because the let removes the name from the co-context of the definition's record ({d(S, 2216, 2228)}), so the record itself cannot show the self-reference. A test pins the error ({p(TSM, 406, 413)}).</p>

<h3 id="cost">What it costs, by shape and by nesting</h3>
{fig("fig-passes", "passes", "Full analyses of a module binding's definition at dev, with #2651, with #2603 alone, and with both, for three kinds of definition, counting the let's recursion probe. Counted from the code, not measured.")}
{counts_table()}
<p>So on today's dev #2651 takes a module literal's definition from three analyses to two; the third is the let's recursion probe, which #2603 removes. The PR's title, "once, not twice", counts only the ModuleExp case's own extra pass; it is exact for the whole binding once both PRs are in. Inside the definition, every member is itself a let and pays the let's own count again.</p>
{fig("fig-nesting", "nesting", "Analyses of the innermost definition when module bindings sit inside each other's definitions, on a log scale: each level multiplies by 3 on dev, 2 with #2651 or with #2603 alone, and 1 with both. Counted from the code.")}
<p>Nesting multiplies, but only one kind of nesting goes through this case. A <code>module … in</code> inside another module binding's definition pays the binding's factor at every level: 3<sup>depth</sup> analyses of the innermost definition on dev, 2<sup>depth</sup> with #2651, one with #2603 as well. A <code>module Inner = {{ … }}</code> item inside braces is lowered to a plain let ({d(MH, 300, 304)}), so it pays only the let's factor, 2 per level on dev, which #2603 removes and #2651 does not touch. Dev's only module program, <code>docs/reference/modules.hz</code>, nests by items.</p>
<p><b>Measured, by the PR (not in this report).</b> On dev the effect is within the noise: on an 800-function module made up for timing, statics was about 0.13 s of 6 s, and whole-command times overlapped (6.06 and 6.74 s before, 5.26 and 6.05 s after, two runs each). On the livelits branch {pr(2635, "livelits × modular editors")}, where a module holds the livelit definitions, a profile of the <i>Shirt and Pants</i> slide put 1.79 s of its 4.2 s of statics in the second pass, and the command line's statics went from 6.7 s to 4.3 s, against 4.1 s for the same slide with the module flattened into top-level lets (two runs each, within 0.3 s; {issue(2609)}, finding 7). That branch also carries #2603's change (as {commit('b9e756132324ef60d51499976debd9a4c54696de')}) and per-definition statics, so these are not dev's numbers. {rep(17, "#pr2651")} and {rep(1, "#issues")} list these numbers too.</p>
"""

# ------------------------------------------------------------------ 7. review
REVIEW_ROWS = [
    ("Is the read-back the same as the direct pass?",
     "Yes, in the let's non-recursive branch, with one exception. There the let's real pass and dev's direct pass get "
     "the same context (the ModuleExp's), the same expected type (" + c("p_syn.ty") + " is the signature already "
     "desugared by " + c("mpat_to_pat") + ", met with " + c("syn") + "; " + c("desugar_sig") + " ignores its context and "
     "changes nothing the second time), the same term and the same flags; only the ancestors list differs. And the "
     "elaboration recorded is the one returned on every path that ends in " + c("add") + ". The exception is the lift (next row).",
     d(S, 2079) + ", " + d(S, 2757, 2762) + ", " + d(MH, 51, 60) + ", " + d(TYP, 615, 657) + ", " + d(SB, 268, 277) + ", " + d(S, 268)),
    ("Where does it not hold?",
     "Under a one-member signature the definition is lifted: " + c("autolabel_singleton_tuple") + " records the bare "
     "analysis but returns " + c("(x = raw source)") + ". The extra-member module now gives " + c("M.x = 1") + " (dev: its "
     "raw source; confirmed by running in ^report(21)); Alexander confirmed 1 is right. A plain value under that "
     "signature gives 5 on dev and, traced, gets stuck with #2651 (<a href=\"#lift\">below</a>).",
     d(S, 310, 358) + ", " + d(S, 2778, 2791) + ", " + p(TEM, 86, 96)),
    ("A tuple literal under a product signature",
     "The let rearranges a tuple definition to the pattern's labels before analyzing it, so the read-back is the "
     "rearranged tuple's elaboration where dev's direct pass analyzed the original. The tuple case rearranges its own "
     "elaboration the same way, so the result should match; a test would settle it.",
     d(S, 2054, 2069) + ", " + d(S, 1117, 1132)),
    ("What does the editor see inside the definition now?",
     "The let's records, not the direct pass's. Two differences, neither in the elaboration: the ancestors list has the "
     "ModuleExp's id twice, as the body's already did (auto-probes drop adjacent repeats); and inside a function-valued "
     "module that does not name itself, the recorded context contains the module's own name, so completion can offer "
     "F inside F, where using it is an error. Dev never showed F there. Alexander's flag (question 3) would remove it.",
     d(S, 270) + ", " + d(S, 2737, 2741) + ", " + d(APP, 81, 93) + ", " + d(S, 2090, 2122) + ", " + d(TYDI, 28, 39)),
    ("Can the fallback be reached?",
     "The self-naming arm, yes: that is the second commit's case. The 'no record found' arm looks unreachable: every "
     "analysis ends in " + c("add") + " at the term's ids, and the map starts empty each run. It is defensive. Codecov's "
     "one missed patch line is the fallback's signature arm, " + c("Asc(_, typ) =&gt; typ") + ", reached only by a "
     "self-naming module with a signature.",
     p(S, 2781, 2788) + ", " + p(S, 2784) + ", " + d(S, 4354, 4362)),
    ("Is the self-naming signal robust?",
     "It reads the shape of the let's elaboration. If the let ever wraps its fixpoint differently, the check turns "
     "false silently and the error goes away again; only the one test would notice. A flag that tells the let not to "
     "try the recursive case (Alexander's suggestion, question 3) would not depend on the shape at all.",
     p(S, 2770, 2774) + ", " + d(S, 2188, 2230)),
    ("The worker's view",
     "Unchanged in the common case, and more consistent: the record at the definition's id and the elaboration spliced "
     "into the program are now the same value. The guard matters here too: without it, a self-naming definition's "
     "record would keep the let's patched co-context, which lacks the module's name, beside an elaboration that "
     "uses it, so the reuse check would not see changes to that name.",
     d(IE, 326, 341) + ", " + d(S, 2207, 2228)),
    ("How strong are the tests?",
     "The statics test passes on any static error anywhere in the program, so it does not pin where the error is or "
     "what kind. Untested: a function-valued module that does not name itself (" + c("module F = fun x -&gt; x + 1 in F(2)") +
     ", 3), the bare value under a one-member signature, and the fallback's signature arm. Evaluator tests run without "
     "EvalInfo or a previous run, so they never exercise reuse.",
     p(TSM, 406, 413) + ", " + p(TSP, 225, 242) + ", " + p(TEP, 24, 27) + ", " + p(TEP, 126, 140)),
    ("Is it ready to merge?",
     "Into dev, yes: 19 commits behind, and merges cleanly; dev's only change under " + c("src/language") + " since the "
     "base is " + c("Ascriptions.re") + " (" + pr(2679, "an ascription pushed through a value gives the value back") + "). "
     "CI was green at 29c08fd8fa (Fast checks, Full tests, codecov). No reviews or comments yet but codecov's. It merges "
     "cleanly with #2603's head too. Against Modules II, one line conflicts in parts 2 to 9 (question 2).",
     "<code>git merge-tree</code>, GitHub's checks (2026-10-21)"),
    ("Pre-existing, not this PR",
     "The class override at the ModuleExp's id is overwritten by the final " + c("add") + "; " + c("docs/modules.md") +
     " still describes the deleted Elaborator; and the lift returns raw source, so any term needing elaboration under a "
     "one-member labeled product reaches the evaluator unelaborated (dev's extra-member result is one case).",
     d(S, 2743, 2756) + ", " + d(S, 2765) + ", " + d(DOC, 261, 264) + ", " + d(S, 329, 334)),
]


def review_table():
    rows = "\n".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c_}</td></tr>" for a, b, c_ in REVIEW_ROWS)
    return ('<div class="scroll"><table id="checks">\n<tr><th>What a reviewer checks</th><th>What the reading found</th>'
            '<th>Where</th></tr>\n' + rows + "\n</table></div>")


REVIEW = f"""
<h2 id="review">What a reviewer checks</h2>
<p>Matthew has tested #2651's behaviour; what a review adds is the argument for why the result is the same, and where it is not. The table gives each check, what reading the code found, and where. The earlier reviews of this PR are {rep(17, "#pr2651")} (merge plan: wave 1, small and independent) and {rep(21, "#pr-2651")} (correctness, which found and confirmed by running both corners the second commit settles).</p>
{review_table()}

<h3 id="lift">The one corner where the result changes</h3>
{fig("fig-lift", "lift", "The one-member signature corner, traced at dev and #2651. The lift records one thing and returns another; dev used what it returns, #2651 uses what it records. Alexander's answer of 2026-10-21 is at the bottom.")}
<p>A one-member signature desugars to a one-field labeled product. When a definition's own type is something else, the walk lifts it into that product: <code>autolabel_singleton_tuple</code> analyzes a fresh copy against the field's type, records that bare analysis at the definition's ids, and returns <code>(x = …)</code> around the raw, unelaborated source ({d(S, 310, 358)}; it runs from {d(S, 2778, 2791)}). Dev's direct pass handed what it returns to <code>moduleexp_elab</code>; #2651 reads what it records. For the extra-member module that turns <code>M.x</code> from the module's raw source into 1, which {rep(21, "#pr-2651")} confirmed by running both commits. Alexander's answer: dev's result is a bug from the auto-labelling of one-member tuples, and 1 (or stuck) is right; the PR's test pins the fix.</p>
{fig("fig-lift-bare", "lift_bare", "The same corner with a plain value instead of a module: 5 on dev, stuck with #2651. Traced in the code at both commits, not run.")}
<p>The same path with a plain value is the one result found where dev gives a value and #2651 does not: <code>module M : {{ let x : Int }} = 5 in M.x</code> has no static error on dev and gives 5; with #2651, <code>M</code> is bound to 5 and <code>M.x</code> projects a label out of an Int, which is indeterminate ({d(UB, 184, 217)}, {d(TR, 1024, 1087)}). Written with <code>let</code> instead of <code>module</code>, the same program still gives 5, because the let keeps the lift ({d(S, 2182, 2187)}). Alexander expects a module bound to something that is not a module to be a static error; that is a question for Cyrus (<a href="#for-cyrus">below</a>). It does not hold up the merge, but it should be run once and named in the PR's description (<a href="#next">What next</a>).</p>

<h3 id="sits">Where #2651 sits</h3>
{fig("fig-landscape", "landscape", "#2651 among the other work: the finding it answers, the statics PRs beside it, the test that pins its count, Alexander's Modules II stack, Matthew's livelits branches, and Modular editors' DefStatics.")}
<p>Of the open {issue(2609)} PRs, #2651 is the smallest that touches statics, and it touches only the ModuleExp case. {pr(2603, "a let analyzed once")} merges cleanly with it, and together they bring a module binding to one analysis; {pr(2689, "statics analyzes each expression within a budget")}, a draft, pins that count, but merged #2651's first commit, {commit(E1)}, without the guard. {pr(2675, "reuse around a recursive let")} changes the let's co-context under a fixpoint, which <code>names_itself</code> does not read. The livelits branches {pr(2635)} and {pr(2597, "user-defined livelits")} carry the read-back without the guard. Modules II keeps the direct pass with <code>~coercible=true</code>, hence the one-line conflict.</p>
"""


# ------------------------------------------------------------------ 8. questions
def tags_html(tags):
    return "".join(f'<span class="tag {cls}">{t}</span>' for t, cls in tags)


def question_html(i, q):
    opts = []
    for text, note in q["options"]:
        nh = ""
        if note:
            cls = "optnote out" if note.startswith("recommended before") else "optnote"
            nh = f' <span class="{cls}">{note}</span>' if not note.startswith("recommended before") else (
                f' <span class="optnote out">recommended before the answer</span> <span class="optnote">withdrawn: it would undo the fix Alexander confirmed</span>')
        opts.append(f"<li>{text}{nh}</li>")
    ev = "\n".join(f'<li>{claim} <span class="refs">{" · ".join(refs)}</span></li>' for claim, refs in q["evidence"])
    ctx = "".join(f"<p>{p_}</p>" for p_ in q["context"])
    ans = f'<div class="answer">{q["answer"]}</div>' if q["answer"] else ""
    after = f'<p class="after">{q["after"]}</p>' if q["after"] else ""
    return f"""
<section class="q" id="q-{q['slug']}">
<h3><span class="qn">{i}.</span> {q['question']} <button type="button" class="copylink" data-target="q-{q['slug']}" title="Copy a link to this question">copy link</button></h3>
<div class="tags">{tags_html(q['tags'])}</div>
{ans}
{after}
<p><b>Context.</b></p>{ctx}
<p><b>Evidence</b> (links to the code at the commit named on each):</p>
<ul class="ev">
{ev}
</ul>
<p><b>Options.</b></p>
<ol class="opts">{''.join(opts)}</ol>
</section>"""


def questions_section():
    qs = "\n".join(question_html(i + 1, q) for i, q in enumerate(QUESTIONS))
    cy = "\n".join(f'<li id="{cid}"><b>{t}</b> {body}</li>' for cid, t, body in FOR_CYRUS)
    status = "; ".join(f'<a href="#q-{q["slug"]}">{i + 1}</a> ({q["short"]}): ' +
                       ", ".join(t for t, _ in q["tags"]) for i, q in enumerate(QUESTIONS))
    return f"""
<h2 id="questions-for-alexander">Questions for Alexander <button type="button" class="copylink" data-target="questions-for-alexander" title="Copy a link to this section">copy link</button></h2>
<p>Alexander, this section stands on its own. {pr(2651, "Statics: a module binding analyzes its definition once, not twice")} stops the ModuleExp case in statics from analyzing a module's definition a second time: <code>module M = def in body</code> is checked as <code>let M = def in body</code>, and the case now reads the definition's elaboration back from the record that let wrote, keeping the second analysis only as a fallback (the picture is <a href="#pr">The pull request, drawn</a>). You and Matthew reviewed it on 2026-10-21, and your answers from that review are below, paraphrased. One open question should be settled before merging: <a href="#q-merge-order-with-modules-ii">question 2</a>, the merge order against your stack.</p>
<p class="callout"><b>From here on, please answer on {pr(2651)} itself,</b> as comments there, rather than here. The open questions are 2, 4 and 5. Where they stand: {status}.</p>
{qs}

<h3 id="for-cyrus">For Cyrus <button type="button" class="copylink" data-target="for-cyrus" title="Copy a link to this list">copy link</button></h3>
<p>Three design questions came out of the review that are Cyrus's to decide; Alexander raised the second and third. None holds up #2651.</p>
<ol class="cyrus">
{cy}
</ol>
"""


# ------------------------------------------------------------------ next and method
NEXT = f"""
<h2 id="next">What next</h2>
<ol>
<li><b>Settle the merge order against Modules II on #2651, then merge it.</b> Question 2's recommendation: merge into dev now, and add <code>~coercible=true</code> to the fallback when Alexander's stack next rebases (parts 2 to 9).</li>
<li><b>Post the open questions on #2651 for Alexander to answer there</b> (questions 2, 4 and 5, linking <a href="#questions-for-alexander">this section</a>), marked with <code>:robot_face:</code>, since the comment is drafted with AI (Alexander's preference).</li>
<li><b>Run <code>module M : {{ let x : Int }} = 5 in M.x</code> with the command-line tool at dev and at 29c08fd8fa.</b> Traced: 5 on dev, stuck with #2651. Name the result in #2651's description as a known change, pending Cyrus's answer on modules bound to non-modules.</li>
<li><b>Tighten #2651's tests.</b> Pin the self-naming error to the FreeConstructor mark on F's use; add <code>module F = fun x -&gt; x + 1 in F(2)</code>, expecting 3, for the read-back after the let's recursive path; add a self-naming module with a signature for the fallback's other arm.</li>
<li><b>Correct the PR's comment:</b> "add records exactly the elab_term it returns" holds for <code>add</code>, not for the one-member lift; and the "no record found" arm is defensive.</li>
<li><b>Alexander's suggestion, in #2651 or a follow-up:</b> an argument on the let analysis saying not to try the recursive case, passed by the ModuleExp case. The let then reports a self-reference as unbound by itself, <code>names_itself</code> and the fallback go, and a module binding skips the recursion probe too.</li>
<li><b>Take the three design questions to Cyrus</b> (<a href="#for-cyrus">For Cyrus</a>): recursive modules (and the item form inside braces), modules bound to non-modules as a static error, and what the <code>module</code> keyword should add over <code>let</code>.</li>
<li><b>Port the guard</b> ({commit(P)}) to Matthew's livelits branches #2635 and #2597, and redo #2689's merge, which took {commit(E1)}.</li>
<li><b>File a dev issue for the lift returning raw source</b> ({d(S, 329, 334)}): any term that needs elaboration, analyzed against a one-member labeled product it does not match, reaches the evaluator unelaborated.</li>
</ol>
"""

METHOD = f"""
<h2 id="method">How this was put together</h2>
<ul>
<li><b>What was read:</b> dev at {commit(D)} and #2651 at {commit(P)} (first commit {commit(E1)}, merge base {commit(MB)}), read on 2026-10-21 after fetching both. For Modules II, the heads of parts 1, 2, 3 and 9 ({commit(M1)}, {commit(M2)}, {commit(M3)}, {commit(M9)}); #2603 at {commit(T2603)}; #2469 at {commit(ME)}. Every file:line in this page links to GitHub at the full commit it names, and each range was checked to exist there.</li>
<li><b>Six readers of the code,</b> one subsystem each: the edit-to-statics pipeline, the statics core, modules, elaboration to evaluation, the PR itself, and its performance context. They read only; nothing was built, run or timed for this report. Their notes are in <code>024/data/research-notes.json</code>.</li>
<li><b>The questions</b> were drafted from two lenses, what a reviewer of #2651 needs and what only the Modules II owner can say, and each was checked for its premise (does the code say what it assumes, line by line at the named commits) and its need (does anything on record already answer it: the PR's conversation, the Modules II descriptions, the docs, the tests). Their checks are in <code>024/data/questions.json</code>. None was found already answered.</li>
<li><b>Alexander's answers</b> are from his review with Matthew on 2026-10-21, relayed by Matthew and paraphrased here.</li>
<li><b>A fact-check</b> re-derived each line number at the commit its link names; dev had moved since some notes were written. The figures were rendered to images with ffmpeg's SVG reader, in the light and dark colours, and looked at; the page was not opened in a browser.</li>
<li><b>Not confirmed:</b> the bare-value program's stuck result, the editor's context inside a function-valued module and the tuple-literal case were traced in the code, not run. The analysis counts were counted from the code, not measured. The timings quoted are #2651's own and #2609's finding 7 (two runs each); this report timed nothing. The two corners {rep(21, "#pr-2651")} found, the extra-member module and the self-naming definition, were confirmed there by running the command-line tool at {commit(E1)} and at dev's {commit(MB)}.</li>
<li><b>Credit:</b> #2651 and #2603 are Matthew Hammer's, made with Claude. Dev's module system and the <code>module</code> keyword are Andrew Blinn's; Modules II is Alexander Bandukwala's; the statics without a separate elaborator, Mode or Self is Matt Keenan's; DefStatics is Andrew Blinn's, in #2469.</li>
<li><b>The page</b> is made by <code>024/drivers/gen024.py</code> (figures in <code>figs.py</code>, questions in <code>questions.py</code>).</li>
</ul>
"""

COPY_SCRIPT = """
<script>
/* "copy link" buttons: copy this page's address with the section's or
   question's anchor; if the clipboard is not available, show the link in a
   field, selected, to copy by hand. */
(() => {
  document.querySelectorAll("button.copylink").forEach(b => {
    b.addEventListener("click", async e => {
      e.preventDefault();
      const url = location.origin + location.pathname + "#" + b.dataset.target;
      let ok = false;
      try { await navigator.clipboard.writeText(url); ok = true; } catch (_) {}
      if (!ok) {
        let f = b.parentElement.nextElementSibling;
        if (!f || !f.classList || !f.classList.contains("copyfield")) {
          f = document.createElement("input"); f.className = "copyfield"; f.readOnly = true;
          b.parentElement.after(f);
        }
        f.value = url; f.focus(); f.select();
      }
      b.textContent = ok ? "copied" : "select and copy";
      b.classList.add("done");
      setTimeout(() => { b.textContent = "copy link"; b.classList.remove("done"); }, 1600);
    });
  });
})();
</script>
"""


def main():
    body = (TOP + SUBSYSTEMS + REPRESENTATIONS + PROTOCOLS + STATICS + MODULES + PR_SECTION + REVIEW +
            questions_section() + NEXT + METHOD)
    # figure references
    def figref(m):
        fid = m.group(1)
        if fid not in FIGS:
            raise SystemExit(f"unknown figure {fid}")
        return f'<a href="#{fid}">Figure {FIGS[fid]}</a>'
    body = re.sub(r"\[\[(fig-[a-z-]+)\]\]", figref, body)
    body = body.replace("^report(21)", '<a href="../021/#pr-2651"><code class="ref"><b>^report(</b>21<b>)</b></code></a>')
    page = HEAD + body + "\n</main>\n" + COPY_SCRIPT + "</body>\n</html>\n"
    open(OUT, "w").write(page)
    for w in svgkit.WARN:
        print("WARN", w)
    check_refs()
    print(f"wrote {OUT}: {len(page):,} bytes, {len(FIGS)} numbered figures, {len(set(REFS))} code ranges")


def check_refs():
    """Every linked range exists at its commit; print each range's first line."""
    cache, bad = {}, 0
    lines = []
    for commit_, path, a, b in sorted(set(REFS), key=lambda r: (r[1], r[0], r[2])):
        key = (commit_, path)
        if key not in cache:
            r = subprocess.run(["git", "-C", HAZEL, "show", f"{commit_}:{path}"], capture_output=True, text=True)
            cache[key] = r.stdout.split("\n") if r.returncode == 0 else None
        src = cache[key]
        if src is None or b > len(src) or a < 1:
            bad += 1
            print(f"BAD REF {commit_[:10]} {path}:{a}-{b} (file has {len(src) if src else 'no'} lines)")
            continue
        lines.append(f"{commit_[:10]} {os.path.basename(path)}:{a}-{b} | {src[a - 1].strip()[:90]} || {src[b - 1].strip()[:60]}")
    open(os.path.join(HERE, "refs-check.txt"), "w").write("\n".join(lines) + "\n")
    print(f"refs: {len(lines)} ok, {bad} bad (see refs-check.txt)")


if __name__ == "__main__":
    main()
