#!/usr/bin/env python3
"""Writes 028/index.html, ^report(28): Hazel and Fumola side by side, for translating (^ticket(543)).
Every Fumola line here was run on Fumola's wasm build (fumola-wasm-main/bindings, 667a34d) on 2026-10-22."""
import os, html, json
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(HERE)
STYLE = open(os.path.join(R, "..", "025", "drivers", "style.css")).read()
esc = html.escape
ROWS = [
 ("A function", "let f = fun (a, b) : (Int, Int) -> a + b in", "func f(a, b) { a + b };", "Annotations optional in both. Fumola: <code>func f (x : Nat) : Nat { x }</code>."),
 ("Calling it", "f(1, 2)", "f(1, 2)", ""),
 ("A recursive helper", "let find = fun (cs, c, r) -> ... find(rest, c, r) ... in", "func find_at(cs, i, n, c, r) { ... find_at(cs, i + 1, n, c, r) ... };", "Hazel walks a list by cons; Fumola's arrays by index (<code>cs[i]</code>, <code>cs.size()</code>)."),
 ("Let, and a sequence", "let x = 3 in x + 1", "let x = 3; x + 1", "Fumola: <code>;</code> between, and <code>var y = 1; y := y + 1</code> for a mutable."),
 ("A tuple, taken apart", "let (c, r) = p in c + r", "let (c, r) = p; c + r", ""),
 ("A record", "(col = 1, row = 2)", "{ col = 1; row = 2 }", "Fields with <code>=</code> in both; Hazel separates with <code>,</code>, Fumola with <code>;</code>. Both: <code>x.col</code>."),
 ("A record type", "type Cell = (col = Int, row = Int, kind = String, ways = [String]) in", "(none needed)", "Fumola infers; Hazel's rules declare them in the preamble."),
 ("A sum type", "type Cmd = + Done + GoSquare(Int, Int, String, Cmd) in", "(none needed)", "Fumola's variants are open: <code>#GoSquare</code> needs no declaration."),
 ("A constructor, applied", "GoSquare(c, r, back, Done)", "#GoSquare((c, r, back, #Done))", "Fumola: <code>#</code>, and a tuple payload takes its own parentheses: two pairs."),
 ("A case on a variant", "case e\n| Way(d) => ...\n| _ => Done\nend", "switch (e) {\n  case (#Way(d)) { ... };\n  case _ { #Done }\n}", "Fumola: <code>;</code> between cases. A pattern <code>#X</code> does not match a value <code>#X(payload)</code>."),
 ("An option", "Some(x) / None (declared constructors)", "?x / null", "Fumola: <code>case (?x) { ... }; case null { ... }</code>."),
 ("A list literal, and joining", "[1, 2] @ [3]", "[1, 2] # [3]", "Fumola's are arrays: <code>xs[i]</code>, <code>xs.size()</code>, <code>for (x in xs.vals()) { ... }</code>."),
 ("A list, taken apart", "case xs | [] => ... | x :: rest => ... end", "(by index, or a loop)", "Fumola has no cons pattern on arrays."),
 ("If", "if c then a else b", "if (c) { a } else { b }", ""),
 ("And, or, not", "a && b, a || b, !a", "a and b, a or b, not a", ""),
 ("Text: equal, join", "a == b, a ++ b", "a == b, a # b", "Fumola's <code>!=</code> on text is inverted: see the traps."),
 ("Numbers", "Int; 0 - 1 for minus one; Float ops <., +.", "Nat and Int; 5 - 7 is -2 (an Int)", "Fumola keeps Nat and Int apart: see the traps."),
 ("A map", "(none: a list of pairs, walked)", "HashMap.new(), HashMap.put(m, k, v) gives (m2, old), HashMap.get(m, k) gives ?v", "Fumola's is persistent (a hash trie, im_rc): put returns a new map. Any value is a key, a tuple too."),
 ("A comment", "# words #", "// words, or /* words */", "Hazel's closes with <code>#</code>: an unclosed one swallows code."),
]
TRAPS = [
 ("Text <code>!=</code> is inverted.", "<code>\"a\" != \"b\"</code> is <code>false</code> and <code>\"a\" != \"a\"</code> is <code>true</code> (run on the wasm build; the <code>Neq</code> arm for text in <code>crates/fumola_semantics/src/lib/vm_ops.rs</code>). Write <code>not (a == b)</code>, or <code>(a == b) == false</code>."),
 ("No text patterns.", "<code>case \"E\"</code> never matches (patterns take Unit, Null and Nat literals only). Test text with <code>==</code> in an <code>if</code>."),
 ("Nat and Int apart.", "A Nat minus a larger Nat is an Int; Int + Nat is a type error; <code>&lt;=</code>, <code>&gt;</code>, <code>&gt;=</code> between them are missing (only <code>&lt;</code> mixes); <code>Int(4) == Nat(4)</code> is false, and they are different map keys. Keep coordinates Nat, and check an edge before stepping off it (the World rule's <code>step</code>)."),
 ("No escapes in text.", "A literal's quotes are stripped, nothing more: no <code>\\\"</code> or <code>\\\\</code> inside."),
 ("A tuple payload, twice parenthesised.", "<code>#GoSquare((c, r, back, #Done))</code>: the outer pair is the application, the inner the tuple."),
]
BOUNDARY = [
 ("What a page loads", "hazel-lib.js (2.8 MB), window.Hazel", "fumola_wasm.js and fumola_wasm_bg.wasm (6.3 MB), initSync or init"),
 ("A program", "Hazel.run(text) gives {errors, value}", "fumola_create() an instance; fumola_eval_top(id, text) gives a JSON string"),
 ("Keeping a function", "the value back is a JS function", "top-level bindings persist in the instance; call by name in a later text"),
 ("Arguments", "JS values, converted (of_js): arrays to lists, objects to records, {tag, value} to constructors", "source text only: the call written out, its arguments as literals"),
 ("The answer", "a JS value (to_js): records to objects, constructors to {tag, value}", "JSON: {tag, value}, with variants as {tag: \"Variant\", value: {name, value}}, numbers as strings"),
 ("Counting work", "times only", "every answer carries counts.step"),
]
hz = open(os.path.join(R, "data", "world.hazel")).read(); fu = open(os.path.join(R, "data", "world.fum")).read()
rows = "".join(f'<tr><td>{a}</td><td><pre class="code">{esc(b)}</pre></td><td><pre class="code">{esc(c)}</pre></td><td>{d}</td></tr>' for a, b, c, d in ROWS)
traps = "".join(f"<li><b>{a}</b> {b}</li>" for a, b in TRAPS)
bnd = "".join(f"<tr><td>{a}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in BOUNDARY)
PAGE = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hazel and Fumola, Side by Side</title>
<meta name="description" content="Each construct Messed Up Dress Up's room rules use, in Hazel and in Fumola, with the traps found translating them and how each takes a value from JS: for the next translation.">
<style>{STYLE}
table.side td {{ vertical-align: top; }} table.side pre.code {{ margin: 0; font-size: 0.82em; white-space: pre-wrap; }}
.pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }} .pair pre.code {{ font-size: 0.8em; white-space: pre-wrap; }}
@media (max-width: 760px) {{ .pair {{ grid-template-columns: 1fr; }} }}
</style></head>
<body><main>
<p class="series"><a href="../">Hazel reports</a> · <code class="ref"><b>^report(</b>28<b>)</b></code> · reference · started 2026-10-22 · <span class="wip">work in progress</span></p>
<h1>Hazel and Fumola, Side by Side</h1>
<p class="sub">Matthew, while the game's World rule was being written in Fumola for <code class="ref"><b>^report(</b>27<b>)</b></code> (<code class="ref"><b>^ticket(</b>542<b>)</b></code>): <q>would it be helpful to compare a document comparing the syntax of Hazel vs Fumola, to make translations easier next time?</q> This is that document (<code class="ref"><b>^ticket(</b>543<b>)</b></code>). Every Fumola line in it was run on Fumola's wasm build (<code>667a34d</code>); it grows as more of the rules are translated.</p>

<h2 id="table">Construct by construct</h2>
<div class="scroll"><table class="side"><tr><th>construct</th><th>Hazel</th><th>Fumola</th><th>notes</th></tr>{rows}</table></div>

<h2 id="traps">Traps, found translating</h2>
<ul>{traps}</ul>

<h2 id="boundary">Across the JS boundary</h2>
<div class="scroll"><table><tr><th></th><th>Hazel (its JS library, #2711)</th><th>Fumola (its wasm build)</th></tr>{bnd}</table></div>

<h2 id="world">One rule, both ways: the World room's step</h2>
<p>The game's shipped Hazel rule (<code>25-scripting.js</code>, <code>SCRIPT_WORLD</code>, with <code>Common</code>'s helpers it uses) and the Fumola one written for <code class="ref"><b>^report(</b>27<b>)</b></code>. Both answer <code>GoSquare(c, r, back, Done)</code> or <code>Done</code> for the same moves.</p>
<div class="pair"><div><b>Hazel</b><pre class="code">{esc(hz)}</pre></div><div><b>Fumola</b><pre class="code">{esc(fu)}</pre></div></div>

<h2 id="method">How this was put together</h2>
<p>The Hazel side is the game's rules (kids-choice-games#2, <code>hazel-logic-531</code>). The Fumola side was written for <code class="ref"><b>^ticket(</b>542<b>)</b></code> and run in node on Fumola's wasm build, line by line (<code>fumola_eval_top</code>); the traps were found in Fumola's source and confirmed by running them.</p>
</main></body></html>
"""
open(os.path.join(R, "index.html"), "w").write(PAGE); print("wrote 028/index.html")
