"""Code links for ^report(24): every file:line is a link to GitHub at a full
commit id, recorded in REFS so the generator can check each range exists."""
import os

D = "962a7cb0091cad9a115f82f92433c4d6499f7135"      # dev, read 2026-10-21
P = "29c08fd8fa6126a6507ab47f4e56e8613276bf0c"      # #2651 head
E1 = "e3013b036053fbef28211eef476cb8090ee2bbda"     # #2651's first commit
MB = "34f9605ddfda9aa9e629586b31d285f98221bcc3"     # #2651's merge base with dev
M1 = "c4bae23739049d13d9dc8eacdfe5be66f9ebee0b"     # modules-ii/1-sig-types (#2493)
M2 = "be90bf4b217609cb3c0e22429715cdd436162cf6"     # modules-ii/2-width-subtyping (#2494)
M3 = "111775a60cde2fb050ae28a652b44a7b999814e5"     # modules-ii/3-abstract-types (#2495)
M9 = "b02ce6dab5eb3e4e79cbcfc29f21227415423172"     # modules-ii/9-stdlib-modules (#2510)
T2603 = "4aa493c05a8d5bc1733e7db685afd821da03bee8"  # #2603 head
ME = "b5eaa3303149d42f4d0e30f715ba6df2685f4926"     # #2469 head (Modular editors)
OLD = "a81e3188fd13665af430882c17c64f6033a53b54"    # parent of cc620bbbdc (delete elaborator)

NAMES = {D: None, P: "PR", E1: "e3013b0360", MB: "base", M1: "part 1", M2: "part 2", M3: "part 3",
         M9: "part 9", T2603: "2603 head", ME: "2469 head", OLD: "a81e3188fd"}

S = "src/language/statics/Statics.re"
MH = "src/language/statics/ModuleHelpers.re"
SB = "src/language/statics/StaticsBase.re"
INFO = "src/language/statics/Info.re"
CO = "src/language/statics/CoCtx.re"
CTX = "src/language/statics/Ctx.re"
CSH = "src/language/statics/ConstructorStaticsHelpers.re"
LTH = "src/language/statics/LabeledTupleHelpers.re"
TYP = "src/language/term/Typ.re"
EXP = "src/language/term/Exp.re"
PAT = "src/language/term/Pat.re"
IDT = "src/language/term/IdTagged.re"
EI = "src/language/dynamics/EvalInfo.re"
IE = "src/language/dynamics/IncrEval.re"
DH = "src/language/dynamics/DHExp.re"
DYN = "src/language/dynamics/Dynamics.re"
TR = "src/language/dynamics/transition/Transition.re"
UB = "src/language/dynamics/transition/Unboxing.re"
WS = "src/web/util/WorkerServer.re"
WC = "src/web/util/WorkerClient.re"
REQ = "src/web/view/EvalRequest.re"
ER = "src/web/app/editors/result/EvalResult.re"
CWS = "src/web/app/editors/code/CodeWithStatics.re"
CE = "src/web/app/editors/code/CodeEditable.re"
MAIN = "src/web/Main.re"
CS = "src/haz3lcore/derived/CachedStatics.re"
ED = "src/haz3lcore/Editor.re"
MT = "src/haz3lcore/lang/MakeTerm.re"
BASE = "src/haz3lcore/tiles/Base.re"
ZB = "src/haz3lcore/zipper/ZipperBase.re"
IND = "src/haz3lcore/zipper/action/Indicated.re"
TYDI = "src/haz3lcore/TyDi/TyDiCtx.re"
APP = "src/haz3lcore/AutoProbePerform.re"
DEFS = "src/haz3lcore/derived/DefStatics.re"
ELAB = "src/language/statics/Elaborator.re"
TEM = "test/evaluator/Test_Evaluator_Modules.re"
TSM = "test/statics/Test_Statics_Modules.re"
TSP = "test/statics/Test_Statics_Prelude.re"
TEP = "test/evaluator/Test_Evaluator_Prelude.re"
TEL = "test/Test_Elaboration.re"
DOC = "docs/modules.md"

REFS = []


def gh(commit, path, a, b=None, label=None, tag=True):
    b = b if b is not None else a
    REFS.append((commit, path, a, b))
    frag = f"#L{a}" + (f"-L{b}" if b != a else "")
    name = label or (f"{os.path.basename(path)}:{a}" + (f"-{b}" if b != a else ""))
    who = NAMES.get(commit)
    sup = f'<sup class="at">{who}</sup>' if (who and tag) else ""
    return (f'<a class="cl" href="https://github.com/hazelgrove/hazel/blob/{commit}/{path}{frag}" '
            f'title="{path}, lines {a}-{b}, at {commit[:10]}"><code>{name}</code></a>{sup}')


def d(path, a, b=None, label=None):
    return gh(D, path, a, b, label)


def p(path, a, b=None, label=None):
    return gh(P, path, a, b, label)


def at(commit, path, a, b=None, label=None):
    return gh(commit, path, a, b, label)


def commit(c, label=None):
    return f'<a href="https://github.com/hazelgrove/hazel/commit/{c}"><code>{label or c[:10]}</code></a>'


def pr(n, phrase=None):
    t = f'<a href="https://github.com/hazelgrove/hazel/pull/{n}">#{n}</a>'
    return t + (f" ({phrase})" if phrase else "")


def issue(n, phrase=None):
    t = f'<a href="https://github.com/hazelgrove/hazel/issues/{n}">#{n}</a>'
    return t + (f" ({phrase})" if phrase else "")


def rep(n, anchor=""):
    return (f'<a href="../{n:03d}/{anchor}"><code class="ref"><b>^report(</b>{n}<b>)</b></code></a>')
