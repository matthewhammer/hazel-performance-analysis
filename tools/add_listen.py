"""A 🔊 Listen bar on a report (^ticket(573), Matthew: "a Listen button for the reports, using the browser's own voices",
"and get a slider for reading speed (if possible), and adjusted reading time"): read aloud by the reader's own browser
(speechSynthesis; nothing is sent anywhere), the report's prose in order, block by block (the title, the question, the short
answers, each section's headings, paragraphs, points and captions; not code, tables, figures' drawings or the embedded data),
the block being read marked and kept in view. Play / pause / stop, the voice (from the ones the device has) and the speed
(0.5x to 2x), both remembered for this site; beside them the listening time at that speed, from the report's words (about 160
words a minute at 1x). A browser without speech gets no bar. Idempotent (between markers): placed after the series line
(<p class="series">), or at the top of <main>.  python3 tools/add_listen.py page.html ..."""
import sys

B, E = "<!-- listen: begin -->", "<!-- listen: end -->"
BLOCK = B + '''
<style>
  .listen { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; margin: 6px 0 10px; font: 13px system-ui, sans-serif; color: var(--muted, GrayText); }
  .listen[hidden] { display: none; }
  .listen button { font: inherit; padding: 2px 10px; border-radius: 999px; border: 1px solid var(--line, #ccc); background: var(--paper, Canvas); color: var(--ink, CanvasText); cursor: pointer; }
  .listen button[aria-pressed="true"] { border-color: var(--accent, #6d28d9); color: var(--accent, #6d28d9); }
  .listen select { font: inherit; max-width: 16em; border-radius: 6px; border: 1px solid var(--line, #ccc); background: var(--paper, Canvas); color: var(--ink, CanvasText); }
  .listen input[type=range] { width: 8em; vertical-align: middle; accent-color: var(--accent, #6d28d9); }
  .listen .speed { min-width: 3.2em; display: inline-block; font-variant-numeric: tabular-nums; }
  .listen-now { outline: 2px solid color-mix(in srgb, var(--accent, #6d28d9) 55%, transparent); outline-offset: 3px; border-radius: 4px;
    background: color-mix(in srgb, var(--accent, #6d28d9) 8%, transparent); }
  @media print { .listen { display: none; } }
</style>
<div class="listen" hidden role="group" aria-label="Listen to this report">
  <button type="button" class="listen-play" aria-pressed="false">🔊 Listen</button>
  <button type="button" class="listen-stop">⏹ Stop</button>
  <label>speed <input type="range" class="listen-rate" min="0.5" max="2" step="0.1" value="1"> <span class="speed">1.0×</span></label>
  <select class="listen-voice" aria-label="voice"></select>
  <span class="listen-time"></span>
</div>
<script>
/* (^ticket(573)) Listen: the report read aloud by this browser's own voices; nothing leaves the page. */
// (once the whole page is parsed: this runs where the bar is, near the top, before the report's sections exist)
document.addEventListener("DOMContentLoaded", () => {
  const S = window.speechSynthesis, bar = document.querySelector(".listen");
  if (!S || !bar || typeof SpeechSynthesisUtterance === "undefined") return;
  bar.hidden = false;
  const main = document.querySelector("main") || document.body;
  const play = bar.querySelector(".listen-play"), stop = bar.querySelector(".listen-stop"), rate = bar.querySelector(".listen-rate"),
        speed = bar.querySelector(".speed"), voiceSel = bar.querySelector(".listen-voice"), timeEl = bar.querySelector(".listen-time");
  const store = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (_) { return null; } };
  // the blocks to read, in order: prose only, each once (a point holding paragraphs is read as its paragraphs)
  const SKIP = "table, pre, svg, script, style, .listen, .theme-toggle, details:not([open]), [aria-hidden=true], button, nav, #report-data";
  const blocks = [...main.querySelectorAll("h1, .sub, h2, h3, h4, p, li, blockquote, figcaption, summary")]
    .filter(el => !el.closest(SKIP) && !el.querySelector("p, li, blockquote") && !el.matches(".series"));
  const textOf = el => { const c = el.cloneNode(true); c.querySelectorAll(".anchor, .copyanchor, button, sup").forEach(x => x.remove()); return c.textContent.replace(/\\s+/g, " ").trim(); };
  const texts = blocks.map(textOf), words = texts.reduce((n, t) => n + (t ? t.split(" ").length : 0), 0);
  const WPM = 160;
  let i = 0, playing = false, voices = [];
  const r = () => +rate.value;
  const showTime = () => {
    speed.textContent = r().toFixed(1) + "×";
    const left = texts.slice(playing || i ? i : 0).reduce((n, t) => n + (t ? t.split(" ").length : 0), 0);
    const min = Math.max(1, Math.round(left / (WPM * r())));
    timeEl.textContent = (i && left < words ? "about " + min + " min left" : "about " + min + " min to listen") + " at " + r().toFixed(1) + "×";
  };
  const fill = () => {
    voices = S.getVoices().filter(v => !document.documentElement.lang || v.lang.slice(0, 2) === document.documentElement.lang.slice(0, 2) || v.lang.startsWith("en"));
    const want = store("listen-voice");
    voiceSel.replaceChildren(...voices.map(v => { const o = document.createElement("option"); o.value = v.name; o.textContent = v.name + (v.localService ? "" : " (online)"); return o; }));
    voiceSel.hidden = !voices.length;
    if (want && voices.some(v => v.name === want)) voiceSel.value = want;
    else { const d = voices.find(v => v.default) || voices[0]; if (d) voiceSel.value = d.name; }
  };
  fill(); if ("onvoiceschanged" in S) S.onvoiceschanged = fill;
  const saved = parseFloat(store("listen-rate")); if (saved >= 0.5 && saved <= 2) rate.value = saved;
  const mark = el => { document.querySelectorAll(".listen-now").forEach(x => x.classList.remove("listen-now")); if (el) { el.classList.add("listen-now"); el.scrollIntoView({ block: "nearest", behavior: "smooth" }); } };
  // one block at a time (a long utterance is cut short in some browsers); the next when it ends
  const speak = () => {
    while (i < blocks.length && !texts[i]) i++;
    if (i >= blocks.length) { end(); return; }
    const u = new SpeechSynthesisUtterance(texts[i]), v = voices.find(v => v.name === voiceSel.value);
    if (v) { u.voice = v; u.lang = v.lang; }
    u.rate = r();
    u.onend = () => { if (!playing) return; i++; showTime(); speak(); };
    u.onerror = e => { if (e.error === "interrupted" || e.error === "canceled") return; i++; if (playing) speak(); };
    mark(blocks[i]); S.speak(u);
  };
  const end = () => { playing = false; S.cancel(); i = 0; mark(null); play.textContent = "🔊 Listen"; play.setAttribute("aria-pressed", "false"); showTime(); };
  play.onclick = () => {
    if (playing && !S.paused) { S.pause(); play.textContent = "▶ Resume"; return; }
    if (playing && S.paused) { S.resume(); play.textContent = "⏸ Pause"; return; }
    playing = true; play.textContent = "⏸ Pause"; play.setAttribute("aria-pressed", "true"); S.cancel(); speak();
  };
  stop.onclick = end;
  // a new speed or voice takes effect from the block being read, said again from its start
  const again = () => { if (playing) { S.cancel(); setTimeout(speak, 0); } };
  rate.oninput = () => { store("listen-rate", rate.value); showTime(); };
  rate.onchange = again;
  voiceSel.onchange = () => { store("listen-voice", voiceSel.value); again(); };
  addEventListener("pagehide", () => S.cancel());
  showTime();
});
</script>
''' + E


def add(path):
    s = open(path, encoding="utf8").read()
    if B in s:
        a, b = s.index(B), s.index(E) + len(E)
        s = s[:a] + s[b:]
        s = s.replace("\n\n" + "\n", "\n\n")
    at = s.find('<p class="series"')
    if at >= 0:
        at = s.index("</p>", at) + len("</p>")
    else:
        at = s.index(">", s.index("<main")) + 1
    s = s[:at] + "\n" + BLOCK + s[at:]
    open(path, "w", encoding="utf8").write(s)
    print("listen:", path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        add(p)
