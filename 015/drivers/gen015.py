#!/usr/bin/env python3
"""^ticket(120): ^report(15)'s page, from the measurements in 015/data/.

  python3 gen015.py   # writes ~/hazel-perf-report/015/index.html
"""
import json, os, re, html, statistics

R = os.path.expanduser("~/hazel-perf-report")
D = os.path.join(R, "015", "data")
J = lambda f: json.load(open(os.path.join(D, f)))

dn, df, dw, de = J("dress_none.json"), J("dress_forest.json"), J("dress_witch.json"), J("dress_eyes.json")
hk, hc, hb = J("hazel_kids_eyes.json"), J("hazel_fullbody_C.json"), J("hazel_fullbody_B.json")
dc = J("dress_change_ms.json")
tld, tlk, tlf = J("tl_dress.json"), J("tl_kids.json"), J("tl_fullbody.json")

css = re.search(r"<style>(.*?)</style>", open(os.path.join(R, "014", "index.html")).read(), re.S).group(1)
esc = html.escape
s1 = lambda ms: f"{ms / 1000:.2f}"
def med(d, k): return d[k]["median"]
def rng(d, k): return d[k]["min"], d[k]["max"]

# ---------- figures ----------
def hbars(title, rows, unit, vmax, note, aria, fmt=lambda v: f"{v:g}", w=460):
    """rows: (label, sublabel, value, lo, hi, cls); bars from x0, whiskers lo..hi."""
    h = 52 + 46 * len(rows) + 26
    x0, x1 = 210, w - 56
    sc = lambda v: x0 + (x1 - x0) * min(v, vmax) / vmax
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">{esc(title)}</text>']
    for i, (lab, sub, v, lo, hi, cls) in enumerate(rows):
        y = 44 + 46 * i
        out.append(f'<text x="{x0 - 8}" y="{y + 12}" text-anchor="end" class="cl">{esc(lab)}</text>')
        out.append(f'<text x="{x0 - 8}" y="{y + 27}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>')
        bw = max(sc(v) - x0, 1.5)
        out.append(f'<rect x="{x0}" y="{y}" width="{bw:.1f}" height="22" rx="3" style="fill: var(--{cls})"/>')
        if lo is not None and hi is not None and hi > lo:
            out.append(f'<line x1="{sc(lo):.1f}" y1="{y + 11}" x2="{sc(hi):.1f}" y2="{y + 11}" class="rng"/>'
                       f'<line x1="{sc(lo):.1f}" y1="{y + 5}" x2="{sc(lo):.1f}" y2="{y + 17}" class="rng"/>'
                       f'<line x1="{sc(hi):.1f}" y1="{y + 5}" x2="{sc(hi):.1f}" y2="{y + 17}" class="rng"/>')
        tx = max(sc(v), sc(hi) if hi is not None else 0) + 6
        out.append(f'<text x="{tx:.1f}" y="{y + 16}" class="cl" font-weight="600">{esc(fmt(v))}</text>')
    out.append(f'<text x="{w / 2}" y="{h - 8}" text-anchor="middle" class="cv">{esc(note)}</text></svg>')
    return "".join(out)

def logbars(title, rows, aria, budget=16.7, w=460):
    import math
    h = 52 + 50 * len(rows) + 40
    x0, x1 = 200, w - 70
    lo, hi = math.log10(0.5), math.log10(3000)
    sc = lambda v: x0 + (x1 - x0) * (math.log10(v) - lo) / (hi - lo)
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">{esc(title)}</text>']
    for t in (1, 10, 100, 1000):
        out.append(f'<line x1="{sc(t):.1f}" y1="34" x2="{sc(t):.1f}" y2="{h - 34}" class="grid"/>'
                   f'<text x="{sc(t):.1f}" y="{h - 20}" text-anchor="middle" class="cv">{"1 s" if t == 1000 else f"{t} ms"}</text>')
    out.append(f'<line x1="{sc(budget):.1f}" y1="30" x2="{sc(budget):.1f}" y2="{h - 34}" class="diag"/>'
               f'<text x="{sc(budget) + 4:.1f}" y="40" class="cv" font-size="11">one frame, 16.7 ms</text>')
    for i, (lab, sub, v, cls) in enumerate(rows):
        y = 50 + 50 * i
        out.append(f'<text x="{x0 - 8}" y="{y + 12}" text-anchor="end" class="cl">{esc(lab)}</text>'
                   f'<text x="{x0 - 8}" y="{y + 27}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>'
                   f'<rect x="{sc(0.5):.1f}" y="{y}" width="{sc(v) - sc(0.5):.1f}" height="22" rx="3" style="fill: var(--{cls})"/>'
                   f'<text x="{sc(v) + 6:.1f}" y="{y + 16}" class="cl" font-weight="600">{v:,.1f} ms</text>' if v < 10 else
                   f'<text x="{x0 - 8}" y="{y + 12}" text-anchor="end" class="cl">{esc(lab)}</text>'
                   f'<text x="{x0 - 8}" y="{y + 27}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>'
                   f'<rect x="{sc(0.5):.1f}" y="{y}" width="{sc(v) - sc(0.5):.1f}" height="22" rx="3" style="fill: var(--{cls})"/>'
                   f'<text x="{sc(v) + 6:.1f}" y="{y + 16}" class="cl" font-weight="600">{v:,.0f} ms</text>')
    out.append("</svg>")
    return "".join(out)

def timeline(aria, w=860):
    lanes = [("Dress Up", "arm length", tld), ("Hazel: Kids' Choice", "eye size", tlk), ("Hazel: Full Body", "arm length, whole program", tlf)]
    runs = [next(r for r in t["runs"] if not r["warmup"]) for _, _, t in lanes]
    tmax = max(r["frame_ms"][-1] for r in runs) + 200
    x0, x1 = 170, w - 20
    sc = lambda t: x0 + (x1 - x0) * t / tmax
    h = 60 + 70 * len(lanes) + 40
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">One 1.5-second drag, frame by frame: each tick is a frame the page drew</text>']
    for t in range(0, int(tmax), 500):
        out.append(f'<line x1="{sc(t):.1f}" y1="36" x2="{sc(t):.1f}" y2="{h - 36}" class="grid"/>'
                   f'<text x="{sc(t):.1f}" y="{h - 22}" text-anchor="middle" class="cv">{t / 1000:g} s</text>')
    for i, ((lab, sub, _), r) in enumerate(zip(lanes, runs)):
        y = 50 + 70 * i
        out.append(f'<text x="{x0 - 10}" y="{y + 18}" text-anchor="end" class="cl" font-weight="600">{esc(lab)}</text>'
                   f'<text x="{x0 - 10}" y="{y + 33}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>')
        fr = r["frame_ms"]
        for a, b in zip(fr, fr[1:]):
            if b - a > 50:
                out.append(f'<rect x="{sc(a):.1f}" y="{y + 2}" width="{sc(b) - sc(a):.1f}" height="34" style="fill: color-mix(in srgb, var(--bad) 18%, transparent)"/>')
        for t in fr:
            out.append(f'<line x1="{sc(t):.1f}" y1="{y + 6}" x2="{sc(t):.1f}" y2="{y + 32}" style="stroke: var(--accent)" stroke-width="1"/>')
        if r.get("up_ms") is not None:
            ux = sc(r["up_ms"])
            out.append(f'<line x1="{ux:.1f}" y1="{y - 2}" x2="{ux:.1f}" y2="{y + 40}" style="stroke: var(--ink)" stroke-width="1.6" stroke-dasharray="3 2"/>')
            if i == 0:
                out.append(f'<text x="{ux + 4:.1f}" y="{y - 2}" class="cv" font-size="11">finger up</text>')
        if r.get("release_to_redraw_ms") is not None and r.get("up_ms") is not None:
            dx_ = sc(r["up_ms"] + r["release_to_redraw_ms"])
            out.append(f'<circle cx="{dx_:.1f}" cy="{y + 19}" r="5" style="fill: var(--good)"/>')
        out.append(f'<text x="{x1:.1f}" y="{y + 52}" text-anchor="end" class="cv" font-size="11">{len(fr)} frames; longest gap {r["longest_gap_ms"]} ms; frozen {r["stalled_ms"] / 1000:.1f} s</text>')
    out.append(f'<text x="{w / 2}" y="{h - 6}" text-anchor="middle" class="cv">pink: gaps over 50 ms, when the page was frozen; dashed: the finger lifts; green dot: the picture shows the final value</text></svg>')
    return "".join(out)

def history(aria, w=460):
    import math
    rows = [("Polygons: a click adds a point", "2026-10-09, the same day", 11000, 200, "the same day"),
            ("Kids' Choice: release to redraw", "2026-10-09 afternoon → today", 4600, med(hk, "release_to_redraw_ms"), "six days"),
            ("Full Body: release to redraw", "10-12, full branch → today", 8600, med(hc, "release_to_redraw_ms"), "three days")]
    x0, x1 = 200, w - 70
    lo, hi = math.log10(50), math.log10(20000)
    sc = lambda v: x0 + (x1 - x0) * (math.log10(v) - lo) / (hi - lo)
    h = 52 + 72 * len(rows) + 30
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">How far it has come: then and now (log scale)</text>']
    for t in (100, 1000, 10000):
        out.append(f'<line x1="{sc(t):.1f}" y1="34" x2="{sc(t):.1f}" y2="{h - 30}" class="grid"/>'
                   f'<text x="{sc(t):.1f}" y="{h - 16}" text-anchor="middle" class="cv">{t / 1000:g} s</text>')
    for i, (lab, sub, a, b, when) in enumerate(rows):
        y = 44 + 72 * i
        out.append(f'<text x="{x0 - 8}" y="{y + 14}" text-anchor="end" class="cl">{esc(lab)}</text>'
                   f'<text x="{x0 - 8}" y="{y + 29}" text-anchor="end" class="cv" font-size="11">{esc(sub)}</text>'
                   f'<rect x="{sc(50):.1f}" y="{y}" width="{sc(a) - sc(50):.1f}" height="18" rx="3" style="fill: var(--muted); opacity: 0.55"/>'
                   f'<text x="{sc(a) + 5:.1f}" y="{y + 13}" class="cv">{a / 1000:g} s</text>'
                   f'<rect x="{sc(50):.1f}" y="{y + 22}" width="{sc(b) - sc(50):.1f}" height="18" rx="3" style="fill: var(--good)"/>'
                   f'<text x="{sc(b) + 5:.1f}" y="{y + 35}" class="cl" font-weight="600">{b / 1000:.2f} s</text>')
    out.append("</svg>")
    return "".join(out)

def bands(aria, w=860):
    """speculation: where a change could land by September 2027, against bands of feel"""
    import math
    lo, hi = math.log10(5), math.log10(2500)
    x0, x1 = 170, w - 30
    sc = lambda v: x0 + (x1 - x0) * (math.log10(v) - lo) / (hi - lo)
    h = 264
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" class="chart" aria-label="{esc(aria)}">',
           f'<text x="{w / 2}" y="20" text-anchor="middle" class="ct">The time from a slider change to its picture: today, and a guess for September 2027 (log scale)</text>']
    for a, b, lab, c in ((5, 16.7, "every frame", "good"), (16.7, 50, "feels immediate", "good2"), (50, 200, "a lag you notice", "warn"), (200, 2500, "waiting", "bad")):
        out.append(f'<rect x="{sc(a):.1f}" y="34" width="{sc(b) - sc(a):.1f}" height="{h - 80}" style="fill: color-mix(in srgb, var(--{c}) 12%, transparent)"/>'
                   f'<text x="{(sc(a) + sc(b)) / 2:.1f}" y="48" text-anchor="middle" class="cv" font-size="11">{lab}</text>')
    for t in (10, 16.7, 50, 100, 200, 500, 1000, 2000):
        out.append(f'<text x="{sc(t):.1f}" y="{h - 30}" text-anchor="middle" class="cv" font-size="11">{t:g} ms</text>')
    rows = [("Dress Up (plain JS)", 1.4 + 16.7, None, None, "accent"),
            ("Kids' Choice", med(hk, "release_to_redraw_ms"), 30, 60, "accent"),
            ("Full Body", med(hc, "release_to_redraw_ms"), 100, 300, "accent")]
    for i, (lab, now, glo, ghi, c) in enumerate(rows):
        y = 84 + 50 * i
        out.append(f'<text x="{x0 - 10}" y="{y + 5}" text-anchor="end" class="cl" font-weight="600">{esc(lab)}</text>')
        if glo:
            out.append(f'<rect x="{sc(glo):.1f}" y="{y - 9}" width="{sc(ghi) - sc(glo):.1f}" height="18" rx="9" style="fill: none; stroke: var(--accent)" stroke-width="1.6" stroke-dasharray="5 3"/>'
                       f'<line x1="{sc(now) - 8:.1f}" y1="{y}" x2="{sc(ghi) + 10:.1f}" y2="{y}" class="ar" marker-end="url(#ah15)"/>'
                       f'<text x="{(sc(glo) + sc(ghi)) / 2:.1f}" y="{y + 24}" text-anchor="middle" class="cv" font-size="11">guess: {glo}–{ghi} ms</text>')
        out.append(f'<circle cx="{sc(now):.1f}" cy="{y}" r="7" style="fill: var(--{c})"/>'
                   f'<text x="{sc(now):.1f}" y="{y - 13}" text-anchor="middle" class="cl" font-size="11.5">today {now:,.0f} ms</text>')
    out.insert(1, '<defs><marker id="ah15" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--muted)"/></marker></defs>')
    out.append(f'<text x="{w / 2}" y="{h - 8}" text-anchor="middle" class="cv">dots: measured today (Dress Up: its cost per change plus one frame); dashed: a guess, argued in the section below, not a measurement</text></svg>')
    return "".join(out)

# ---------- numbers ----------
dress_change = statistics.median(dc["times"]["none"] + dc["times"]["forest"] + dc["times"]["witch"])
prof = {"fullbody_C_main_js_ms": 1010, "fullbody_B_main_js_ms": 1251, "kids_main_js_ms": 225,
        "source": "Gecko profiler, headless Firefox, #2635 at 032fe3aca6, 2026-10-15 morning: 6 profiled changes of Full Body's arm length (whole program; UX mode), 4 of Kids' Choice's eye size; main-thread JavaScript per change. Profiled times run long."}

fig_stall = hbars("A 1.5-second drag: how long the page was frozen (s)", [
    ("Dress Up, no place", "arm length", 0, 0, 0, "good"),
    ("Dress Up, forest", "arm length", 0, 0, 0, "good"),
    ("Dress Up, witch's woods", "arm length", 0, 0, 0, "good"),
    ("Dress Up, eyes", "eye size", 0, 0, 0, "good"),
    ("Kids' Choice", "eye size", med(hk, "stalled_ms") / 1000, *[x / 1000 for x in rng(hk, "stalled_ms")], "warn"),
    ("Full Body, whole program", "arm length", med(hc, "stalled_ms") / 1000, *[x / 1000 for x in rng(hc, "stalled_ms")], "bad"),
    ("Full Body, UX mode", "arm length", med(hb, "stalled_ms") / 1000, *[x / 1000 for x in rng(hb, "stalled_ms")], "bad")],
    "s", 4.2, "medians of 8; lines: fastest to slowest; frozen: gaps over 50 ms",
    f"Time frozen during a 1.5 s drag: Dress Up 0 s in every case; Kids' Choice {med(hk, 'stalled_ms') / 1000:.2f} s; Full Body {med(hc, 'stalled_ms') / 1000:.1f} s with the whole program, {med(hb, 'stalled_ms') / 1000:.1f} s in UX mode.",
    fmt=lambda v: "0" if v == 0 else f"{v:.2f}")
fig_release = hbars("From the finger lifting to the final picture (s)", [
    ("Dress Up, no place", "arm length", 0.05, None, None, "good"),
    ("Dress Up, witch's woods", "arm length", med(dw, "release_to_redraw_ms") / 1000, *[x / 1000 for x in rng(dw, "release_to_redraw_ms")], "good"),
    ("Kids' Choice", "eye size", med(hk, "release_to_redraw_ms") / 1000, *[x / 1000 for x in rng(hk, "release_to_redraw_ms")], "warn"),
    ("Full Body, whole program", "arm length", med(hc, "release_to_redraw_ms") / 1000, *[x / 1000 for x in rng(hc, "release_to_redraw_ms")], "bad"),
    ("Full Body, UX mode", "arm length", med(hb, "release_to_redraw_ms") / 1000, *[x / 1000 for x in rng(hb, "release_to_redraw_ms")], "bad")],
    "s", 2.3, "medians of 8; ≤ 0.05 s: already final at the first check",
    f"Release to redraw: Dress Up at most 0.05 s (already final); Kids' Choice {med(hk, 'release_to_redraw_ms') / 1000:.2f} s; Full Body {med(hc, 'release_to_redraw_ms') / 1000:.2f} s whole program, {med(hb, 'release_to_redraw_ms') / 1000:.2f} s UX mode.",
    fmt=lambda v: "≤ 0.05" if v == 0.05 else f"{v:.2f}")
fig_change = logbars("One change, start to finish, in JavaScript on the page (log scale)", [
    ("Dress Up", "redraw the friend and the scene", dress_change, "good"),
    ("Kids' Choice", "eye size, profiled", prof["kids_main_js_ms"], "warn"),
    ("Full Body, whole program", "arm length, profiled", prof["fullbody_C_main_js_ms"], "bad"),
    ("Full Body, UX mode", "arm length, profiled", prof["fullbody_B_main_js_ms"], "bad")],
    f"Main-thread JavaScript per change, log scale: Dress Up {dress_change:.1f} ms, Kids' Choice 225 ms, Full Body 1,010 ms whole program and 1,251 ms in UX mode; one frame is 16.7 ms.")
fig_tl = timeline("Three lanes of frame ticks over about five seconds. Dress Up's ticks are evenly packed through the drag and the picture is final as the finger lifts. Kids' Choice's ticks have small gaps and the picture follows 0.1 s after the finger lifts. Full Body's ticks are broken by long gaps of up to half a second, and the picture is final about a second after the finger lifts.")
fig_hist = history(f"Then and now, log scale: Polygons click 11 s then 0.2 s; Kids' Choice release 4.6 s then {med(hk, 'release_to_redraw_ms') / 1000:.2f} s; Full Body release 8.6 s on the full livelits branch then {med(hc, 'release_to_redraw_ms') / 1000:.2f} s on the modular one.")
fig_bands = bands(f"Bands of feel from every frame to waiting, on a log scale of milliseconds. Today: Dress Up about 18 ms, Kids' Choice {med(hk, 'release_to_redraw_ms'):.0f} ms, Full Body {med(hc, 'release_to_redraw_ms'):.0f} ms. Guessed for September 2027, dashed: Kids' Choice 30 to 60 ms, Full Body 100 to 300 ms.")

def row(name, sub, d, extra=""):
    lg, st, rr, ip = d["longest_gap_ms"], d["stalled_ms"], d["release_to_redraw_ms"], d["inputs"]
    f = lambda m: f'{m["median"]:g} <span class="rr">({m["min"]:g}–{m["max"]:g})</span>'
    return (f'<tr><td>{name}<br><span class="note">{sub}</span></td><td class="n">{f(lg)}</td><td class="n">{f(st)}</td>'
            f'<td class="n">{f(rr)}</td><td class="n">{f(ip)}</td></tr>')

table_drag = ('<div class="scroll"><table><tr><th>Set-up</th><th>Longest gap between frames (ms)</th><th>Frozen, gaps over 50 ms (ms)</th>'
              '<th>Finger up to final picture (ms)</th><th>Input events the slider fired</th></tr>' +
              row("Dress Up, no place", "arm length", dn) + row("Dress Up, the forest", "arm length", df) +
              row("Dress Up, the witch's woods", "arm length", dw) + row("Dress Up, no place", "eye size", de) +
              row("Hazel: Kids' Choice", "eye size", hk) + row("Hazel: Full Body, whole program", "arm length", hc) +
              row("Hazel: Full Body, UX mode", "arm length", hb) + "</table></div>")

data = {
    "report": 15, "title": "Dress Up and its livelits, side by side", "date": "2026-10-15",
    "question": "How does Messed Up Dress Up, the plain-JS game, perform today against the same features as livelits in Hazel, and what could close the gap over the next 11 months? (Matthew, 2026-10-15)",
    "builds": {"hazel": {"pr": "hazelgrove/hazel#2635", "branch": "integration/livelits-modular-editors", "commit": "032fe3aca6", "bundle": "dev build, 2026-10-15 10:00"},
               "dress_up": {"repo": "matthewhammer/kids-choice-games", "version": "0.0.48", "commit": "08abedf7bc"}},
    "browser": dc["ua"], "machine": "Matthew's laptop (Linux, x86-64), headless Firefox 157, window 1600×1100, a fresh profile per set-up",
    "measures": {
        "drag": "one real drag per run (WebDriver pointer actions: down, 15 moves of 100 ms, up) to a value not drawn before; 2 warm-up drags, then 8 measured",
        "longest_gap_ms": "the longest time between two requestAnimationFrame callbacks, from just before the pointer goes down until the picture is final",
        "stalled_ms": "the sum of frame gaps over 50 ms in that window: time the page was frozen",
        "release_to_redraw_ms": "from pointerup to the first 50 ms poll at which the largest picture's markup differs from before the drag (a bound from above: the poll's resolution is 50 ms)",
        "inputs": "the slider's input events during the drag",
        "dress_change_ms": "Dress Up's changed() (redraw of the friend and scene, controls synced, state saved), 40 changes of arm length per sample, 5 samples per place, JavaScript only",
    },
    "drags": {"dress_none": dn, "dress_forest": df, "dress_witch": dw, "dress_eyes": de, "hazel_kids_eyes": hk, "hazel_fullbody_whole_program": hc, "hazel_fullbody_ux_mode": hb},
    "timelines": {"dress": tld, "kids": tlk, "fullbody": tlf},
    "dress_change_ms": dc, "hazel_profiled_per_change": prof,
    "history": [{"what": "Polygons: a click adding a point", "then_ms": 11000, "now_ms": 200, "source": "^report(1), 2026-10-09"},
                {"what": "Kids' Choice: slider release to redraw", "then_ms": 4600, "then": "2026-10-09 afternoon (^report(1))", "now_ms": med(hk, "release_to_redraw_ms"), "now": "this report"},
                {"what": "Full Body: release to redraw", "then_ms": 8600, "then": "#2597, ^report(8)", "now_ms": med(hc, "release_to_redraw_ms"), "now": "#2635, this report"}],
    "speculation": {"kids_sep_2027_ms": [30, 60], "fullbody_sep_2027_ms": [100, 300], "note": "guesses, argued in the report's section #bridge; not measurements"},
    "files": "https://github.com/matthewhammer/hazel-performance-analysis/tree/main/015/data",
}

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dress Up and Hazel Today</title>
<style>{css}
  figure.narrow svg.chart {{ max-width: 600px; margin: 0 auto; }}
</style>
</head>

<body>
<main>

<p class="series"><a href="../">Hazel performance analysis</a> · report 015 · 2026-10-15</p>
<h1>Dress Up and its livelits, side by side</h1>
<p class="sub">How does Messed Up Dress Up, the plain-JavaScript game Matthew's kids M and N play and design, perform today against the same features built as livelits in Hazel? And what could close the gap over the next eleven months? Matthew asked both on 2026-10-15. Dress Up is where each toy is tried first; report 002 described how its pieces became the Livelit Playground's slides. This report puts the two side by side with one measurement, a real drag of a slider, in one browser on one machine, and then guesses, as a guess, at what is reachable by September 2027.</p>

<div class="headline">
<p><b>Short answers.</b> Dress Up 0.0.48 and Hazel's <a href="https://github.com/hazelgrove/hazel/pull/2635">#2635</a> at <code>032fe3aca6</code>, in headless Firefox 157 on Matthew's laptop; 8 real drags per set-up, each 1.5 seconds long. Medians, with the fastest and slowest. The method is <a href="#method">at the end</a>.</p>
<ol>
  <li><b>Dress Up keeps up with the finger.</b> During a 1.5-second drag of a slider it never froze: the longest gap between frames was one frame (17 ms) with no place and in the forest, two frames (33 ms) in the witch's woods, its busiest place. When the finger lifted, the picture was already final. One change costs it about {dress_change:.1f} ms of JavaScript (<a href="#drag">Figures 1 and 3</a>).</li>
  <li><b>A small livelit is close.</b> Kids' Choice, a face drawn by a Hazel livelit, froze for {med(hk, 'stalled_ms') / 1000:.2f} s per drag (0 to {rng(hk, 'stalled_ms')[1] / 1000:.2f} s), its longest gap was {med(hk, 'longest_gap_ms'):g} ms, and the face was final {med(hk, 'release_to_redraw_ms') / 1000:.2f} s after the finger lifted. On 2026-10-09 that release took 4.6 s (<a href="#closed">Figure 5</a>).</li>
  <li><b>A big one is not.</b> Full Body, the whole Dress Up friend as Hazel code (167 items), froze for {med(hc, 'stalled_ms') / 1000:.1f} s during a 1.5-second drag with the whole program on screen ({rng(hc, 'stalled_ms')[0] / 1000:.1f}–{rng(hc, 'stalled_ms')[1] / 1000:.1f}), and {med(hb, 'stalled_ms') / 1000:.1f} s in UX mode. The picture was final {med(hc, 'release_to_redraw_ms') / 1000:.1f} s after the finger lifted ({med(hb, 'release_to_redraw_ms') / 1000:.1f} s in UX mode). Hazel handled {med(hc, 'inputs'):g} of the drag's input events where Dress Up handled about 50, and each one it handled took about a second of the page's time (<a href="#drag">Figures 1 to 3</a>).</li>
  <li><b>Per change, the gap is about {round(1010 / dress_change, -1):.0f} times for Full Body and {round(225 / dress_change, -1):.0f} times for Kids' Choice.</b> Profiled, one Full Body change costs about 1,010 ms of JavaScript on the page, Kids' Choice about 225 ms, and Dress Up's {dress_change:.1f} ms. A frame is 16.7 ms (<a href="#change">Figure 4</a>).</li>
  <li><b>Most of the distance has already been covered.</b> Full Body's release went from 8.6 s on <a href="https://github.com/hazelgrove/hazel/pull/2597">#2597</a> to {med(hc, 'release_to_redraw_ms') / 1000:.1f} s on #2635, Kids' Choice's from 4.6 to {med(hk, 'release_to_redraw_ms') / 1000:.2f} s, and a Polygons click from about 11 s to 0.2 s, all within the last week (<a href="#closed">Figure 5</a>).</li>
  <li><b>A guess for September 2027: Kids'-sized livelits immediate, Full Body a short lag.</b> The fixes in hand and the measured shares of where a change's time goes point to small livelits at 30 to 60 ms per change, and Full Body at 100 to 300 ms: a drag that follows the finger at a few to ten pictures a second, not every frame. Every frame for a program of Full Body's size would take an evaluator several times faster per step, which this guess does not assume. This is speculation, argued step by step <a href="#bridge">below</a> (<a href="#bridge">Figure 6</a>).</li>
</ol>
</div>

<div class="glance">
<figure id="fig-stall">{fig_stall}<figcaption><b>Figure 1.</b> The time the page was frozen (frame gaps over 50 ms) during a 1.5-second drag of one slider. Dress Up froze for none of it in any place; Hazel's Full Body was frozen for longer than the drag itself. Numbers in <a href="#drag">the table below</a>.</figcaption></figure>
<figure id="fig-release">{fig_release}<figcaption><b>Figure 2.</b> From the finger lifting to the final picture. Dress Up's picture is final as the finger lifts (the measurement checks every 50 ms, so ≤ 0.05 s means "at the first check"). Numbers in <a href="#drag">the table below</a>.</figcaption></figure>
</div>
<figure class="fig" id="fig-timeline">{fig_tl}<figcaption><b>Figure 3.</b> One drag in each, frame by frame: each tick is a frame the page drew, from the pointer going down; pink spans are gaps over 50 ms. Dress Up draws a frame every 17 ms throughout, and its picture is final when the finger lifts. Kids' Choice stutters a little and follows 0.1 s after. Full Body draws in bursts between long freezes, and its picture is final about a second after the finger lifts. One drag per lane (the first measured one); all runs are in the data.</figcaption></figure>

<h2 id="drag">One drag, three ways</h2>
<p>A slider drag is the commonest thing the kids do in Dress Up, and the simplest thing a livelit can be asked to do: one number changes, many times a second, and a picture that depends on it redraws. The same drag was made in each set-up: a real pointer, driven over WebDriver, pressing the slider's thumb, moving 15 times, 100 ms apart, and lifting, to a value not drawn before. A loop in the page records every frame from the press until the picture shows the final value. The set-ups:</p>
<ul>
  <li><b>Dress Up</b> 0.0.48: the friend's "arm length" slider, alone and in two of its places (the forest, and the witch's woods, the place with the most moving parts); and the "eye size" slider, the closest match to Kids' Choice.</li>
  <li><b>Kids' Choice</b> on the Livelit Playground: a face drawn by a livelit, with an "eye size" slider. A small program.</li>
  <li><b>Full Body</b> on the Livelit Playground: Dress Up's friend written in Hazel (167 items), with an "arm length" slider; with the whole program on screen, and in UX mode, where the outline shows only the slider and the picture (report 008 measured both modes' releases).</li>
</ul>
{table_drag}
<p class="note">Medians of 8 drags after 2 warm-ups, fastest to slowest in brackets. Dress Up's "finger up to final picture" of about 50 ms is the measurement's first check after the release: its picture was already final. Input events are what the browser fired for the slider: a page that is busy gets fewer, since the browser folds the moves it could not deliver into one.</p>
<p>The difference is not in what is drawn: Full Body draws the same friend as Dress Up's no-place set-up. It is in what a change costs. Dress Up handles every input the browser fires, about 50 in a 1.5-second drag, and redraws for each within a frame. Hazel handles about 13 to 15, because the page is busy with the last one when the next arrives; for Kids' Choice each takes a frame or a few, for Full Body about a second.</p>
<p><b>Noise.</b> The same Full Body drag measured this morning, on the same build, froze for medians of 4.1 and 3.2 s in two sessions, against 2.9 s this evening; the session matters more than any difference under about a second. Dress Up's numbers did not vary between its runs beyond one frame.</p>

<h2 id="change">The cost of one change</h2>
<figure class="fig narrow" id="fig-change">{fig_change}<figcaption><b>Figure 4.</b> The JavaScript one change costs on the page, log scale, against one frame (16.7 ms, dashed). Dress Up's is timed directly ({dress_change:.1f} ms, the median of 15 samples of 40 changes each, in three places). Hazel's are from this morning's profiles of the same build (6 changes of Full Body, 4 of Kids' Choice), and profiled times run long, sometimes by half: Kids' Choice's unprofiled release to redraw is {med(hk, 'release_to_redraw_ms'):.0f} ms.</figcaption></figure>
<p>For a drag to follow the finger at every frame, a change has to fit in a frame, 16.7 ms, with the browser's own drawing. Dress Up's fits about ten times over. Kids' Choice's is about 8 to 13 frames, Full Body's about 60. Where a Full Body change's second goes was profiled on the way to this report, on the same build: the editor's update takes about 860 ms of it, and within the update the livelit views about 450 ms. Over a whole drag, about 40% of the page's time is a check of the whole program for what can be reused: for every preview of a dragged value, the page compares the program with the last one, piece by piece. The evaluation itself runs in the worker, off the page, and the picture waits for it.</p>

<h2 id="closed">How far it has come</h2>
<figure class="fig narrow" id="fig-history">{fig_hist}<figcaption><b>Figure 5.</b> Then and now, log scale. Polygons and Kids' Choice from report 001 (2026-10-09), Full Body's release on #2597 from report 008, each against today. The fixes behind them are in reports 001 to 014; several are Andrew Blinn's, from <a href="https://github.com/hazelgrove/hazel/pull/2469">#2469</a>, the modular editors.</figcaption></figure>
<p>A week ago, a slider release in Kids' Choice took 4.6 seconds; today a drag of it nearly keeps up. The largest steps were analysing only the changed item instead of the whole program (report 008: statics 5.4 s to 38 ms per change), a reuse check by hash in the worker, requests that carry only what changed (report 013), and views that re-evaluate only the calls whose inputs changed (report 001). What is left is not one large mistake, but the cost of a general system doing for a whole program what Dress Up does for one figure, at every change.</p>

<h2 id="bridge">What could close the rest, by September 2027</h2>
<p><b>This section is speculation.</b> Matthew's work on Hazel runs, as far as he knows now, through the next eleven months. Here is what we think that time could buy, step by step, each with what it rests on. The steps' sizes are measured today; that they add up as written is the guess.</p>
<figure class="fig" id="fig-bands">{fig_bands}<figcaption><b>Figure 6.</b> Today's time from a change to its picture (dots, measured: Kids' Choice and Full Body are release to redraw; Dress Up is its cost per change plus one frame), against bands of how it feels, and a guess for September 2027 (dashed). The guess is argued in the list below.</figcaption></figure>
<ol class="ranked">
  <li><b>Weeks: stop checking the whole program for a dragged value's preview.</b> About 40% of a Full Body drag's time on the page is that check (profiled). A preview changes one number in one livelit's model; nothing else needs comparing. With it gone, and only the newest value kept while a change is in flight (built and measured on the way here; only 1.5 to 3 of a drag's 13 changes could be folded, so it matters once changes are cheap), a Full Body drag would freeze roughly half as long.</li>
  <li><b>One to three months: evaluate the views in the worker.</b> A prototype, built on the way here, moved the livelit views off the page: about 540 ms less on the page per change in UX mode and 220 ms with the whole program, with the picture no sooner, and Kids' Choice 45 ms later. Its value is that the page keeps drawing frames while the worker works: the freezes shrink even where the wait does not.</li>
  <li><b>Three to six months: evaluate only what a change touches.</b> Report 010 found that a slider changes 8 of Full Body's 49 shapes, and that 75 to 84% of the evaluation steps run today are in calls whose inputs did not change; named by caller, call site and count (report 011), only 13 to 25% of a picture's evaluation would need to run. Report 012 showed a move of a group need not touch its points. This is incremental computation inside one binding, the research behind Adapton, and the step most likely to take Full Body's evaluation from about a second toward a tenth of one.</li>
  <li><b>Alongside: draw only what changed.</b> The page redraws a livelit's whole picture as a new tree and compares it with the last (report 005). With the worker sending what changed, only the 8 shapes would be redrawn.</li>
  <li><b>Not assumed: a faster evaluator.</b> Hazel's evaluator is an interpreter, compiled to JavaScript with js_of_ocaml. Dress Up's code is JavaScript itself. Closing the last factor of ten for a program of Full Body's size, every frame, would take compiling livelit code or a much faster interpreter: possible, but larger than the steps above, and not in the guess.</li>
</ol>
<p>Together: steps 1 and 2 make the page stop freezing; steps 3 and 4 cut the wait. That is how the guess lands Kids'-sized livelits at 30 to 60 ms per change (immediate, and a drag at 15 to 30 pictures a second) and Full Body at 100 to 300 ms (a short lag, a drag at 3 to 10 pictures a second). Dress Up stays the bar: the kids will keep playing the plain-JavaScript game, and each toy will keep reaching them there first.</p>

<h2 id="next">What next</h2>
<ol>
  <li>Measure the two drag fixes already built (keeping only the newest value, and views in the worker) in an interleaved comparison: both builds served at once, alternating drag by drag, ten or more each, so the session's drift cancels.</li>
  <li>Skip the whole-program reuse check for a drag's preview, and measure a Full Body drag with it.</li>
  <li>Split one Full Body change's second into stages with marks rather than a profiler (the page's update, the request, the worker's evaluation, the reply, the views, the redraw), so this report's guess rests on measured shares.</li>
  <li>Make the same drags on an iPad, in Safari, where M plays: the kids' own device sets the bar.</li>
  <li>Run this report's drags again every month, on #2635's head and the newest Dress Up, and add a dated update with the new figures.</li>
</ol>

<h2 id="method">How this was put together</h2>
<ul>
  <li><b>Builds:</b> Hazel <a href="https://github.com/hazelgrove/hazel/pull/2635">#2635</a> (livelits × modular editors) at <code>032fe3aca6</code>, a dev build; Messed Up Dress Up 0.0.48 (<a href="https://github.com/matthewhammer/kids-choice-games/commit/08abedf7bc"><code>08abedf7bc</code></a>), the game as published.</li>
  <li><b>Browser and machine:</b> headless Firefox 157 over WebDriver (geckodriver), a 1600×1100 window, a fresh profile for each set-up, on Matthew's laptop (Linux, x86-64), one browser at a time, 2026-10-15 between 18:55 and 19:08 Mountain time. Dress Up's music was muted.</li>
  <li><b>The drag:</b> WebDriver pointer actions: move to the slider's thumb, press, 15 moves of 100 ms each to the target, release. Targets are values not drawn before (Full Body: 150 to 425 in steps; the others: a share of the slider's range). Two warm-up drags, then 8 measured, per set-up. A requestAnimationFrame loop in the page records every frame from just before the press; after the release, the page checks every 50 ms whether the largest picture's markup differs from before the drag, which ends the window. Frozen time is the sum of frame gaps over 50 ms in the window.</li>
  <li><b>Dress Up's cost per change:</b> its <code>changed()</code> (draw the friend and the scene, sync the controls, save the state) called for 40 changes of arm length, timed with <code>performance.now()</code>, 5 samples in each of three places (no place, the forest, the witch's woods); JavaScript only, not the browser's drawing, which the drags cover.</li>
  <li><b>Hazel's cost per change:</b> from Gecko profiles of the same build taken the same morning (6 changes of Full Body in each mode, 4 of Kids' Choice), main-thread JavaScript per change. Profiled times run long; the unprofiled release times above are the check.</li>
  <li><b>History:</b> the earlier numbers are from reports 001 and 008, each measured with its own method on its own build; they are compared with today's for scale, not to the millisecond.</li>
  <li><b>The numbers, for programs too:</b> every number behind the figures and tables is also in this page, as JSON in its <code>&lt;script type="application/json" id="report-data"&gt;</code> element: each run's readings, the frame times of the drags in Figure 3, Dress Up's timing samples, and the profiled costs. The same numbers are files in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/015/data"><code>015/data/</code></a>, and the drivers that made them in <a href="https://github.com/matthewhammer/hazel-performance-analysis/tree/main/015/drivers"><code>015/drivers/</code></a> (<code>stall_any.py</code> for any slider in either, <code>drag_stall.py</code> and <code>dressup_stall.py</code> for the arm-length drags; they use <code>deck_regress.py</code> from #2635's <code>scripts/</code>).</li>
</ul>

</main>
<script type="application/json" id="report-data">{json.dumps(data, ensure_ascii=False).replace("</", "<\\/")}</script>
</body>
</html>
"""
open(os.path.join(R, "015", "index.html"), "w").write(page)
print("wrote", len(page), "bytes")
