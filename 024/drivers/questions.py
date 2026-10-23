"""The questions for Alexander, as shown in #questions-for-alexander: the five
questions handed to the writer (premise and need already checked), with
Alexander's answers of 2026-10-21 where he gave one (relayed by Matthew,
paraphrased here)."""
from links import *

PR2651 = "https://github.com/hazelgrove/hazel/pull/2651"


def c(s):
    return f"<code>{s}</code>"


QUESTIONS = [
    {
        "slug": "one-member-signature-lift",
        "short": "the one-member signature lift",
        "question": ("Alexander, on dev should " + c("module M : { let x : Int } = 5 in M.x") +
                     " keep evaluating to 5? If so, #2651 must not read back the bare analysis whenever statics lifted "
                     "the definition into a one-member signature: either it skips the read-back there, or "
                     + c("autolabel_singleton_tuple") + " first records what it returns. Either way it gives up the new "
                     "result its evaluator test pins for " + c("module M : { let x : Int } = { let x = 1; let y = 2 } in M.x") + "."),
        "tags": [("answered", "ans")],
        "blocks_merge_given": True,
        "answer": ("<b>Answered, Alexander, 2026-10-21:</b> dev's result for the module with an extra member (its "
                   "unelaborated source) is a bug, which comes from the auto-labelling of one-member tuples; that "
                   "program should evaluate to 1, or be stuck. So #2651's 1 is a correct result: the behaviour change "
                   "fixes a dev bug, and the PR's test pins the fix."),
        "after": ("<b>What the answer leaves (our reading).</b> It settles the extra-member half, so the first option "
                  "below, drafted before the answer, would undo a fix and is withdrawn. The bare-value half is a "
                  "different program: dev gives 5 with no static error, and #2651, by our reading of the code (not "
                  "run), leaves " + c("M.x") + " stuck ([[fig-lift-bare]]). Alexander expects a "
                  "module bound to something that is not a module to be a static error, which is a question for Cyrus "
                  "(<a href=\"#for-cyrus\">below</a>); if Cyrus agrees, that program becomes an error and the stuck run "
                  "does not matter. Until then it is a known change to name in the PR's description, after running "
                  "it once with the command-line tool. It does not hold up the merge."),
        "context": [
            "On dev a one-member signature desugars to a one-field labeled product. A definition whose own synthesized "
            "type has a different shape (and is not unknown) is lifted into it by " + c("autolabel_singleton_tuple") +
            ". That function records the bare definition's analysis (against the field type) at the definition's ids, "
            "but returns " + c("(x = def)") + " wrapped around the raw, unelaborated source. Dev's second, direct pass "
            "used that returned tuple, so as we read the code " + c("module M : { let x : Int } = 5 in M.x") +
            " gives 5 with no static error.",
            "The extra-member module is a static error on dev, the kind dev's tests call a limitation, and "
            + c("M.x") + " evaluated to its raw source. #2651 reads back the recorded bare analysis instead: the "
            "extra-member module now gives " + c("M.x = 1") + ", which the PR keeps and pins with a test named "
            "'runs as itself'. For the bare value, though, " + c("M") + " becomes 5 and " + c("M.x") +
            " gets stuck, because projecting a label out of an Int is indeterminate (traced in the code, not run).",
            "From part 1 (" + pr(2493, "first-class signature types") + ") on, a signature stays a Sig type and is "
            "never lifted this way, and your stack seals the extra-member module to " + c("{ let x = 1 }") +
            ". So this question is about dev only, until your stack lands.",
        ],
        "evidence": [
            ("After a synthesis pass, every expression analyzed against a type that weak-head-normalizes to a one-field "
             "labeled product goes through " + c("autolabel_singleton_tuple") + ", except when its own type is a "
             "one-field product with that same label, or unknown.", [d(S, 2778, 2791)]),
            ("It analyzes a fresh copy against the field type and returns the surface tuple " + c("(l = e)") +
             " around the raw source. It writes the lifted info and then the bare info under the same ids (rewrap "
             "keeps the ids), so the info left at the definition's id is the bare analysis: what it records and what "
             "it returns differ.", [d(S, 310, 358), d(S, 312, 321), d(S, 329, 334), d(S, 356, 357), d(IDT, 158, 164)]),
            (c("mpat_to_pat") + " desugars " + c("{ let x : Int }") + " to the one-field product " + c("(x = Int)") +
             ": the direct pass's " + c("def_ana") + ", and the type the let analyzes def against.",
             [d(MH, 51, 60), d(TYP, 615, 646), d(S, 2079)]),
            ("Dev's direct pass analyzes def against that product, so the term it hands " + c("moduleexp_elab") +
             " is " + c("(x = 5)") + ", or " + c("(x = raw module)") + " for the extra-member case.", [d(S, 2757, 2764)]),
            ("#2651 takes " + c("elab_term") + " from the InfoExp at " + c("rep_id(def)") + ": on this path the bare "
             "inner analysis, 5, or the module's own elaboration without the label.", [p(S, 2775, 2780)]),
            (c("moduleexp_elab") + " strips the binder's signature, so nothing wraps or seals the definition again at "
             "run time.", [d(MH, 447, 456), d(MH, 364, 371)]),
            ("When Dot meets an Int (a value of the wrong form: not a tuple, and not a list, which Dot maps over), "
             "unboxing gives IndetMatch and the step is Indet, so " + c("M.x") + " stays stuck.",
             [d(TR, 1024, 1087), d(UB, 184, 217)]),
            ("The lift is meant for plain lets: " + c('let x : (l=String) = "a" in x') + " elaborates to "
             + c('(l="a")') + ".", [d(TEL, 386, 399)]),
            ("Dev's statics tests call an extra member a limitation that 'should pass with full modules': it is an "
             "error only because modules desugar to products.", [d(TSM, 373, 387)]),
            ("The new test asserts " + c("M.x = 1") + "; its comment calls the program an error in statics that still "
             "runs as the module, and its name says it 'runs as itself'.", [p(TEM, 86, 96)]),
            ("The PR description says that on dev " + c("M.x") + " evaluates to the module's unelaborated source and "
             "with #2651 " + c("M") + " to " + c("(x=1, y=2)") + ", kept since the new result looks like the right "
             "one. It does not mention a non-module definition.",
             [f'<a href="{PR2651}">#2651\'s description</a> (read 2026-10-21)']),
            ("From part 1 on, " + c("mpat_to_pat") + " keeps the raw signature (no " + c("desugar_sig") + "), and "
             + c("weak_head_normalize") + " has no Sig case, so a signature-ascribed module is never lifted; part 3 "
             "also rejects a product annotation on a module.",
             [at(M1, MH, 47, 56), at(M3, MH, 47, 56), at(M3, TYP, 675, 738), at(M3, TSM, 1657, 1662)]),
            ("In part 1, " + c("module M : { let x : Int } = { let x = 1; let y = 2 } in M") + " evaluates to "
             + c("{ let x = 1 }") + ".", [at(M1, TEM, 196, 202)]),
            ("Your docs make " + c("module M : S = e") + " a coercion site, where extra members are sealed away and "
             "the run-time value keeps only the signature's members.", [at(M9, DOC, 82, 90)]),
        ],
        "options": [
            ("Yes, keep dev's results. Skip the read-back when the lift ran: narrowly, when the info recorded at def's "
             "id was analyzed against the field type rather than " + c("def_ana") + "; more simply and a little "
             "dearer, whenever " + c("def_ana") + " is a one-field labeled product. #2651 then changes neither result "
             "the review found. Replace its evaluator test with " + c("module M : { let x : Int } = 5 in M.x") +
             " giving 5, and take 'runs as itself' out of the test and the description. The stuck result was traced, "
             "not run: run that program with the command-line tool at dev and at the PR head first.",
             "recommended before the answer; withdrawn: it would undo the fix Alexander confirmed"),
            ("No: dev need not support a module bound to a non-module value, since Modules II makes it a type error, "
             "so #2651 can merge as it is. Keep only the assertion " + c("M.x = 1") + ", which holds on dev with #2651 "
             "and on your stack. Reword the test's name and comment, and the PR description, to say only what holds "
             "on both: " + c("M.x") + " is the member, not the module's raw source; dev still reports a type error "
             "there (the module's type against the field type Int) and does not seal; Modules II seals.",
             "fits the answer: recommended now, with the bare-value program named in the description"),
            ("Fix the cause in a separate PR: make what " + c("autolabel_singleton_tuple") + " records at the "
             "definition's ids agree with what it returns. #2651 would then need no special case, but the "
             "extra-member module's " + c("M.x") + " would become the whole elaborated module, not 1.", ""),
        ],
    },
    {
        "slug": "merge-order-with-modules-ii",
        "short": "the merge order against Modules II",
        "question": ("Alexander, can #2651 merge into dev ahead of your Modules II stack, with the one-line conflict in "
                     "parts 2 to 9 resolved by keeping its read-back and adding " + c("~coercible=true") + " to its "
                     "fallback? That resolution is right only if, on your branches, the let's recorded analysis of the "
                     "definition is the same analysis as the direct pass it replaces."),
        "tags": [("open", "open"), ("settle before merging", "block")],
        "blocks_merge_given": True,
        "answer": None,
        "after": None,
        "context": [
            "On dev, " + c("module M = def in body") + " is checked as " + c("let M = def in body") + ", and ModuleExp "
            "then analyzes def a second time, directly, only to get its elaboration. #2651 reads that elaboration back "
            "from the info the let recorded at def's id and keeps the direct pass only as a fallback. Your "
            + pr(2494, "part 2, sealing at explicit coercion sites") + " changed that same direct-pass line to pass "
            + c("~coercible=true") + ", so #2651 conflicts on exactly that line with each of parts 2 to 9, while it "
            "merges cleanly into dev, part 1 and " + pr(2603, "a let is analyzed once unless it refers to itself") + ".",
            "As we read your branches, both passes check def against the same type with the same flag: from part 2 "
            "every analysis of a let's definition is a coercion site, and from part 1 the binder keeps its raw "
            "signature. Two other differences look harmless there. The let's recursive path has the module's name in "
            "scope, which matters only when def uses it, and then the let builds a fixpoint and #2651 falls back. And "
            "the read-back is what was recorded at def's id, not what the analysis returned; the two differ only when "
            "the expected type is a one-member labeled tuple, which is what a one-member signature desugars to on "
            "dev, but not on your branches, where a signature stays a signature type. You would know whether sealing "
            "or abstract type members make the two passes differ anywhere else.",
        ],
        "evidence": [
            ("On dev, after checking the expanded let, the ModuleExp case analyzes the definition again, directly, to "
             "get " + c("def_elab_direct") + ".", [d(S, 2757, 2762)]),
            ("#2651 reads " + c("def_elab_direct") + " from the InfoExp the let recorded at " + c("Exp.rep_id(def)") +
             ". It falls back to the direct analysis, as on dev (no " + c("~coercible") + " exists there), when the "
             "let's elaboration is " + c("Let(_, FixF(_), _)") + " or no InfoExp was recorded.", [p(S, 2770, 2789)]),
            ("Part 2 changed the direct analysis to " + c("go(~ana=def_ana, ~coercible=true, def, m)") + "; the same "
             "line is still there in part 3 and at the top of the stack in part 9.",
             [at(M2, S, 2833, 2834), at(M3, S, 2853, 2854), at(M9, S, 2973, 2974)]),
            ("In part 2 the let passes " + c("~coercible=true") + " in all five analyses of the definition (the "
             "recursion probe, the non-recursive pass, and the recursive path's three), under the comment that every "
             "analysis of it is a coercion site.",
             [at(M2, S, 2152, 2155), at(M2, S, 2164, 2165), at(M2, S, 2177, 2178), at(M2, S, 2190, 2191),
              at(M2, S, 2209, 2210)]),
            (c("coercible") + " switches the expected-type check from a meet to " + c("Typ.coercion") + ", which seals "
             "a wider module.", [at(M2, SB, 265, 271)]),
            (pr(2494) + "'s description says that " + c("Asc") + ", " + c("Let") + " (all analyses of the definition), "
             + c("ModuleExp") + " and " + c("Ap") + " set " + c("~coercible") + " on their operand.",
             ['<a href="https://github.com/hazelgrove/hazel/pull/2494">#2494\'s description</a> (read 2026-10-21)']),
            ("From part 1 on, " + c("mpat_to_pat") + " keeps the raw signature (later as " + c("Pat.of_mpat") + "), "
             "and the pattern Asc case reports that annotation as its type, so the let's expected type for def is the "
             "annotation the direct pass takes as " + c("def_ana") + ".",
             [at(M1, MH, 47, 56), at(M3, MH, 47, 56), at(M9, PAT, 298, 306), at(M1, S, 3710, 3725),
              at(M3, S, 3747, 3761), at(M3, S, 2848, 2852)]),
            ("The let wraps def in a fixpoint only when it took the recursive path and def or the binder's annotation "
             "mentions the bound name (uses in the body are filtered out); otherwise a function-shaped def is read "
             "back from the recursive pass, where the name is in scope but unused.",
             [at(M2, S, 2233, 2242), d(CO, 43, 53)]),
            ("When the expected type is a one-member labeled tuple, the analysis records the inner analysis at the "
             "user's ids but returns the user's term wrapped as a one-field tuple, so what is recorded at def's id and "
             "what " + c("go") + " returns can differ.", [d(S, 310, 359), d(S, 2776, 2791)]),
            ("On dev a module signature desugars to a labeled tuple, so a one-member signature takes that path; "
             "#2651's second commit names this as the one result it changes, and a new test checks it.",
             [d(MH, 51, 60), d(TYP, 615, 646), p(TEM, 86, 96)]),
            ("On the Modules II branches a signature is a Sig type, which " + c("weak_head_normalize") + " returns "
             "unchanged, so a signature ascription does not take the one-member-tuple path.", [at(M2, TYP, 629, 690)]),
            ("Part 2's " + c("moduleexp_elab") + " keeps the binder's signature ascription, which is what seals at run "
             "time, and still swaps " + c("def_elab_direct") + " in for the let's definition.", [at(M2, MH, 617, 627)]),
            ("A three-way merge of 29c08fd8fa with each part (merge base 34f9605ddf; every part contains dev "
             "962a7cb009) gives exactly one conflict, in " + c("Statics.re") + " on that line, for each of parts 2 to "
             "9, and none for part 1; it also merges cleanly with dev and with #2603's head 4aa493c05a.",
             ["<code>git merge-tree</code> (run 2026-10-21; parts 1, 2 and 9 and dev re-run for this report)"]),
            ("Separately, #2603 conflicts with every part, 1 to 9 (TyDiCtx.re, Ctx.re and StaticsBase.re, plus "
             "Statics.re from part 2 on). That belongs to #2603's review, not #2651's.",
             ["<code>git merge-tree</code> of 4aa493c05a with each part (run 2026-10-21)"]),
            ("No one has reviewed or commented on #2651 yet: the only comment is the codecov report, and the checks "
             "are green.", ["GitHub's reviews, review comments, comments and check runs for #2651 (read 2026-10-21)"]),
        ],
        "options": [
            ("Merge #2651 into dev now. When your stack next rebases, keep the read-back and add "
             + c("~coercible=true") + " to the fallback's " + c("go") + " call in parts 2 to 9. Matthew can send you "
             "the resolved hunk.", "recommended"),
            ("Merge parts 1 to 3, or the whole stack, first. Matthew then rebases #2651 onto it with "
             + c("~coercible=true") + " in the fallback and reruns the Statics.Modules and Evaluator.Modules groups "
             "there.", ""),
            ("Merge #2651 now. If ModuleExp on your stack can use the let's elaboration as is (see "
             "<a href=\"#q-def-elab-direct-on-modules-ii\">question 4</a>), remove the direct pass there altogether, "
             "so the conflict resolves by deleting both sides.", ""),
            ("Hold #2651 until you have decided whether ModuleExp keeps " + c("def_elab_direct") + " in Modules II.", ""),
        ],
    },
    {
        "slug": "are-module-bindings-recursive",
        "short": "whether module bindings are recursive",
        "question": ("Alexander, are module bindings meant never to be recursive, items inside " + c("{ … }") +
                     " included, and if so, would you rather the module expansion tell the let that it is not "
                     "recursive than have ModuleExp spot self-reference from the fixpoint in the let's elaboration, as "
                     "#2651 now does?"),
        "tags": [("answered for now", "now"), ("for Cyrus", "cyrus")],
        "blocks_merge_given": False,
        "answer": ("<b>Answered for now, Alexander, 2026-10-21:</b> whether modules should be recursive is not "
                   "settled. For now it is fine for them not to be recursive by default, since recursion has a number "
                   "of known correctness problems; whether they should be is a question for Cyrus. On the signal: "
                   "Modules II has none for this, and he did not write the original module keyword; as things stand a "
                   "module binding is a let that is not recursive. His suggestion is an argument on the let analysis "
                   "saying whether to check the recursive case, so that a module binding is never analyzed recursively."),
        "after": ("<b>What the answer settles (our reading).</b> #2651's statics test, which pins the expression form "
                  "as not recursive, matches the current intent; a " + c("module") + " item inside a module body, "
                  "which is lowered to a plain let and so is recursive, stays as it is until Cyrus decides. His "
                  "suggestion is the flag of the first option: with it the let reports a self-reference as unbound by "
                  "itself, " + c("names_itself") + " and its fallback are not needed, and a module binding skips the "
                  "let's recursion probe as well. It can go in #2651 or a follow-up (<a href=\"#next\">What next</a>)."),
        "context": [
            "A module binding " + c("module F = def in body") + " is checked as " + c("let F = def in body") + ". The "
            "let treats a definition that is one function of arrow-like type as possibly recursive: it analyzes def "
            "with F in scope, and wraps it in a fixpoint (FixF) only if def uses F. On dev, "
            + c("module F = fun x -> F(x) in 1") + " is an error only because ModuleExp then analyzed def a second "
            "time in the outer scope, where " + c("F") + " is a free constructor; that pass's infos, with no F in "
            "scope, were also what the editor saw inside def.",
            "#2651 keeps the let's infos and reruns the old pass only when the let's elaboration is "
            + c("Let(_, FixF, _)") + " (or def has no recorded info), so that error stays; but inside a function-valued "
            "module that does not name itself, the context at the caret now contains F, so completion offers F wherever "
            "its type fits, and picking it brings the error back. #2603 accepts a related editor-visible difference "
            "for lets, but there the binder was already in scope inside its own function on dev, and only its type "
            "there changes. Meanwhile a " + c("module F = …") + " item inside " + c("{ … }") + " is lowered to a plain "
            "let with no such pass, so by our reading it is recursive with no error, on dev and all through the "
            "Modules II stack, and no test or doc binds a module to a function.",
        ],
        "evidence": [
            (c("is_recursive") + " looks only at the shape of the code: one bound variable and one function of "
             "arrow-like type count as recursive, whether or not the name is used.", [d(S, 2024, 2039), d(S, 2076)]),
            ("On the recursive path the let analyzes def in " + c("def_ctx") + ", where the bound name is in scope at "
             "def's synthesized type, and records those infos.", [d(S, 2090, 2122)]),
            ("A fixpoint is used only when def (or the pattern's types) uses the bound name; the body's uses are "
             "dropped by " + c("CoCtx.mk") + ". The let then removes the name from the co_ctx of def's info, so that "
             "info cannot show the self-reference.",
             [d(S, 2172, 2181), d(S, 2200, 2206), d(S, 2216, 2228), d(CO, 43, 53)]),
            ("The let's own co_ctx still contains the name when def uses it, because it unions the unpatched "
             + c("def.co_ctx") + ": a check on " + c("expanded_info.co_ctx") + " would also work as a signal.",
             [d(S, 2231, 2240)]),
            ("Dev's direct pass analyzed def in the outer context after the let and overwrote def's infos. There "
             + c("F") + " is not a variable, so it elaborates as a constructor with a FreeConstructor mark: the error "
             "the fallback still reports.", [d(S, 2757, 2762), d(S, 1598, 1606), d(CSH, 61, 64)]),
            ("#2651's signal is the shape of the let's elaboration; the direct pass also runs when def has no recorded "
             "InfoExp. Its new test's comment says 'modules are not recursive'.",
             [p(S, 2770, 2774), p(S, 2775, 2789), p(TSM, 406, 413)]),
            ("ModuleExp's elaboration replaces the let's def with the direct (dev) or read-back (#2651) elaboration, so "
             "a FixF the let built is dropped either way.", [d(MH, 448, 456), p(S, 2764, 2769), p(S, 2790, 2791)]),
            ("Completion offers the context's variables, at the Info under the caret, whose type is consistent with "
             "the expected type.", [d(TYDI, 28, 39), d(TYDI, 192, 201)]),
            ("A " + c("module F = def") + " item inside a module body is lowered to a plain Let with no fallback, on dev "
             "and on every Modules II part; the item's elaboration keeps the let's FixF.",
             [d(MH, 300, 304), d(MH, 442, 445), at(M3, MH, 265, 271), at(M9, MH, 268, 274), at(M9, MH, 642, 651)]),
            ("#2603 keeps the probe's analysis for a function that does not mention its binders and whose binders "
             "shadow nothing, with the binder in scope at its synthesized type, and calls that an accepted "
             "editor-visible difference. On dev the binder was already in scope there.",
             [at(T2603, S, 2079, 2089), at(T2603, S, 2108, 2119), d(S, 2091, 2102), d(S, 2121)]),
            ("The only module bound to a function anywhere in the tree is #2651's self-naming test, and part 9 has none.",
             ["<code>git grep</code> over the whole tree at 29c08fd8fa and b02ce6dab5 (run 2026-10-21)"]),
            (pr(2493) + " lists 'No mutually recursive modules' among its limitations and says nothing about a module "
             "binding that names itself.",
             ['<a href="https://github.com/hazelgrove/hazel/pull/2493">#2493\'s description</a> (read 2026-10-21)']),
        ],
        "options": [
            ("Never recursive, at either level, as in OCaml without " + c("module rec") + ". Merge #2651 with the FixF "
             "check now, then follow up with a 'not recursive' flag on the let, set by ModuleExp and by the item "
             "lowering (for " + c("module") + " items only, not " + c("let") + " items). With it the let skips the "
             "recursion probe and passes and analyzes def once, in the outer scope, so the error and the editor's "
             "context both come out right, and " + c("names_itself") + " and the fallback go away.",
             "recommended; matches Alexander's suggestion (the item form waits for Cyrus)"),
            ("Keep the FixF shape check as the long-term signal, and add a comment where the let builds its FixF "
             "saying that ModuleExp depends on that shape.", ""),
            ("Use the module's own name in " + c("expanded_info.co_ctx") + " as the signal instead. It also fires when "
             "def uses an outer binding of the same name, which then only costs the old extra pass.", ""),
            ("Recursive like " + c("let") + ", at both levels: #2651's fallback and its new statics test go away, and "
             "ModuleExp's elaboration must take the let's FixF (dev's direct pass and #2651's read-back both drop it), "
             "so the module can call itself at run time.", ""),
            ("Keep dev's split for now (not recursive as an expression, recursive as an item) and decide in a later "
             "Modules II part.", "the state for now, until Cyrus decides"),
        ],
    },
    {
        "slug": "def-elab-direct-on-modules-ii",
        "short": "whether Modules II still needs def_elab_direct",
        "question": ("Alexander, on your stack does ModuleExp still need its separate analysis and elaboration of the "
                     "definition (" + c("def_elab_direct") + ", which " + c("moduleexp_elab") + " swaps in for the "
                     "let's), or could a module binding use the let's elaboration as is, as your "
                     + c("docs/modules.md") + " already says it does?"),
        "tags": [("open", "open")],
        "blocks_merge_given": False,
        "answer": None,
        "after": None,
        "context": [
            c("moduleexp_elab") + " builds the binding's run-time term from the let's elaboration, with "
            + c("def_elab_direct") + " (from a second analysis of the definition in the outer context) in place of the "
            "let's definition. That drops what the let wraps around a definition: label alignment, the function's "
            "name, and, for a recursive function that refers to itself, a fixpoint. On dev, alignment is why the swap "
            "matters for a module literal: a module elaborates to a let-chain and a one-member signature desugars to a "
            "one-field product, so the let would wrap the module as " + c("(x = whole module)") + ", and "
            + c("module M : { let x : Int } = { let x = 42 } in M.x") + " gives 42 only because of the swap.",
            "On your stack a signature stays a Sig type, which alignment leaves alone; a module literal elaborates to a "
            "Module value; the name touches only functions; and a module literal is never treated as recursive. So "
            "for a module literal the let's elaboration already is the direct one. What is left is a definition that "
            "is a function naming its own module (" + c("module F = fun x -> F(x)") + "), where the let adds a "
            "fixpoint and, analyzing it recursively, does not report F as unbound; #2651 handles that by falling back "
            "to the direct pass, and a non-recursive module binder would remove it. The direct pass is also not part "
            "of the modules design: it arrived in April 2026 with 'delete elaborator' (" + commit(
                "cc620bbbdc4bddd93e4c61e2ff6116d7c4c5dbb4") + "), and before that ModuleExp elaborated its definition "
            "from the info map with no second analysis, which is what #2651 goes back to.",
        ],
        "evidence": [
            (c("moduleexp_elab") + " keeps the let's pattern (with its signature ascription stripped) and body, and "
             "puts " + c("def_elab_direct") + " in place of the let's definition.", [d(MH, 447, 456)]),
            ("ModuleExp analyzes the definition a second time, in the outer context, against the binder's annotation, "
             "and swaps the result in.", [d(S, 2757, 2764)]),
            ("Both of the let's paths align and name the definition's elaboration; the recursive path, when the "
             "binding refers to itself, also wraps it in a fixpoint.", [d(S, 2172, 2230)]),
            ("On dev a module binder's signature annotation is desugared to a labeled product.",
             [d(MH, 51, 60), d(TYP, 615, 657)]),
            ("Against a one-field labeled product, alignment wraps any elaboration that is not already a tuple, such "
             "as a module's let-chain, into " + c("(x = e)") + ".", [d(LTH, 49, 75), d(LTH, 108, 110)]),
            ("Dev's test that depends on the swap: " + c("module M : { let x : Int } = { let x = 42 } in M.x") +
             " evaluates to 42.", [d(TEM, 123, 129)]),
            (c("add_name") + " changes only " + c("Fun") + " and " + c("TypFun") + ".", [d(EXP, 544, 551)]),
            ("A let is treated as recursive only when its definition is a function or a tuple of functions; "
             + c("get_num_of_functions") + " returns None for a Module literal, on dev and on your stack.",
             [d(S, 2024, 2039), d(S, 2076), d(EXP, 407, 460), at(M9, S, 2241, 2256), at(M9, S, 2284),
              at(M9, EXP, 456)]),
            ("#2651 keeps the direct pass for a definition that names its own module: there the let wraps a fixpoint "
             "and analyzes the name in scope, while the direct pass reports it unbound; its test is "
             + c("module F = fun x -> F(x) in 1") + ".", [p(S, 2764, 2789), p(TSM, 409, 413)]),
            ("On your stack a module literal elaborates to a Module value.",
             [at(M3, S, 2765, 2815), at(M9, S, 2925)]),
            (c("weak_head_normalize") + " leaves a Sig as a Sig, through its fall-through case; "
             + c("LabeledTupleHelpers.re") + " is unchanged from dev through part 9, and its alignment returns a term "
             "unchanged when the expected type is not a product; a product annotation on a module is rejected from "
             "part 3.", [at(M3, TYP, 675, 739), at(M3, TYP, 737), at(M3, TSM, 1657, 1662), at(M9, LTH, 77),
                         at(M9, LTH, 104)]),
            ("Your docs say a ModuleExp is checked as " + c("Let(pat, def, body)") + " and 'elaborates to that Let'.",
             [at(M9, DOC, 496, 497)]),
            ("The code on your stack still analyzes the definition a second time (with the same "
             + c("~coercible=true") + " the let uses) and swaps it in, keeping the binder's signature for sealing.",
             [at(M9, S, 2968, 2976), at(M9, S, 2287, 2288), at(M9, MH, 671, 681)]),
            ("Before 'delete elaborator' (" + commit("cc620bbbdc4bddd93e4c61e2ff6116d7c4c5dbb4") + ", committed "
             "2026-04-17), the separate Elaborator elaborated ModuleExp's definition from the info map, with no second "
             "analysis; " + c("def_elab_direct") + " first appears in that commit.",
             [at(OLD, ELAB, 518, 524), "<code>git log -S def_elab_direct</code>"]),
            ("The info at def's id is not always what the let's analysis returned: when a definition is auto-labelled "
             "into a one-field tuple, the analysis returns " + c("(x = the unelaborated term)") + " but records the "
             "elaboration from before the label, which is why #2651's new one-member-signature test gives 1.",
             [d(S, 310, 359), d(S, 357), p(TEM, 86, 96)]),
        ],
        "options": [
            ("Nothing is left for a module literal, and for a function definition only the fixpoint and the "
             "unbound-name report (plus the harmless name). Once module binders are not recursive, a follow-up on "
             "your stack removes " + c("def_elab_direct") + ", the swap in " + c("moduleexp_elab") + " and #2651's "
             "read-back, and #2651 is then a step needed only on dev.", "recommended"),
            ("It still guarantees something else on Modules II (please say what). #2651's read-back is then the "
             "long-term shape, and its contract should be written down next to " + c("moduleexp_elab") + ": the info "
             "at def's id holds the definition's own elaboration, which is what the analysis returned, except when the "
             "definition was auto-labelled into a one-field tuple, where it holds the elaboration from before the "
             "label.", ""),
            ("Not decided yet: merge #2651 either way and revisit when the stack lands.", ""),
        ],
    },
    {
        "slug": "tests-to-pin",
        "short": "which module behaviours to pin as tests",
        "question": ("Alexander, which of these module behaviours do you want pinned as tests in #2651: the "
                     "self-naming error at its exact place, a function-valued module that does not name itself, and a "
                     "module bound to a bare value under a one-member signature?"),
        "tags": [("open", "open")],
        "blocks_merge_given": False,
        "answer": None,
        "after": ("<b>Since the answers.</b> The second needs nobody: " + c("module F = fun x -> x + 1 in F(2)") +
                  " gives 3 under any reading, so it is in <a href=\"#next\">What next</a> as a test to add. For the "
                  "third, the extra-member result (1) is settled; the bare value's waits on Cyrus. The first follows "
                  "from the recursion answer: for now the expression form is not recursive."),
        "context": [
            "#2651 adds one statics test, " + c("module F = fun x -> F(x) in 1") + ", written with "
            + c("inconsistent_typecheck") + ". That helper passes whenever the program has any static error at all, so "
            "the test would still pass if the error moved or changed kind; today the error is a FreeConstructor mark "
            "('Constructor is not defined') on the F inside the definition, because a capitalized name parses as a "
            "constructor and the fallback analysis runs without F in scope.",
            "Three paths the PR changes have no test. The first is the read-back after the let's recursive branch, "
            "which a module bound to a function takes even when it does not name itself, such as "
            + c("module F = fun x -> x + 1 in F(2)") + " (expected 3). The second is a module bound to a non-module "
            "value under a one-member signature, " + c("module M : { let x : Int } = 5 in M.x") + ", which gives 5 on "
            "dev but, as we read it, a stuck " + c("5.x") + " under #2651 unless the PR adds a guard. The third is the "
            "fallback's signature-ascribed arm, the one patch line Codecov marks as missed. These behaviours are yours "
            "to define, so we would rather pin the ones you consider part of the modules contract.",
        ],
        "evidence": [
            ("The self-naming test is an " + c("inconsistent_typecheck") + " case.", [p(TSM, 406, 413)]),
            (c("inconsistent_typecheck") + " only checks that the list of static errors is not empty; that list is "
             "every info in the statics map that carries marks.", [p(TSP, 142, 151), p(TSP, 225, 242)]),
            ("The error the fallback reports is the FreeConstructor mark at the use of F: Ap analyzes a constructor "
             "head against an arrow, " + c("syn_marks_ctr") + " finds no constructor F, and the Constructor case finds "
             "no variable F in the outer context.",
             [d(S, 1561, 1565), d(S, 1598, 1606), d(S, 1705, 1718), d(CSH, 46, 67)]),
            ("Under #2651 the self-naming case reaches the direct analysis only because the let wrapped the definition "
             "in a FixF, which " + c("names_itself") + " detects.",
             [p(S, 2172, 2181), p(S, 2202, 2206), p(S, 2229), p(S, 2770, 2789)]),
            ("A single variable bound to a function with an arrow type takes the let's recursive branch, which "
             "analyzes the definition last with the name in scope; with no self-reference no FixF is built, so the "
             "read-back is used.", [p(S, 2024, 2039), p(S, 2070, 2076), p(S, 2090, 2123), p(S, 2172, 2187),
                                    p(S, 2775, 2780)]),
            ("On dev the direct analysis passes the signature, a one-field labeled product, as the expected type, and "
             "the singleton-label lift returns the tuple " + c("(x=5)") + ".",
             [d(S, 2757, 2762), d(S, 2778, 2789), d(TYP, 615, 646)]),
            ("The lift records the tuple's info at the definition's ids, then overwrites them with the unlabeled inner "
             "info, and returns the tuple; so the PR's read-back gets 5, not " + c("(x=5)") + ".", [d(S, 310, 358)]),
            ("Projecting a label from a non-tuple value such as 5 is indeterminate, so " + c("M.x") + " is stuck.",
             [d(TR, 1024, 1086), d(UB, 185, 217)]),
            ("The PR's own evaluator test covers the same read-back for a module value with an extra member, not for "
             "a bare value.", [p(TEM, 86, 96)]),
            ("The only module bound to a function anywhere in the tests is the self-naming one, and no test binds a "
             "module to a non-module value.", ["<code>git grep</code> over test/ and docs/ at 29c08fd8fa (run 2026-10-21)"]),
            ("Codecov reports 87.5% patch coverage with one line missing: the fallback's signature-ascribed arm, "
             "which was hit on the base.", [p(S, 2784), d(S, 2759),
                                             f'<a href="{PR2651}">codecov\'s comment on #2651</a> (read 2026-10-21)']),
        ],
        "options": [
            ("(1) Pin the self-naming error to the FreeConstructor mark on F's use inside the definition; (2) add "
             + c("module F = fun x -> x + 1 in F(2)") + ", expected 3, which covers the read-back after the recursive "
             "branch; (3) add " + c("module M : { let x : Int } = 5 in M.x") + " with whatever result the "
             "one-member-signature question settles.", "recommended"),
            ("Only tighten the self-naming test now, and add the rest with Modules II.", ""),
            ("Leave the tests as they are.", ""),
        ],
    },
]

FOR_CYRUS = [
    ("cyrus-recursive", "Should module bindings be recursive?",
     "Today " + c("module F = …") + " as an expression is not (a self-reference is an error, and #2651 keeps it one), "
     "while a " + c("module F = …") + " item inside " + c("{ … }") + " is lowered to a plain let and, by our reading, "
     "is. Alexander: for now it is fine for modules not to be recursive by default, since recursion has a number of "
     "known correctness problems (<a href=\"#q-are-module-bindings-recursive\">question 3</a>)."),
    ("cyrus-non-module", "Should binding a module to something that is not a module be a static error?",
     c("module F = fun x -> 1 in F(3)") + " is accepted today, and so is " + c("module M : { let x : Int } = 5 in M.x")
     + ". Alexander expects such a binding to be an error. If it is, the bare-value program of "
     "<a href=\"#q-one-member-signature-lift\">question 1</a> becomes an error too."),
    ("cyrus-keyword", "What should the " + c("module") + " keyword add over " + c("let") + "?",
     "Alexander had favoured plain " + c("let") + " for module definitions; Cyrus wanted the keyword to do more. "
     "Today a module binding is checked as a let that is not recursive (<a href=\"#modules\">Modules</a>)."),
]
