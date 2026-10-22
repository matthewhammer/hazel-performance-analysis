#!/usr/bin/env python3
"""Writes 026/index.html, ^report(26): does #2681 need #2661? (Alexander's question, ^ticket(541)).
  python3 026/drivers/gen026.py   (then build.sh runs the series tools)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE)
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Does #2681 Need #2661?</title>
<meta name="description" content="Alexander asked whether hazelgrove/hazel#2681 needs #2661 and suggested retargeting its base. It does: its memo is keyed by #2661's type hash. Merged with #2661's branch and retargeted, #2681 shows reviewers only its own commit.">
<style>{STYLE}</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>26<b>)</b></code> · review · started 2026-10-22 · <span class="wip">work in progress</span> · about 4 minutes to read</p>
<h1>Does #2681 Need #2661?</h1>
<p class="sub">Alexander, on #2681 (a value known to have a type is not walked again for it): <q>Looks like it needs #2661 as a dependency. Might be worth just changing the parent branch of the pr to that branch.</q> Matthew: <q>It seems like a real dep, but I'll double check.</q> This is that double check (<code class="ref"><b>^ticket(</b>541<b>)</b></code>), made with git alone, nothing built or run.</p>

<div class="headline">
<p><b>Short answers.</b></p>
<ol class="ans">
<li><b>Yes, #2661 is a real dependency.</b> #2681's own commit, <code>8546bde64e</code>, keys its memo by the type's hash: <code>known_to_have</code> and <code>noted</code> both call <code>TypHash.hash(t)</code>, which #2661 adds. Without #2661, #2681 does not compile.</li>
<li><b>#2681 carries #2661 today as merges, not as a base.</b> Its branch merged #2661's first two commits (<code>0875dfcd66</code>, <code>67f676852b</code>) and #2679 (<code>a032bd5c6a</code>), and holds a copy of #2661's third (<code>a4fee77a63</code>, the same patch as #2661's <code>09b8af372f</code>). So against <code>dev</code> its diff is 39 files, the dependencies included, and it is 14 commits behind <code>dev</code>.</li>
<li><b>Retargeting works, after one merge.</b> #2661's branch is up to date with <code>dev</code> (it merged <code>dev</code>, which now has #2679). Merging #2661's head into #2681's branch conflicts in <code>Ascriptions.re</code>, the known conflict between #2661's and #2679's helpers, and #2681's side is the right resolution: it already has both helpers and the memo. After that merge, #2681 against #2661's branch is 4 files, +161 and -2: its own commit, one line of layout apart.</li>
<li><b>So Alexander's suggestion is the simplest review.</b> Merge #2661's head into #2681's branch (resolution: #2681's <code>Ascriptions.re</code>), push, and set #2681's base to <code>typ-hash-consistent</code>. Reviewers see one commit. When #2661 lands, #2681's base goes back to <code>dev</code> and its diff stays that one commit.</li>
</ol>
</div>

<h2 id="evidence">The evidence</h2>
<h3 id="uses">What #2681's commit uses from #2661</h3>
<pre class="code">known_to_have = (d, t) =&gt; switch (type_key(d), TypHash.hash(t)) {{ ... }}
noted = (e, t, r) =&gt; switch (r, TypHash.hash(t)) {{ ... }}
let has_type: Util.IdentityTable.t(Obj.t, list(TypHash.t))</pre>
<p>The memo remembers, per value, the hashes of the types it has; a lookup asks for the type's hash. <code>TypHash</code> is #2661's module, so the dependency is in the memo's design, not incidental.</p>

<h3 id="branches">The branches today</h3>
<div class="scroll"><table>
<tr><th>branch</th><th>head</th><th>against dev</th></tr>
<tr><td>#2661, <code>typ-hash-consistent</code></td><td><code>09b8af372f</code></td><td>4 commits ahead (its three, and a merge of dev), 0 behind</td></tr>
<tr><td>#2681, <code>ascriptions-has-type</code></td><td><code>a4fee77a63</code></td><td>6 commits ahead (#2661's first two, a merge of #2679, its own <code>8546bde64e</code>, a merge of #2661's three-lane hash, a copy of #2661's test commit), 14 behind</td></tr>
</table></div>
<p><code>a4fee77a63</code> on #2681 and <code>09b8af372f</code> on #2661 have the same patch (<code>git patch-id</code>), so the merge below takes it once.</p>

<h3 id="simulation">The retarget, simulated</h3>
<p>In a scratch worktree, never pushed: #2681's head, merged with #2661's head.</p>
<ul>
<li>One conflict, in <code>Ascriptions.re</code>. #2681's side keeps both helpers (#2661's <code>consistent_by_hash</code>, #2679's <code>unchanged</code>) and the memo; #2661's side has the first two.</li>
<li>Resolved with #2681's side, the diff against <code>typ-hash-consistent</code> is <code>Ascriptions.re</code> +84 -2, <code>IdentityTable.re</code> +24, <code>Util.re</code> +1, <code>Test_Ascriptions.re</code> +54: <code>8546bde64e</code>'s four files (its own stat is +83 -1 in <code>Ascriptions.re</code>; the extra line is layout around <code>transition</code>).</li>
</ul>

<h2 id="steps">The steps</h2>
<ol>
<li>On <code>ascriptions-has-type</code>: <code>git merge origin/typ-hash-consistent</code>; resolve <code>Ascriptions.re</code> with #2681's side; build and run <code>Ascriptions</code>, <code>TypHash</code> and <code>Evaluator</code> (on GitHub's CI).</li>
<li>Push, then set #2681's base to <code>typ-hash-consistent</code>. The PR then shows one commit.</li>
<li>Optionally, in the same push: the depth-1 limit on the memo and its test (<a href="https://github.com/hazelgrove/hazel/pull/2681#issuecomment-6344616722">proposed on #2681</a>, measured in <a href="../025/#floor">^report(25)</a>).</li>
<li>When #2661 merges into <code>dev</code>, set #2681's base back to <code>dev</code> (GitHub does it on its own if #2661's branch is deleted).</li>
</ol>

<h2 id="method">How this was put together</h2>
<p>git on <code>dev</code> at <code>962a7cb009</code>, #2661 at <code>09b8af372f</code> and #2681 at <code>a4fee77a63</code>, 2026-10-22: <code>git log</code> per branch, <code>git merge-base --is-ancestor</code> per commit, <code>git patch-id</code> for the copied commit, and the merge in a scratch worktree (resolution recorded, nothing pushed). The stats are in <code>data/</code>.</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE); print("wrote 026/index.html")
