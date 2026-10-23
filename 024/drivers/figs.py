"""The figures of ^report(24), as inline SVG (see svgkit.py)."""
from svgkit import Svg, tw


# ------------------------------------------------------------------ short answers
def a_passes():
    s = Svg("fig-a-passes", 290, 116,
            "Bars: analyses of a module binding's definition. dev 3, with #2651 2, with #2651 and #2603 1.")
    s.text(4, 14, "analyses of def, per module binding", cls="tm", size=11, maxw=262)
    for i, (lab, n, c) in enumerate([("dev", 3, "r"), ("#2651", 2, "w"), ("#2651 + #2603", 1, "g")]):
        y = 28 + i * 28
        s.text(112, y + 13, lab, anchor="end")
        s.rect(118, y, n * 44, 18, cls=f"bar {c}", rx=3)
        s.text(118 + n * 44 + 6, y + 13, str(n), cls="tb")
    return s.render()


def a_infomap():
    s = Svg("fig-a-infomap", 340, 100,
            "Three boxes: the expanded let writes an Info at the definition's id into the info map; "
            "the ModuleExp case reads its elaboration back.")
    s.box(2, 8, 98, 48, ["expanded let", "writes Info"], cls="bx k")
    s.box(122, 8, 96, 48, ["info map", "id → Info"], cls="bx a")
    s.box(240, 8, 98, 48, ["ModuleExp", "reads elab"], cls="bx g")
    s.arrow([(100, 32), (120, 32)], marker="m-mu")
    s.arrow([(218, 32), (238, 32)], marker="m-mu")
    s.text(170, 84, "one Info per id; the last write wins", cls="tm", anchor="middle", size=11, maxw=330)
    return s.render()


def a_nesting():
    s = Svg("fig-a-nesting", 280, 138,
            "Grouped bars by nesting depth 1, 2, 3: dev 3, 9, 27 analyses of the innermost definition; "
            "with #2651 2, 4, 8; with #2651 and #2603 1, 1, 1.")
    for x, c, lab in [(4, "r", "dev"), (58, "w", "#2651"), (128, "g", "#2651 + #2603")]:
        s.rect(x, 4, 10, 10, cls=f"bar {c}", rx=2)
        s.text(x + 14, 13, lab, size=11)
    vals = {1: (3, 2, 1), 2: (9, 4, 1), 3: (27, 8, 1)}
    base, k = 112, 2.6
    for d in (1, 2, 3):
        x0 = 30 + (d - 1) * 86
        for j, (v, c) in enumerate(zip(vals[d], "rwg")):
            h = max(2, v * k)
            x = x0 + j * 22
            s.rect(x, base - h, 18, h, cls=f"bar {c}", rx=2)
            s.text(x + 9, base - h - 3, str(v), anchor="middle", size=10)
        s.text(x0 + 31, 128, f"depth {d}", cls="tm", anchor="middle", size=11)
    return s.render()


def a_lift():
    s = Svg("fig-a-lift", 312, 84,
            "What M.x gives for a module with an extra member under a one-member signature: "
            "on dev the module's raw source, with #2651 the value 1.")
    s.text(4, 26, "M.x on dev", size=12)
    s.box(108, 8, 200, 28, ["{ let x = 1; let y = 2 }"], cls="bx r", mono=True, size=11)
    s.text(4, 66, "M.x, #2651", size=12)
    s.box(108, 48, 44, 28, ["1"], cls="bx g", mono=True)
    s.text(160, 66, "a fix (Alexander)", cls="tm", size=11, maxw=150)
    return s.render()


def a_guard():
    s = Svg("fig-a-guard", 330, 112,
            "The self-naming guard: if the let's elaboration is Let(_, FixF, _), the definition is analyzed "
            "again and the error is kept; otherwise its elaboration is read back with no pass.")
    s.box(4, 41, 136, 30, ["Let(_, FixF, _)?"], cls="bx w", mono=True)
    s.box(180, 6, 146, 30, ["read back, no pass"], cls="bx g")
    s.box(180, 76, 146, 30, ["pass again: error"], cls="bx a")
    s.arrow([(140, 50), (160, 50), (160, 21), (178, 21)], marker="m-g")
    s.arrow([(140, 62), (160, 62), (160, 91), (178, 91)], marker="m-a")
    s.text(163, 44, "no", cls="tm", size=10)
    s.text(163, 77, "yes", cls="tm", size=10)
    return s.render()


def a_merge():
    s = Svg("fig-a-merge", 320, 104,
            "Merge check chips: dev clean, #2603 clean, Modules II part 1 clean, parts 2 to 9 one conflicting line.")
    w = s.chip(4, 6, "dev: clean", cls="bx g")
    s.chip(4 + w + 8, 6, "#2603: clean", cls="bx g")
    s.chip(4, 38, "Modules II part 1: clean", cls="bx g")
    s.chip(4, 70, "parts 2 to 9: one line conflicts", cls="bx w")
    return s.render()


def a_questions():
    s = Svg("fig-a-questions", 330, 160,
            "The five questions for Alexander: two answered, one of them for now; three open, one of those "
            "to settle before merging; and three design questions for Cyrus.")
    rows = [("1  one-member lift: answered", "bx g"),
            ("2  merge order: open, before merging", "bx w"),
            ("3  recursive modules: answered for now", "bx b2"),
            ("4  def_elab_direct: open", "bx"),
            ("5  tests to pin: open", "bx")]
    for i, (t, c) in enumerate(rows):
        s.chip(4, 4 + i * 26, t, cls=c, size=11, h=21)
    s.chip(4, 134, "for Cyrus: 3 design questions", cls="bx a", size=11, h=21)
    return s.render()


# ------------------------------------------------------------------ 1. subsystems
def subsystems():
    s = Svg("fig-subsystems", 1000, 446,
            "Five subsystems left to right: editor, MakeTerm, statics, evaluation, results; results go back as "
            "actions. Below statics, the info map, and the eight things that read it.", minw=780)
    xs = [10, 217, 424, 631, 838]
    boxes = [("Editor", ["tiles with ids", "zipper = the caret", "Perform.go edits it"], "bx k"),
             ("MakeTerm", ["tiles to Exp.t", "term id = tile id", "holes filled first"], "bx k"),
             ("Statics", ["walks the program", "info map: id → Info", "elaborates too"], "bx a"),
             ("Evaluation", ["in the eval worker", "runs the program", "reuse keyed by id"], "bx b2"),
             ("Results", ["values, samples,", "tests, as actions;", "then a redraw"], "bx k")]
    for x, (t, ls, c) in zip(xs, boxes):
        s.box(x, 40, 150, 118, ls, cls=c, title=t)
    for i, lab in enumerate(["segment", "Exp.t", "message", "Result"]):
        x1, x2 = xs[i] + 150, xs[i + 1]
        s.arrow([(x1 + 2, 99), (x2 - 2, 99)], marker="m-mu")
        s.text((x1 + x2) / 2, 91, lab, cls="tm", anchor="middle", size=11, maxw=57)
    s.arrow([(913, 40), (913, 24), (85, 24), (85, 38)], cls="ar d", marker="m-mu")
    s.text(499, 18, "the worker's answers come back as actions: update, calculate, redraw",
           cls="tm", anchor="middle", size=11)
    # the info map and its readers
    s.box(390, 225, 220, 60, ["one Info per id", "the last write wins"], cls="bx a", title="info map")
    s.arrow([(499, 158), (499, 223)], cls="ar a", marker="m-a")
    s.text(507, 196, "add writes", cls="ta", size=11)
    left = [("cursor inspector", "cls, ty, ana, marks, message"),
            ("error and warning marks", "marks, via error_ids"),
            ("completion", "ctx and ana at the caret"),
            ("the next edit", "Perform.go reads the old map")]
    right = [("projectors and livelits", "the Info at their id; its ctx"),
             ("probes", "ctx, co_ctx, ancestors"),
             ("EvalInfo, for the worker", "elab_term, co_ctx per id"),
             ("ModuleExp case (#2651)", "elab_term at def's id")]
    for i, (t, l) in enumerate(left):
        y = 190 + i * 50
        s.box(20, y, 290, 42, [l], title=t, cls="bx", size=11)
        s.line(390, 255, 312, y + 21, cls="ar thin")
    for i, (t, l) in enumerate(right):
        y = 190 + i * 50
        s.box(690, y, 290, 42, [l], title=t, cls="bx a" if i == 3 else "bx", size=11)
        s.line(610, 255, 688, y + 21, cls="ar thin a" if i == 3 else "ar thin")
    s.text(500, 420, "dev: one walk of the whole program per refresh. Modular editors (#2469, not on dev): one per "
           "top-level definition (DefStatics).", cls="tm", anchor="middle", size=11)
    return s.render()


# ------------------------------------------------------------------ 2. one id
def ids():
    s = Svg("fig-ids", 1000, 214,
            "One id across five representations: the tile, the term node, the Info, the EvalInfo entry, and the "
            "worker's samples and cache entries all use the same id.", minw=740)
    xs = [10, 217, 424, 631, 838]
    bx = [("tile", ["in the segment", "id: a1"]),
          ("term node", ["Exp.t, from MakeTerm", "ids: [a1, …]"]),
          ("Info", ["statics' record", "at a1 in the map"]),
          ("EvalInfo entry", ["elab_term, co_ctx", "at a1, sent along"]),
          ("in the worker", ["probe samples and", "cache entries at a1"])]
    cls = ["bx k", "bx k", "bx a", "bx b2", "bx b2"]
    for x, (t, ls), c in zip(xs, bx, cls):
        s.box(x, 30, 160, 76, ls, cls=c, title=t)
    for i, lab in enumerate(["MakeTerm", "Statics.mk", "of_info_map", "postMessage"]):
        x1, x2 = xs[i] + 160, xs[i + 1]
        s.arrow([(x1 + 2, 68), (x2 - 2, 68)], marker="m-mu")
        s.text((x1 + x2) / 2, 124, lab, cls="tm", anchor="middle", size=11)
    s.line(90, 160, 918, 160, cls="ar d a")
    for x in xs:
        s.line(x + 80, 106, x + 80, 160, cls="ar thin a")
        s.add(f'<circle cx="{x + 80}" cy="160" r="4" class="dot a"/>')
    s.text(500, 188, "the same id, a1, names one piece of code in every representation; consumers meet at it",
           cls="ta", anchor="middle", size=12)
    return s.render()


# ------------------------------------------------------------------ 3. round trip
def roundtrip():
    s = Svg("fig-roundtrip", 1000, 712,
            "Sequence diagram of one edit: the key becomes an action, the editor edits the zipper with the old "
            "statics, the calculate phase debounces and then reruns MakeTerm and statics, the syntax cache and "
            "probes are refreshed, EvalResult sends the elaborated program and EvalInfo to the eval worker, and "
            "the worker's Ack, ReusePlan, Stream and Result messages come back as actions.", minw=840)
    L = {1: 80, 2: 245, 3: 420, 4: 600, 5: 760, 6: 935}
    s.rect(2, 2, 848, 706, cls="lane", rx=10)
    s.rect(858, 2, 140, 706, cls="lane2", rx=10)
    s.text(425, 22, "main thread", cls="tm", anchor="middle", size=12)
    s.text(928, 22, "worker thread", cls="t2", anchor="middle", size=12)
    heads = {1: ("key event", "CodeEditable"), 2: ("Editor.update", "Perform.go"),
             3: ("Main.apply", "calculate phase"), 4: ("CachedStatics", "MakeTerm, Statics"),
             5: ("EvalResult", "EvalRequest"), 6: ("eval worker", "Evaluator")}
    for k, (t, l) in heads.items():
        w = 150 if k < 6 else 120
        s.box(L[k] - w / 2, 34, w, 46, [l], title=t, cls="bx b2" if k == 6 else "bx", size=11)
        s.line(L[k], 80, L[k], 700, cls="life")

    def msg(a, b, y, lab, dashed=False, cls=""):
        xa, xb = L[a], L[b]
        d = 4 if xb > xa else -4
        s.arrow([(xa, y), (xb - d, y)], cls="ar" + (" d" if dashed else "") + (" " + cls if cls else ""),
                marker={"a": "m-a", "b2": "m-2"}.get(cls, "m-mu"))
        s.text((xa + xb) / 2, y - 6, lab, cls="t", anchor="middle", size=11, maxw=abs(xb - xa) - 6)

    def note(k, y, lines, cls="bx", w=None, dx=0):
        w = w or max(tw(l, 11) for l in lines) + 18
        h = len(lines) * 15 + 10
        s.box(L[k] - w / 2 + dx, y - h / 2, w, h, lines, cls=cls, size=11)

    msg(1, 2, 118, "Perform(Insert(c))")
    note(2, 148, ["edits with the OLD statics"], cls="bx w")
    msg(2, 3, 190, "Updated.t {is_edit}")
    note(3, 226, ["debounce 225 ms:", "Defer while typing"], cls="bx w")
    s.path("M420 262 H446 V284 H424", cls="ar d", marker="m-mu")
    s.text(452, 277, "timer: Force", cls="tm", size=11)
    msg(3, 4, 316, "CachedStatics.init(zipper)", cls="a")
    note(4, 346, ["MakeTerm: complete, parse"], cls="bx a")
    note(4, 378, ["Statics.mk: walk from an empty map"], cls="bx a")
    msg(4, 3, 414, "info map, elaborated", dashed=True, cls="a")
    note(3, 446, ["completion, CachedSyntax, probes"])
    msg(3, 5, 486, "EvalResult.calculate")
    note(5, 518, ["elab changed? EvalInfo.of_info_map"], dx=-40)
    msg(5, 6, 560, "Evaluate (Marshal)", cls="b2")
    msg(6, 5, 596, "Ack", dashed=True, cls="b2")
    msg(6, 5, 622, "ReusePlan, Stream", dashed=True, cls="b2")
    msg(6, 5, 648, "Result", dashed=True, cls="b2")
    msg(5, 3, 684, "UpdateResult: update, calculate, redraw", dashed=True)
    return s.render()


# ------------------------------------------------------------------ 4. worker protocol
def worker():
    s = Svg("fig-worker", 920, 410,
            "Sequence diagram of the eval worker's protocol: the page posts Evaluate; the worker answers Ack at "
            "once, then ReusePlan, then Stream after each slice of 5000 steps, then Result. Timeouts and "
            "retries on the page's side.", minw=700)
    C, Wk = 270, 720
    s.box(C - 95, 20, 190, 46, ["the page"], title="WorkerClient", cls="bx", size=11)
    s.box(Wk - 95, 20, 190, 46, ["the eval worker"], title="WorkerServer", cls="bx b2", size=11)
    s.line(C, 66, C, 396, cls="life")
    s.line(Wk, 66, Wk, 396, cls="life")

    def m(y, lab, back=False, dashed=False, cls="b2"):
        a, b = (Wk, C) if back else (C, Wk)
        d = -4 if back else 4
        s.arrow([(a, y), (b - d, y)], cls=f"ar {cls}" + (" d" if dashed else ""), marker="m-2")
        s.text((C + Wk) / 2, y - 6, lab, anchor="middle", size=11, maxw=Wk - C - 10)

    def left(y, t):
        s.text(C - 10, y, t, cls="tm", anchor="end", size=11, maxw=C - 14)

    def right(y, t):
        s.text(Wk + 10, y, t, cls="tm", size=11, maxw=920 - Wk - 14)

    m(96, "Evaluate {request_id, batch of (key, {expr, eval_info_map, prev})}")
    left(100, "Marshal-encoded string")
    right(100, "on_request")
    m(132, "Ack {request_id}: posted at once", back=True, dashed=True)
    left(136, "clears the 5 s ack timer")
    m(168, "ReusePlan: predicted reuse, for programs of 2500+ entries", back=True, dashed=True)
    left(172, "UpdateStreamingEval")
    s.box(Wk + 8, 190, 184, 54, ["slices of 5000 steps,", "setTimeout(0) between"], cls="bx b2", size=11)
    m(212, "Stream {key, outbox}: entries done so far", back=True, dashed=True)
    left(216, "MergeStreamingEval")
    m(248, "Stream … (one per slice that finished entries)", back=True, dashed=True)
    m(290, "Result {response: (value, EvaluatorState) per key, eval_time}", back=True, dashed=True)
    left(294, "UpdateResult")
    right(294, "a newer request abandons")
    right(310, "the old one's slices")
    s.box(10, 330, 252, 58, ["no Ack in 5 s: restart, retry (×3)", "20 s in all: restart, report Timeout"],
          cls="bx w", size=11, align="start")
    return s.render()


# ------------------------------------------------------------------ 5. the walk
def walk():
    s = Svg("fig-walk", 1000, 350,
            "The statics walk: uexp_to_info_map takes a context, an expected type and a term; each case analyzes "
            "its children (context and expected type go down, Info, elaboration and map come up) and ends in add, "
            "which writes an Info at the term's ids and returns the same elaboration. Two outputs: the info map, "
            "and the root's elaboration for the evaluator.", minw=780)
    s.box(20, 14, 420, 46, ["uexp_to_info_map(~ctx, ~ana, term, m)", "returns (Info.exp, elab, m)"],
          cls="bx k", mono=True, size=12)
    s.box(120, 92, 200, 34, ["Let(p, def, body)"], mono=True)
    s.box(30, 200, 150, 34, ["go(def)"], mono=True)
    s.box(260, 200, 150, 34, ["go(body)"], mono=True)
    s.arrow([(185, 126), (105, 198)], marker="m-mu")
    s.arrow([(125, 200), (205, 128)], cls="ar d a", marker="m-a")
    s.arrow([(255, 126), (315, 198)], marker="m-mu")
    s.arrow([(345, 200), (285, 128)], cls="ar d a", marker="m-a")
    s.text(108, 158, "ctx, ana", cls="tm", anchor="end", size=11)
    s.text(332, 158, "Info, elab, m", cls="ta", size=11)
    s.text(30, 262, "solid: what goes down (context, expected type)", cls="tm", size=11)
    s.text(30, 278, "dashed: what comes up (Info, elaboration, map)", cls="ta", size=11)
    s.box(470, 82, 230, 92, ["marks and message", "ty = fixed_typ(ana, syn)", "writes Info at its ids"],
          title="add (lines 204-269)", cls="bx a")
    s.arrow([(320, 109), (468, 109)], marker="m-mu")
    s.text(394, 102, "every case ends in", cls="tm", anchor="middle", size=11)
    # the map
    s.rect(740, 30, 240, 214, cls="bx a")
    s.text(860, 52, "info map", cls="tb", anchor="middle", size=13)
    s.text(860, 70, "Id.Map, the last write wins", cls="tm", anchor="middle", size=11)
    for i, r in enumerate(["id(Let)  → Info", "id(def)  → Info", "id(body) → Info", "…"]):
        y = 84 + i * 36
        s.box(756, y, 208, 28, [r], cls="bx", mono=True, size=12, align="start")
    s.arrow([(700, 128), (738, 128)], cls="ar a", marker="m-a")
    s.text(719, 146, "add_info", cls="ta", anchor="middle", size=10)
    s.arrow([(585, 174), (585, 286)], cls="ar a", marker="m-a")
    s.text(577, 236, "returns the same elab (268)", cls="ta", anchor="end", size=11)
    s.box(20, 288, 690, 44, ["the root's returned elaboration: Statics.mk → CachedStatics.elaborated → the evaluator"],
          cls="bx b2")
    s.arrow([(860, 244), (860, 286)], cls="ar a", marker="m-a")
    s.box(740, 288, 240, 44, ["its readers (Figure 1)"], cls="bx")
    return s.render()


# ------------------------------------------------------------------ 6. an Info record
GROUPS = {"A": ("b2", "context in"), "B": ("w", "mode: the expected type"), "C": ("k", "self: what the term gives"),
          "D": ("g", "co-context out"), "E": ("a", "the terms")}


def info():
    s = Svg("fig-info", 960, 470,
            "An Info.exp record field by field, colour-coded into five groups: the context in (ctx, ancestors), "
            "the mode (ana), the self (elab_syn_ty, marks, message, warnings, ty), the co-context out (co_ctx, "
            "probe_targets), and the terms (user_term, elab_term, which #2651 reads back).", minw=760)
    s.rect(20, 14, 400, 440, cls="bx")
    s.text(36, 40, "Info.exp", cls="tb mono", size=14)
    s.text(122, 40, "one per expression id (Info.re:35-53)", cls="tm", size=11)
    rows = [("user_term", "E", "the term as written"),
            ("elab_term", "E", "elaboration; #2651 reads it"),
            ("ancestors", "A", "ids of the enclosing terms"),
            ("ctx", "A", "the variables in scope"),
            ("ana", "B", "the type expected of it"),
            ("elab_syn_ty", "C", "the type it gives"),
            ("marks", "C", "its static errors"),
            ("co_ctx", "D", "free variables it uses"),
            ("probe_targets", "D", "probes at or under it"),
            ("cls", "", "its form, for display"),
            ("message", "C", "the inspector's text"),
            ("warnings", "C", "e.g. an unused variable"),
            ("ty", "C", "its type after hole fixing"),
            ("label_inference", "", "labeled tuples (and 3 more)")]
    for i, (f, g, c) in enumerate(rows):
        y = 70 + i * 27
        col = GROUPS[g][0] if g else "k"
        s.add(f'<circle cx="40" cy="{y - 4}" r="5" class="dot {col}"/>')
        s.text(52, y, f, cls="ta tb" if f == "elab_term" else "t", mono=True, size=12)
        s.text(196, y, c, cls="ta" if f == "elab_term" else "tm", size=11, maxw=218)
    texts = {"A": ["ctx and ancestors come from the parent: what is in",
                   "scope here, and which terms enclose this one."],
             "B": ["ana. Unknown(SynSwitch) means synthesize; anything",
                   "else means check against it. Mode is no longer a type."],
             "C": ["elab_syn_ty, marks, message, ty: what it synthesizes,",
                   "its errors, and the meet with ana (fixed_typ)."],
             "D": ["co_ctx lists each free variable's uses, passed up to",
                   "its binder (unused names, probes, reuse checks)."],
             "E": ["user_term as written; elab_term, its elaboration,",
                   "which add both records and returns (line 268)."]}
    for i, g in enumerate("ABCDE"):
        col, title = GROUPS[g]
        y = 14 + i * 89
        s.box(450, y, 490, 78, texts[g], cls=f"bx {col}" if col != "k" else "bx k", title=title,
              size=12, align="start", pad=26)
        s.add(f'<circle cx="466" cy="{y + 20}" r="5" class="dot {col}"/>')
    return s.render()


# ------------------------------------------------------------------ 7. a let, pass by pass
def let():
    s = Svg("fig-let", 1000, 580,
            "Flow of the Let case on dev: a pattern probe and a recursion probe whose maps are dropped, then the "
            "structural is_recursive test; not recursive: one real pass in the outer context; recursive: two "
            "dropped passes and a final pass with the name in scope; then the body, the pattern again, and the "
            "elaboration, with a FixF when the definition uses the name. Counts: 2 analyses of a non-function "
            "definition, 4 of a function; with #2603, 1, 1 and 3.", minw=780)
    s.box(110, 16, 440, 40, ["pattern probe: p's type; map dropped (2052)"], cls="bx d")
    s.box(110, 74, 440, 40, ["recursion probe: go(def) in p's context (2070); map dropped"], cls="bx d")
    s.box(110, 132, 440, 54, ["is_recursive? one variable, one function, an arrow", "type: the shape only (2024-2039)"],
          cls="bx w")
    s.arrow([(330, 56), (330, 72)])
    s.arrow([(330, 114), (330, 130)])
    s.box(20, 222, 280, 54, ["real pass in the outer context,", "against p's type (2079): kept"], cls="bx")
    s.box(330, 206, 310, 36, ["def_base, in p's context (2091): dropped"], cls="bx d")
    s.box(330, 252, 310, 36, ["def_base2, name in scope (2103): dropped"], cls="bx d")
    s.box(330, 298, 310, 40, ["final pass, name in scope (2121): kept"], cls="bx")
    s.arrow([(200, 186), (160, 220)])
    s.text(168, 204, "no", cls="tm", anchor="end", size=11)
    s.arrow([(460, 186), (485, 204)])
    s.text(482, 196, "yes", cls="tm", size=11)
    s.arrow([(485, 242), (485, 250)])
    s.arrow([(485, 288), (485, 296)])
    s.box(110, 366, 440, 40, ["body (2152), then p again with the body's co_ctx (2154)"], cls="bx")
    s.arrow([(160, 276), (160, 364)])
    s.arrow([(485, 338), (485, 364)])
    s.box(110, 426, 440, 50, ["requires_fixf? recursive, and def or p's type", "uses the name (2172-2181)"],
          cls="bx w")
    s.arrow([(330, 406), (330, 424)])
    s.box(20, 506, 280, 56, ["Let(p, def′, body)", "def′ aligned and named (2184-2187)"], cls="bx")
    s.box(330, 506, 310, 56, ["Let(p, FixF(p, def′), body)", "co_ctx patched at def's id (2216-2228)"], cls="bx")
    s.arrow([(200, 476), (160, 504)])
    s.text(168, 492, "no", cls="tm", anchor="end", size=11)
    s.arrow([(460, 476), (485, 504)])
    s.text(482, 488, "yes", cls="tm", size=11)
    s.box(680, 16, 310, 74, ["not a function: 2 (probe, real)", "a function: 4 (probe, 2 dropped, final)"],
          title="analyses of def, dev", cls="bx r", align="start", size=12)
    s.box(680, 108, 310, 108, ["not a function: 1, and no probe", "a function that neither uses nor",
                               "shadows its name: 1, the probe kept", "otherwise: 3 (the probe is def_base)"],
          title="with #2603 (open)", cls="bx g", align="start", size=12)
    s.box(680, 236, 310, 74, ["dashed: the map is dropped", "solid: writes the info map"],
          title="key", cls="bx", align="start", size=12)
    return s.render()


# ------------------------------------------------------------------ 8. ModuleExp on dev, step by step
def module_steps():
    s = Svg("fig-module-steps", 1000, 500,
            "A table of the ModuleExp case's seven steps on dev and which ids each step writes in the info map: "
            "the name's InfoMPat, the let's Infos for the definition, the body, the pattern and the binding, the "
            "cls override, the direct pass that writes the definition's Infos again, and the final add.",
            minw=800)
    cols = [("M, the name", 490), ("ModuleExp's id", 615), ("inside def", 740), ("inside body", 865)]
    for t, x in cols:
        s.text(x + 57, 30, t, cls="tb", anchor="middle", size=12, maxw=112)
    s.text(20, 30, "step (line numbers in Statics.re at dev)", cls="tb", size=12)
    steps = [
        (["MPat: the name's cursor info (2728-2735)"], {0: (["InfoMPat"], "b2")}),
        (["mpat_to_pat: M : S, with S desugared to a", "labeled product (ModuleHelpers.re:51-60)"], {}),
        (["expanded = Let(pat, def, body), given the", "ModuleExp's own id (2736-2741)"], {}),
        (["go(expanded): the let case (2742), probe and", "real pass over def, then body and pattern"],
         {0: (["InfoPat", "overwrites"], "w"), 1: (["the let's", "Info"], "bx"), 2: (["real pass:", "Infos A"], "a"),
          3: (["Infos"], "bx")}),
        (["cls override (2743-2756), which step 7", "writes over anyway"], {1: (["cls changed,", "rewritten"], "d")}),
        (["dev: go(def) again, directly, against S or", "syn (2757-2762)"], {2: (["direct pass:", "Infos B win"], "r")}),
        (["moduleexp_elab, then add (2763-2772)"], {1: (["final Info"], "g")}),
    ]
    for i, (txt, cells) in enumerate(steps):
        y = 48 + i * 58
        s.add(f'<circle cx="32" cy="{y + 24}" r="11" class="dot {"r" if i == 5 else "k"}"/>')
        s.text(32, y + 28, str(i + 1), cls="tb", anchor="middle", size=12)
        s.box(50, y, 425, 48, txt, cls="bx r" if i == 5 else "bx", align="start", size=12)
        for j, (_, x) in enumerate(cols):
            if j in cells:
                ls, c = cells[j]
                cl = "bx" if c == "bx" else ("bx d" if c == "d" else f"bx {c}")
                s.box(x, y, 115, 48, ls, cls=cl, size=11)
            else:
                s.text(x + 57, y + 28, "·", cls="tm", anchor="middle")
    s.box(50, 458, 930, 34, ["with #2651, step 6 is a lookup at def's id: Infos A stay, and their elab_term "
                             "is what moduleexp_elab gets"], cls="bx a")
    return s.render()


# ------------------------------------------------------------------ 9. moduleexp_elab
def moduleexp_elab():
    s = Svg("fig-moduleexp-elab", 1000, 392,
            "Left, the let's elaboration: a Let whose pattern carries the signature ascription and whose "
            "definition is aligned and named, or wrapped in a FixF. Right, what moduleexp_elab builds: the same "
            "Let with the ascription stripped and the direct elaboration of the definition in place. Below, the "
            "four things that are dropped.", minw=780)
    s.rect(20, 34, 440, 200, cls="bx k")
    s.text(36, 58, "the let's elaboration", cls="tb", size=13)
    s.text(36, 76, "expanded_elab (Statics.re:2182-2230)", cls="tm", size=11)
    s.box(36, 88, 408, 38, ["pattern: M : S (the ascription)"], cls="bx w", align="start")
    s.box(36, 134, 408, 38, ["def: align(def_elab) + name, or FixF(p, def)"], cls="bx w", align="start")
    s.box(36, 180, 408, 38, ["body_elab"], cls="bx", align="start")
    s.rect(540, 34, 440, 200, cls="bx a")
    s.text(556, 58, "what moduleexp_elab builds", cls="tb", size=13)
    s.text(556, 76, "ModuleHelpers.re:447-456", cls="tm", size=11)
    s.box(556, 88, 408, 38, ["pattern: M (the ascription stripped)"], cls="bx g", align="start")
    s.box(556, 134, 408, 38, ["def: def_elab_direct, unwrapped"], cls="bx a", align="start")
    s.box(556, 180, 408, 38, ["body_elab, the same"], cls="bx", align="start")
    s.arrow([(462, 134), (538, 134)], cls="ar a x", marker="m-a")
    s.text(500, 124, "swap", cls="ta", anchor="middle", size=11)
    s.text(20, 266, "dropped from the let's elaboration:", cls="tb", size=12)
    x = 20
    for t in ["the ascription: no sealing at run time", "label alignment", "the function's name",
              "a FixF, when def names M"]:
        w = s.chip(x, 278, t, cls="bx r", size=11, h=24)
        x += w + 10
    s.box(20, 318, 960, 58, ["why it matters on dev: under a one-member signature the let would wrap the module as "
                             "(x = whole module); dev's test", "module M : { let x : Int } = { let x = 42 } in M.x "
                             "gives 42 only because of the swap (Test_Evaluator_Modules.re:123-129)"],
          cls="bx", size=12, align="start")
    return s.render()


# ------------------------------------------------------------------ 10. members
def members():
    s = Svg("fig-members", 1000, 420,
            "How a module's members reach the code after it: the module body is lowered to a type alias and let "
            "chain ending in a labeled tuple; the binding puts a variable M of the tuple's type and a type alias M "
            "for its type members in the context; M.x is a labeled-tuple projection, and M.T a type projection "
            "through the alias.", minw=780)
    s.box(20, 30, 230, 110, ["module M = {", "  type T = Int;", "  let x : T = 1", "} in M.x"], cls="bx k",
          mono=True, align="start")
    s.box(285, 30, 270, 110, ["type T = Int in", "let x : T = 1 in", "(x = x)"], cls="bx", mono=True,
          align="start", title="lowered (ModuleHelpers 286-337)", size=12)
    s.arrow([(250, 85), (283, 85)])
    s.text(267, 78, "lower", cls="tm", anchor="middle", size=10)
    s.box(590, 30, 390, 110, ["value: VarEntry M : (x = Int)", "type: TVarEntry M = (T = Int), an alias",
                              "at run time: M = (x = 1), a labeled tuple"],
          title="the body's context and value", cls="bx a", align="start")
    s.arrow([(555, 85), (588, 85)], cls="ar a", marker="m-a")
    chain1 = [("M.x", "bx k", True), ("M parses as a constructor; the newest\nbinding is a variable: Var M", "bx", False),
              ("Dot: find label x in the\nproduct type (Statics 1278-1420)", "bx", False),
              ("run time: project field x\n(Transition 1024-1058)", "bx b2", False)]
    chain2 = [("M.T", "bx k", True), ("ProdProjection(Var M, T)", "bx", False),
              ("weak_head_normalize: lookup_alias M,\nthen project T (Typ.re:481-500)", "bx", False)]
    for row, chain in enumerate([chain1, chain2]):
        y = 190 + row * 110
        x = 20
        widths = [80, 300, 250, 220] if row == 0 else [80, 220, 330]
        for (t, c, mono), w in zip(chain, widths):
            s.box(x, y, w, 70, t.split("\n"), cls=c, mono=mono, size=12 if mono else 11)
            if x > 20:
                s.arrow([(x - 26, y + 35), (x - 2, y + 35)])
            x += w + 28
    s.text(20, 405, "a capitalized name parses as a constructor; Statics.re:1561-1597 turns it into the variable "
           "when a variable is its newest binding", cls="tm", size=11)
    return s.render()


# ------------------------------------------------------------------ 11. the PR's flow
def pr_flow():
    s = Svg("fig-pr-flow", 1000, 640,
            "Before and after flow of the ModuleExp case. Shared: the binding is expanded to a let, whose real "
            "pass records an Info at the definition's id with elaboration E. Before (dev): the definition is "
            "analyzed again directly and its Infos overwrite the let's. After (#2651): if the let's elaboration "
            "has a FixF, or no Info was recorded, the direct pass runs as before; otherwise E is read back with no "
            "pass. Below, a timeline of writes at the definition's ids.", minw=800)
    s.box(250, 12, 500, 36, ["module M = def in body"], cls="bx k", mono=True)
    s.box(250, 66, 500, 38, ["expanded = Let(M, def, body), with the ModuleExp's id (2736-2742)"], cls="bx")
    s.box(250, 122, 500, 56, ["the let case: recursion probe (map dropped), then the", "real pass: an Info at def's id, "
                              "whose elab_term is E"], cls="bx a")
    s.arrow([(500, 48), (500, 64)])
    s.arrow([(500, 104), (500, 120)])
    s.text(20, 216, "before: dev at 962a7cb009", cls="tr tb", size=13)
    s.text(530, 216, "after: #2651 at 29c08fd8fa", cls="tg tb", size=13)
    s.line(500, 196, 500, 470, cls="grid")
    s.arrow([(400, 178), (400, 228)])
    s.arrow([(740, 178), (740, 228)])
    s.box(20, 230, 450, 74, ["the whole definition, every node again,", "against S or syn: its Infos overwrite the let's"],
          title="go(def) again, directly (2757-2762)", cls="bx r")
    s.box(20, 330, 450, 40, ["def_elab_direct = E′ (equal to E but for one corner)"], cls="bx")
    s.box(20, 400, 450, 40, ["moduleexp_elab(E′), add (2763-2772)"], cls="bx")
    s.arrow([(245, 304), (245, 328)])
    s.arrow([(245, 370), (245, 398)])
    s.box(530, 230, 450, 56, ["names_itself: is the let's elaboration", "Let(_, FixF(_), _)? (2770-2774)"], cls="bx w")
    s.box(530, 316, 215, 70, ["no: InfoExp at", "rep_id(def): E,", "no pass (2775-2780)"], cls="bx g")
    s.box(765, 316, 215, 70, ["yes, or no Info:", "go(def) directly,", "as on dev (2781-2788)"], cls="bx a")
    s.box(530, 410, 450, 40, ["moduleexp_elab(E), add (2790-2799)"], cls="bx")
    s.arrow([(637, 286), (637, 314)], cls="ar g", marker="m-g")
    s.arrow([(872, 286), (872, 314)], cls="ar a", marker="m-a")
    s.arrow([(637, 386), (680, 408)])
    s.arrow([(872, 386), (830, 408)])
    # timeline of writes at def's ids
    s.text(20, 498, "writes at def's ids, in order", cls="tb", size=12)
    for row, (lab, last, lc) in enumerate([("dev", "direct pass: writes B, which wins", "r"),
                                           ("#2651", "lookup: reads A's elab_term", "g")]):
        y = 532 + row * 50
        s.text(20, y + 5, lab, cls="tb", size=12)
        s.line(90, y, 975, y, cls="grid")
        s.box(110, y - 17, 220, 34, ["probe: map dropped, no write"], cls="bx d", size=11)
        s.box(380, y - 17, 230, 34, ["real pass: writes A"], cls="bx a", size=11)
        s.box(660, y - 17, 300, 34, [last], cls=f"bx {lc}", size=11)
    return s.render()


# ------------------------------------------------------------------ 12. the self-naming guard
def selfnaming():
    s = Svg("fig-selfnaming", 1000, 340,
            "How module F = fun x -> F(x) in 1 goes: the let takes the recursive path with F in scope, so it "
            "records no error, and wraps the definition in a FixF; the first commit read that Info back and lost "
            "the error; the second sees the FixF and analyzes the definition directly in the outer context, where "
            "F is a free constructor, an error. Alexander's suggested follow-up: tell the let not to try the "
            "recursive case.", minw=780)
    s.box(20, 16, 340, 34, ["module F = fun x -> F(x) in 1"], cls="bx k", mono=True)
    s.box(20, 82, 280, 92, ["one variable, one function:", "the recursive path, F in scope;", "no error at F"],
          title="the let (2023-2248)", cls="bx")
    s.box(340, 82, 300, 92, ["requires_fixf: the elab is", "Let(F, FixF(F, def), 1); F is", "dropped from def's co_ctx"],
          title="F is used in def", cls="bx w")
    s.box(680, 82, 300, 92, ["tell the let not to try the", "recursive case for a module", "binding: no FixF to check"],
          title="Alexander's suggestion", cls="bx b2")
    s.arrow([(190, 50), (160, 80)])
    s.arrow([(300, 128), (338, 128)])
    s.box(20, 222, 450, 82, ["reads the let's Info back:", "no error at F (lost)"],
          title="e3013b0360, the first commit", cls="bx r")
    s.box(530, 222, 450, 82, ["sees the FixF: go(def) directly, in the outer", "context, where F is a free constructor: error"],
          title="29c08fd8fa: names_itself", cls="bx g")
    s.arrow([(420, 174), (300, 220)], cls="ar r", marker="m-r")
    s.arrow([(560, 174), (680, 220)], cls="ar g", marker="m-g")
    s.text(20, 330, "the error is a FreeConstructor mark (ConstructorStaticsHelpers.re:61-64) on the F inside the "
           "definition, as on dev", cls="tm", size=11)
    return s.render()


# ------------------------------------------------------------------ 13. nesting
def nesting():
    s = Svg("fig-nesting", 1000, 384,
            "Left, module bindings nested in each other's definitions, each level multiplying the analyses of what "
            "is inside it. Right, bars on a log scale: analyses of the innermost definition at depth 1 to 4: dev "
            "3, 9, 27, 81; #2651 2, 4, 8, 16; #2603 alone 2, 4, 8, 16; both 1, 1, 1, 1.", minw=780)
    lv = ["module A = ( … ) in …", "module B = ( … ) in …", "module C = ( … ) in …", "the innermost definition"]
    for i, t in enumerate(lv):
        x, y = 20 + i * 34, 30 + i * 70
        s.box(x, y, 250, 40, [t], cls="bx a" if i == 3 else "bx", mono=i < 3, size=12)
        if i:
            s.arrow([(x - 18, y - 30), (x - 18, y + 20), (x - 2, y + 20)])
    s.box(20, 312, 300, 58, ["per level: ×3 on dev, ×2 with #2651", "or #2603 alone, ×1 with both"],
          cls="bx", size=11, align="start")
    x0, base, k = 420, 330, 122
    import math
    s.text(410, 26, "analyses of the innermost definition (log scale)", cls="tb", size=12)
    leg = [("dev", "r"), ("#2651", "w"), ("#2603 alone", "b2"), ("both", "g")]
    lx = 420
    for lab, c in leg:
        s.rect(lx, 40, 11, 11, cls=f"bar {c}", rx=2)
        s.text(lx + 15, 50, lab, size=11)
        lx += 30 + tw(lab, 11)
    for v in (1, 3, 9, 27, 81):
        y = base - (math.log10(v) - math.log10(0.5)) * k
        s.line(400, y, 980, y, cls="grid")
        s.text(396, y + 4, str(v), cls="tm", anchor="end", size=10)
    data = {1: (3, 2, 2, 1), 2: (9, 4, 4, 1), 3: (27, 8, 8, 1), 4: (81, 16, 16, 1)}
    for d in range(1, 5):
        g = x0 + (d - 1) * 140 + 8
        for j, (v, c) in enumerate(zip(data[d], ["r", "w", "b2", "g"])):
            h = (math.log10(v) - math.log10(0.5)) * k
            x = g + j * 27
            s.rect(x, base - h, 23, h, cls=f"bar {c}", rx=2)
            s.text(x + 11.5, base - h - 4, str(v), anchor="middle", size=10)
        s.text(g + 52, 352, f"depth {d}", cls="tm", anchor="middle", size=11)
    s.line(400, base, 980, base, cls="ar thin")
    return s.render()


# ------------------------------------------------------------------ 14. counts by shape
def passes():
    s = Svg("fig-passes", 980, 262,
            "Analyses of a module binding's definition for three kinds of definition and four builds, drawn as "
            "unit blocks. A module literal: dev 3, #2651 2, #2603 2, both 1. A function that does not name the "
            "module: 5, 4, 2, 1. A function that names it: 5, 5, 4, 4.", minw=760)
    cols = [("dev", 400, "r"), ("#2651", 545, "w"), ("#2603 alone", 690, "b2"), ("#2651 + #2603", 835, "g")]
    for t, x, c in cols:
        s.text(x, 28, t, cls="tb", size=12)
    rows = [("module M = { … } in body", "a module literal: never recursive", (3, 2, 2, 1)),
            ("module F = fun x -> x + 1 in F(2)", "a function that does not name F", (5, 4, 2, 1)),
            ("module F = fun x -> F(x) in 1", "a function that names F", (5, 5, 4, 4))]
    for i, (code, sub, vals) in enumerate(rows):
        y = 50 + i * 68
        s.text(14, y + 18, code, mono=True, size=12, maxw=370)
        s.text(14, y + 38, sub, cls="tm", size=11)
        for (t, x, c), v in zip(cols, vals):
            for u in range(v):
                s.rect(x + u * 19, y + 6, 15, 15, cls=f"bar {c}", rx=2)
            s.text(x + v * 19 + 4, y + 19, str(v), cls="tb", size=12)
        s.line(10, y + 56, 970, y + 56, cls="grid")
    s.text(14, 254, "each block is one full analysis of the definition; the let's recursion probe counts",
           cls="tm", size=11)
    return s.render()


# ------------------------------------------------------------------ 15. the one-member signature corner
def lift():
    s = Svg("fig-lift", 1000, 452,
            "The one-member signature corner: the module with an extra member is checked against the one-field "
            "product the signature desugars to; its own type does not match, so autolabel_singleton_tuple runs. "
            "It records the bare analysis at the definition's ids but returns the labeled tuple around the raw "
            "source. Dev's direct pass used what it returns, so M.x was the raw module; #2651 reads what it "
            "records, so M.x is 1. Alexander: dev's result is a bug.", minw=800)
    s.box(20, 16, 460, 52, ["module M : { let x : Int } =", "  { let x = 1; let y = 2 } in M.x"], cls="bx k",
          mono=True, align="start")
    s.box(520, 16, 460, 52, ["the definition is checked against (x : Int):",
                             "the signature desugared to a one-field product"], cls="bx")
    s.arrow([(480, 42), (518, 42)])
    s.box(250, 96, 500, 52, ["its own type (x : Int, y : Int) is not (x : _), so", "autolabel_singleton_tuple runs (Statics.re:310-358)"],
          cls="bx w")
    s.arrow([(750, 68), (650, 94)])
    s.box(20, 184, 450, 74, ["(x = raw source), not elaborated:", "the module as written"],
          title="what it RETURNS (line 358)", cls="bx w")
    s.box(530, 184, 450, 74, ["the bare analysis against Int, whose elab_term", "is the module's own elaboration"],
          title="what it RECORDS at def's ids (357)", cls="bx a")
    s.arrow([(380, 148), (245, 182)])
    s.arrow([(620, 148), (755, 182)])
    s.box(20, 290, 450, 74, ["M = (x = { let x = 1; let y = 2 })", "M.x = the module's raw source"],
          title="dev: the direct pass gets what it returns", cls="bx r")
    s.box(530, 290, 450, 74, ["M = (x = 1, y = 2)", "M.x = 1, pinned by the PR's new test"],
          title="#2651: the read-back gets what it records", cls="bx g")
    s.arrow([(245, 258), (245, 288)], cls="ar r", marker="m-r")
    s.arrow([(755, 258), (755, 288)], cls="ar g", marker="m-g")
    s.box(20, 386, 960, 54, ["dev's result is a bug, from the auto-labelling of one-member tuples; the program "
                             "should give 1 or be stuck,", "so #2651's 1 is a fix"],
          title=None, cls="bx a", align="start")
    s.text(30, 380, "Alexander, 2026-10-21", cls="ta tb", size=11)
    return s.render()


def lift_bare():
    s = Svg("fig-lift-bare", 1000, 214,
            "The same corner with a plain value: module M : { let x : Int } = 5 in M.x. On dev the direct pass "
            "returns (x = 5), so M.x is 5 with no static error; with #2651 M is bound to 5 and M.x is stuck, traced "
            "in the code, not run.", minw=780)
    s.box(300, 12, 400, 38, ["module M : { let x : Int } = 5 in M.x"], cls="bx k", mono=True, size=12)
    s.box(20, 82, 450, 52, ["the direct pass returns (x = 5): M = (x = 5),", "M.x = 5, and no static error"],
          cls="bx g", title=None)
    s.box(530, 82, 450, 52, ["the read-back gets the bare 5: M = 5, and", "M.x is stuck: a Dot on an Int (traced, not run)"],
          cls="bx r")
    s.text(245, 76, "dev", cls="tb", anchor="middle", size=12)
    s.text(755, 76, "#2651", cls="tb", anchor="middle", size=12)
    s.arrow([(420, 50), (300, 62)])
    s.arrow([(580, 50), (700, 62)])
    s.box(20, 154, 960, 46, ["Alexander expects a module bound to something that is not a module to be a static error: "
                             "a question for Cyrus"], cls="bx w", align="start", size=12)
    return s.render()


# ------------------------------------------------------------------ 16. where #2651 sits
def landscape():
    s = Svg("fig-landscape", 1000, 360,
            "Where #2651 sits: under #2609's finding 7; beside #2603, with which it merges cleanly and brings a "
            "module binding to one analysis; #2675, #2661 and #2681 touch other parts of statics; #2689 pins the "
            "counts; Modules II keeps the direct pass and conflicts on one line in parts 2 to 9; the livelits "
            "branches carry the read-back without the self-naming guard.", minw=780)
    s.box(300, 12, 400, 40, ["#2609, finding 7: statics re-analyzes whole subterms"], cls="bx b2")
    s.box(380, 150, 240, 56, ["a module's definition", "analyzed once"], title="#2651", cls="bx a")
    s.arrow([(500, 52), (500, 148)], cls="ar b2", marker="m-2")
    left = [("#2603: a let analyzed once", "clean; together: 1 analysis", "bx g"),
            ("#2675: reuse around a recursive let", "touches the let's co_ctx only", "bx"),
            ("#2661, #2681: type hash, typed values", "independent", "bx"),
            ("#2679: merged on 10-19", "the only dev change since the base", "bx k")]
    right = [("#2689 (draft): pass budgets", "has #2651 at e3013b0360", "bx"),
             ("Modules II, #2493 to #2510", "one-line conflict, parts 2 to 9", "bx w"),
             ("#2635, #2597: livelits branches", "read-back without the guard", "bx"),
             ("DefStatics, #2469: per definition", "the walk inside one is the same", "bx k")]
    for i, (t, l, c) in enumerate(left):
        y = 70 + i * 70
        s.box(20, y, 300, 52, [l], title=t, cls=c, size=11)
        s.line(378, 178, 322, y + 26, cls="ar thin" + (" g" if i == 0 else ""))
    for i, (t, l, c) in enumerate(right):
        y = 70 + i * 70
        s.box(680, y, 300, 52, [l], title=t, cls=c, size=11)
        s.line(622, 178, 678, y + 26, cls="ar thin" + (" w" if i == 1 else ""))
    return s.render()


ALL = {
    "a_passes": a_passes, "a_infomap": a_infomap, "a_nesting": a_nesting, "a_lift": a_lift,
    "a_guard": a_guard, "a_merge": a_merge, "a_questions": a_questions,
    "subsystems": subsystems, "ids": ids, "roundtrip": roundtrip, "worker": worker, "walk": walk,
    "info": info, "let": let, "module_steps": module_steps, "moduleexp_elab": moduleexp_elab,
    "members": members, "pr_flow": pr_flow, "selfnaming": selfnaming, "nesting": nesting,
    "passes": passes, "lift": lift, "lift_bare": lift_bare, "landscape": landscape,
}
