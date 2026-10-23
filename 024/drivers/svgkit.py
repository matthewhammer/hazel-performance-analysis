"""Small helpers for the report's inline SVG figures.

Every colour is a class whose rule (in the page's <style>) reads one of the
page's CSS variables, so a figure follows the light and dark themes. Text
widths are estimated (about 7 px a character at 12 px, a little more for
monospace) and every box checks that its lines fit; the generator prints
any line that does not."""
import html

WARN = []

SANS = 0.58   # em per character, a conservative average for system-ui
MONO = 0.62


def _cw(c):
    if c.isdigit() or c.isupper() or c in "#_%&@=+<>~^":
        return 0.64
    if c in " ":
        return 0.32
    if c in ".,:;'!|()[]{}-/":
        return 0.38
    if c.islower():
        return 0.57 if c not in "mw" else 0.85
    return 0.8


def tw(s, size=12, mono=False, bold=False):
    if mono:
        w = len(s) * size * MONO
    else:
        w = sum(_cw(c) for c in s) * size
    return w * (1.07 if bold else 1.0)


def esc(s):
    return html.escape(s, quote=False)


class Svg:
    def __init__(self, fid, w, h, label, minw=None):
        self.fid, self.w, self.h, self.label, self.minw = fid, w, h, label, minw
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    # ---- primitives -------------------------------------------------
    def rect(self, x, y, w, h, cls="bx", rx=7):
        self.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx}" class="{cls}"/>')

    def text(self, x, y, s, cls="t", anchor="start", size=None, mono=False, bold=False, maxw=None, where=""):
        c = cls + (" mono" if mono else "") + (" tb" if bold and "tb" not in cls else "")
        st = f' style="font-size:{size}px"' if size else ""
        an = "" if anchor == "start" else f' text-anchor="{anchor}"'
        if maxw is not None and tw(s, size or 12, mono, bold) > maxw:
            WARN.append(f"{self.fid}: text {s!r} ~{tw(s, size or 12, mono, bold):.0f}px > {maxw:.0f}px {where}")
        # keep inside the viewBox
        width = tw(s, size or 12, mono, bold)
        left = x - (width if anchor == "end" else width / 2 if anchor == "middle" else 0)
        if left < -1 or left + width > self.w + 1:
            WARN.append(f"{self.fid}: text {s!r} runs outside the viewBox ({left:.0f}..{left + width:.0f} of {self.w})")
        sp = ' xml:space="preserve" style="white-space:pre' + (f';font-size:{size}px"' if size else '"') if s.startswith(" ") else ""
        if sp:
            st = ""
        self.add(f'<text x="{x:g}" y="{y:g}" class="{c}"{an}{st}{sp}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, cls="ar", marker=None):
        m = f' marker-end="url(#{marker})"' if marker else ""
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" class="{cls}"{m}/>')

    def path(self, d, cls="ar", marker=None, start=None):
        m = f' marker-end="url(#{marker})"' if marker else ""
        m += f' marker-start="url(#{start})"' if start else ""
        self.add(f'<path d="{d}" class="{cls}"{m}/>')

    def poly(self, pts, cls="ar", marker=None):
        d = "M" + " L".join(f"{x:g} {y:g}" for x, y in pts)
        self.path(d, cls, marker)

    # ---- composites -------------------------------------------------
    def box(self, x, y, w, h, lines, cls="bx", size=12, mono=False, title=None, align="middle",
            tcls="t", lh=None, pad=7, title_cls="tb"):
        """A rounded box with an optional bold title line and text lines,
        centred (or left-aligned) and vertically centred."""
        self.rect(x, y, w, h, cls)
        lines = list(lines)
        lh = lh or round(size * 1.33)
        rows = ([("title", title)] if title else []) + [("line", l) for l in lines]
        total = lh * (len(rows) - 1)
        y0 = y + h / 2 - total / 2 + size * 0.36
        for i, (kind, s) in enumerate(rows):
            if s is None or s == "":
                continue
            isT = kind == "title"
            tx = x + w / 2 if align == "middle" else x + pad + 2
            m = mono and not isT
            if isinstance(s, tuple):        # (text, class)
                s, c = s
            else:
                c = title_cls if isT else tcls
            self.text(tx, y0 + i * lh, s, cls=c, anchor="middle" if align == "middle" else "start",
                      size=(size + 1 if isT else size) if size != 12 or isT else None,
                      mono=m, bold=isT, maxw=w - 2 * pad, where=f"in box at {x},{y}")
        need = len(rows) * lh + 6
        if need > h + 2:
            WARN.append(f"{self.fid}: {len(rows)} lines need ~{need}px in a box {h}px high at {x},{y}")

    def autobox(self, x, y, lines, cls="bx", size=12, mono=False, title=None, h=None, pad=9, align="start", minw=0):
        ws = [tw(l if isinstance(l, str) else l[0], size, mono) for l in lines]
        if title:
            ws.append(tw(title, size + 1, False, True))
        w = max([minw] + ws) + 2 * pad
        n = len(lines) + (1 if title else 0)
        h = h or n * round(size * 1.33) + 12
        self.box(x, y, w, h, lines, cls=cls, size=size, mono=mono, title=title, align=align, pad=pad)
        return w, h

    def chip(self, x, y, s, cls="bx", size=12, h=22, pad=9, mono=False, tcls="t"):
        w = tw(s, size, mono) + 2 * pad
        self.rect(x, y, w, h, cls, rx=h / 2 if h < 26 else 8)
        self.text(x + w / 2, y + h / 2 + size * 0.36, s, cls=tcls, anchor="middle",
                  size=size if size != 12 else None, mono=mono)
        return w

    def arrow(self, pts, cls="ar", marker="m-mu", label=None, lpos=None, lanchor="middle", lcls="tm", lsize=11):
        self.poly(pts, cls, marker)
        if label:
            if lpos is None:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                lpos = ((x1 + x2) / 2, (y1 + y2) / 2 - 5)
            self.text(lpos[0], lpos[1], label, cls=lcls, anchor=lanchor, size=lsize)

    def render(self):
        mw = f' style="min-width:{self.minw}px"' if self.minw else ""
        return (f'<svg class="fg" viewBox="0 0 {self.w} {self.h}"{mw} role="img" '
                f'aria-label="{html.escape(self.label)}"><title>{esc(self.label)}</title>\n'
                + "\n".join(self.parts) + "\n</svg>")


MARKERS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>
<marker id="m-mu" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--muted)"/></marker>
<marker id="m-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--accent)"/></marker>
<marker id="m-2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--accent2)"/></marker>
<marker id="m-r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--bad)"/></marker>
<marker id="m-g" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--good)"/></marker>
<marker id="m-w" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" style="fill: var(--warn)"/></marker>
</defs></svg>"""

CSS = """
  svg.fg { width: 100%; height: auto; display: block; font: 12px system-ui, "Segoe UI", Roboto, sans-serif; }
  svg.fg text { fill: var(--ink); }
  svg.fg .t { fill: var(--ink); }
  svg.fg .tm { fill: var(--muted); }
  svg.fg .tb { font-weight: 650; }
  svg.fg .ta { fill: var(--accent); } svg.fg .t2 { fill: var(--accent2); } svg.fg .tg { fill: var(--good); }
  svg.fg .tr { fill: var(--bad); } svg.fg .tw { fill: var(--warn); }
  svg.fg .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  svg.fg .bx { fill: var(--paper); stroke: var(--line); stroke-width: 1.5; }
  svg.fg .bx.k { stroke: var(--muted); }
  svg.fg .bx.a { fill: color-mix(in srgb, var(--accent) 12%, var(--paper)); stroke: var(--accent); }
  svg.fg .bx.b2 { fill: color-mix(in srgb, var(--accent2) 12%, var(--paper)); stroke: var(--accent2); }
  svg.fg .bx.g { fill: color-mix(in srgb, var(--good) 13%, var(--paper)); stroke: var(--good); }
  svg.fg .bx.w { fill: color-mix(in srgb, var(--warn) 14%, var(--paper)); stroke: var(--warn); }
  svg.fg .bx.r { fill: color-mix(in srgb, var(--bad) 11%, var(--paper)); stroke: var(--bad); }
  svg.fg .bx.d { stroke-dasharray: 5 4; stroke: var(--muted); }
  svg.fg .bx.nofill { fill: none; }
  svg.fg .lane { fill: color-mix(in srgb, var(--line) 40%, transparent); stroke: none; }
  svg.fg .lane2 { fill: color-mix(in srgb, var(--accent2) 8%, transparent); stroke: none; }
  svg.fg .ar { stroke: var(--muted); stroke-width: 1.6; fill: none; }
  svg.fg .ar.a { stroke: var(--accent); } svg.fg .ar.r { stroke: var(--bad); } svg.fg .ar.g { stroke: var(--good); }
  svg.fg .ar.w { stroke: var(--warn); } svg.fg .ar.b2 { stroke: var(--accent2); }
  svg.fg .ar.d { stroke-dasharray: 5 4; } svg.fg .ar.thin { stroke-width: 1.1; }
  svg.fg .ar.x { stroke-width: 2.4; }
  svg.fg .life { stroke: var(--muted); stroke-opacity: 0.55; stroke-width: 1.5; stroke-dasharray: 4 4; }
  svg.fg .grid { stroke: var(--line); stroke-width: 1; }
  svg.fg .bar.r { fill: var(--bad); } svg.fg .bar.w { fill: var(--warn); } svg.fg .bar.g { fill: var(--good); }
  svg.fg .bar.a { fill: var(--accent); } svg.fg .bar.b2 { fill: var(--accent2); } svg.fg .bar.k { fill: var(--muted); }
  svg.fg .strike { stroke: var(--bad); stroke-width: 2; }
  svg.fg .dot.a { fill: var(--accent); } svg.fg .dot.b2 { fill: var(--accent2); } svg.fg .dot.g { fill: var(--good); }
  svg.fg .dot.w { fill: var(--warn); } svg.fg .dot.k { fill: var(--muted); } svg.fg .dot.r { fill: var(--bad); }
"""
